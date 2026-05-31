import json
import logging
import pathlib
import random
import signal
import sqlite3
import threading
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial, wraps

import polars as pl
from pydantic import BaseModel
from tqdm import tqdm

logger = logging.getLogger(__name__)

class TokenBucket:
    """
    线程安全的令牌桶限流器

    Examples:
        >>> bucket = TokenBucket(capacity=10, fill_rate=1)
        >>> bucket.consume(1.0)
        True
    """
    def __init__(self, capacity: float, fill_rate: float):
        self.capacity = float(capacity)
        self._tokens = float(capacity)
        self.fill_rate = float(fill_rate) # 每秒补充的令牌数 (即 QPS)
        self.last_update = time.monotonic()
        self.lock = threading.Lock()

    def consume(self, tokens: float = 1.0):
        while True:
            with self.lock:
                now = time.monotonic()
                # 计算自上次更新以来的时间，补充令牌
                self._tokens += (now - self.last_update) * self.fill_rate
                self.last_update = now
                
                # 令牌数不能超过桶的容量
                self._tokens = min(self._tokens, self.capacity)

                # 如果令牌足够，扣除并放行
                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return True
            
            # 令牌不足，短暂休眠后再次检查，防止 CPU 空转
            time.sleep(0.05)

def with_resilience(
    qps: float | None = None, 
    max_retries: int = 5, 
    base_delay: float = 1.0, 
    max_delay: float = 60.0
) -> Callable:
    """
    通用 API 韧性装饰器

    Args:
        qps: 每秒最大请求数 (None 表示不限流，依赖默认并发控制)
        max_retries: 遇到网络或 API 错误时的最大退避重试次数
        base_delay: 退避基础延迟 (秒)
        max_delay: 退避最大延迟 (秒)

    Returns:
        一个装饰器函数，用于为目标函数增加限流和重试能力。

    Examples:
        >>> @with_resilience(qps=100, max_retries=3)
        ... def fast_func(x):
        ...     return x + 1
        >>> fast_func(1)
        2
    """
    # 装饰器初始化时创建共享的令牌桶实例
    bucket = TokenBucket(capacity=qps, fill_rate=qps) if qps else None

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            while True:
                # 1. 令牌桶限流 (主动卡位)
                if bucket:
                    bucket.consume(1.0) 

                try:
                    # 2. 执行核心操作
                    return func(*args, **kwargs)
                
                except Exception as e:
                    # 3. 拦截异常，执行指数退避重试 (被动防御)
                    attempt += 1
                    if attempt > max_retries:
                        logger.error(f"❌ Worker 内部重试耗尽 ({max_retries}次). 最终报错: {e}")
                        # 抛出异常，交由外层 PersistentTaskQueue 记为 failed
                        raise 

                    # 计算退避时间: base_delay * 2^(attempt-1)
                    delay = min(max_delay, base_delay * (2 ** (attempt - 1)))
                    # 加入 ±10% 的随机抖动 (Jitter)，防止多个线程同时苏醒再次引发雪崩
                    jitter = random.uniform(-0.1 * delay, 0.1 * delay)
                    total_delay = delay + jitter
                    
                    logger.warning(f"⚠️ API 异常 ({type(e).__name__}): {e}. 正在退避，等待 {total_delay:.1f} 秒后进行第 {attempt} 次重试...")
                    time.sleep(total_delay)
        return wrapper
    return decorator

class PersistentTaskQueue:
    """
    持久化任务队列，使用 SQLite 存储任务状态，支持并发处理和优雅停机。

    Examples:
        >>> import polars as pl
        >>> import tempfile
        >>> from pathlib import Path
        >>> with tempfile.TemporaryDirectory() as tmpdir:
        ...     db_path = Path(tmpdir) / "tasks.db"
        ...     queue = PersistentTaskQueue(db_path, task_name="test_task")
        ...     queue.setup()
        ...     # 1. 压入任务
        ...     df = pl.DataFrame({
        ...         "batch_id": ["B1", "B1"],
        ...         "input_text": ["text1", "text2"]
        ...     })
        ...     queue.enqueue_dataframe(df)
        ...     # 2. 处理任务
        ...     def my_processor(text: str) -> str:
        ...         return text.upper()
        ...     queue.process(worker_func=my_processor, concurrency=2)
        ...     # 3. 获取结果
        ...     results = queue.get_results().sort("input_text")
        ...     print(results["result"].to_list())
        ['TEXT1', 'TEXT2']
    """
    def __init__(self, db_path: str|pathlib.Path, task_name: str, max_retries: int = 3):
        """
        初始化持久化任务队列
        
        Args:
            db_path: 数据库文件路径，用于持久化存储任务状态
            task_name: 任务名称，将作为数据库表名使用
            max_retries: 失败任务的最大重试次数，默认为3次
        
        Attributes:
            db_path: 数据库文件路径
            table_name: 任务表名
            max_retries: 最大重试次数
            db_lock: 数据库操作锁，确保线程安全
            _shutdown_event: 优雅停机事件对象
        """
        self.db_path = db_path
        self.table_name = task_name
        self.max_retries = max_retries
        self.db_lock = threading.Lock()
        
        # 🟢 优雅停机信号
        self._shutdown_event = threading.Event()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def setup(self):
        """
        初始化数据库表结构、创建索引，并执行崩溃恢复
        
        此方法会：
        1. 创建任务表（如果不存在），包含字段：id, batch_id, input_text, status, result, error_msg, retry_count
        2. 为 pending 状态的任务创建部分索引，提高查询性能
        3. 将所有 processing 状态的任务重置为 pending（处理崩溃恢复）
        4. 将未达到最大重试次数的 failed 任务重置为 pending（处理失败恢复）
        
        注意：此方法应在首次使用队列时调用一次，之后每次启动时也建议调用以进行恢复
        """
        with self._get_conn() as conn:
            create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_id TEXT,
                input_text TEXT,
                status TEXT DEFAULT 'pending',
                result TEXT,
                error_msg TEXT,
                retry_count INTEGER DEFAULT 0,
                UNIQUE(batch_id, input_text)
            );
            """
            conn.execute(create_table_sql)
            
            # 部分索引：极速捞取 pending 任务
            conn.execute(f"CREATE INDEX IF NOT EXISTS idx_pending ON {self.table_name}(id) WHERE status='pending';")
            
            # 崩溃恢复
            cursor_processing = conn.execute(f"UPDATE {self.table_name} SET status='pending' WHERE status='processing'")
            
            # ⚡️ 失败恢复：将未达到最大重试次数的 failed 任务重置为 pending ⚡️
            cursor_failed = conn.execute(
                f"UPDATE {self.table_name} SET status='pending' WHERE status='failed' AND retry_count < ?",
                (self.max_retries,)
            )
            
            conn.commit()
            if cursor_processing.rowcount > 0:
                logging.info(f"🔄 启动恢复: 成功重置 {cursor_processing.rowcount} 个意外卡死的 processing 任务为 pending.")
            if cursor_failed.rowcount > 0:
                logging.info(f"🔄 失败恢复: 成功重置 {cursor_failed.rowcount} 个未达重试上限的 failed 任务为 pending.")

    def enqueue_dataframe(self, df: pl.DataFrame):
        """
        将 Polars DataFrame 压入队列（幂等操作）
        
        Args:
            df: Polars DataFrame，必须包含 'batch_id' 和 'input_text' 两列
        
        说明：
        - 使用 INSERT OR IGNORE 语句，重复的 (batch_id, input_text) 组合会被自动过滤
        - 所有新任务初始状态为 'pending'
        - 此方法是幂等的，可以安全地多次调用相同数据
        """
        data = df.select(["batch_id", "input_text"]).to_dicts()
        insert_sql = f"INSERT OR IGNORE INTO {self.table_name} (batch_id, input_text) VALUES (:batch_id, :input_text)"
        with self._get_conn() as conn:
            conn.executemany(insert_sql, data)
            conn.commit()
        logging.info("📥 数据压入完成 (已自动过滤重复项)。")

    def _worker(self, task_record: dict, worker_func: Callable):
        """
        通用 Worker：执行任务处理函数
        
        Args:
            task_record: 任务记录字典，包含 id, input_text, retry_count 等字段
            worker_func: 任务处理函数，接收 input_text 参数，返回处理结果
        
        处理流程：
        1. 检查是否收到停机信号，如果是则放弃执行
        2. 将任务状态更新为 'processing'
        3. 调用 worker_func 处理任务
        4. 根据处理结果更新任务状态：
           - 成功：状态设为 'completed'，保存结果
           - 失败：根据重试次数决定状态为 'pending' 或 'failed'
        
        说明：
        - 如果 worker_func 返回 Pydantic BaseModel，会自动序列化为 JSON
        - 如果返回其他类型（dict, list, str 等），也会自动序列化为 JSON
        - 异常会被捕获并记录到 error_msg 字段
        """
        task_id = task_record["id"]
        
        # 🟢 如果接收到了停机信号，放弃执行，将任务退回队列
        if self._shutdown_event.is_set():
            return

        with self.db_lock, self._get_conn() as conn:
            conn.execute(f"UPDATE {self.table_name} SET status='processing' WHERE id=?", (task_id,))
            conn.commit()

        try:
            # 执行通用任务 (LLM、爬虫、计算等)
            result_obj = worker_func(task_record["input_text"])
            
            # 智能序列化：支持 Pydantic, Dict, List, String 等
            if isinstance(result_obj, BaseModel):
                result_json = result_obj.model_dump_json()
            else:
                result_json = json.dumps(result_obj, ensure_ascii=False)

            with self.db_lock, self._get_conn() as conn:
                conn.execute(
                    f"UPDATE {self.table_name} SET status='completed', result=?, error_msg=NULL WHERE id=?",
                    (result_json, task_id)
                )
                conn.commit()
            
        except Exception as e:
            retry_count = task_record["retry_count"] + 1
            status = 'failed' if retry_count >= self.max_retries else 'pending'
            
            with self.db_lock, self._get_conn() as conn:
                conn.execute(
                    f"UPDATE {self.table_name} SET status=?, retry_count=?, error_msg=? WHERE id=?",
                    (status, retry_count, str(e), task_id)
                )
                conn.commit()
                
    def process(self, worker_func: Callable, concurrency: int = 10):
        """
        并发调度引擎，处理所有待处理的任务
        
        Args:
            worker_func: 任务处理函数，接收 input_text 参数，返回处理结果
            concurrency: 并发线程数，默认为10
        
        功能特性：
        - 支持优雅停机：按下 Ctrl+C 会等待当前正在执行的任务完成
        - 实时进度条：显示任务处理进度
        - 自动分批：每次从数据库读取最多1000个任务进行处理
        - 崩溃恢复：启动时自动重置 processing 状态的任务
        - 失败重试：支持自动重试失败的任务
        
        注意：
        - 此方法会阻塞直到所有任务完成或收到停机信号
        - 收到停机信号后，会将正在处理的任务状态重置为 pending
        - 下次启动时会自动继续处理未完成的任务
        """
        self._shutdown_event.clear()
        
        # 🟢 注册信号监听器
        original_sigint = signal.getsignal(signal.SIGINT)
        def handle_sigint(signum, frame):
            logging.warning("\n🛑 接收到中止信号 (Ctrl+C)！正在等待当前活跃线程保存进度，请勿强制关闭...")
            self._shutdown_event.set()
        signal.signal(signal.SIGINT, handle_sigint)

        # 1. 查询全局 pending 数量
        with self._get_conn() as conn:
            cursor = conn.execute(f"SELECT COUNT(*) FROM {self.table_name} WHERE status='pending'")
            total_pending = cursor.fetchone()[0]

        if total_pending == 0:
            logging.info("🎉 队列为空，所有任务处理完毕！")
            return

        try:
            # 2. 创建全局进度条
            with tqdm(total=total_pending, desc="Global Progress", unit="task") as global_pbar:
                
                while not self._shutdown_event.is_set():
                    with self._get_conn() as conn:
                        cursor = conn.execute(
                            f"SELECT id, input_text, retry_count FROM {self.table_name} WHERE status='pending' LIMIT 1000"
                        )
                        pending_tasks = [dict(row) for row in cursor.fetchall()]

                    if not pending_tasks:
                        break
                        
                    # 包装 worker_func
                    worker_partial = partial(self._worker, worker_func=worker_func)
                    
                    # 我们直接使用并发工具执行，但不用它画图
                    with ThreadPoolExecutor(max_workers=concurrency) as executor:
                        # 提交任务
                        futures = [executor.submit(worker_partial, task) for task in pending_tasks]
                        
                        # 每完成一个任务，全局进度条 +1
                        for future in as_completed(futures):
                            future.result() # 触发潜在的异常
                            global_pbar.update(1)

        finally:
            # 恢复默认的 Ctrl+C 行为
            signal.signal(signal.SIGINT, original_sigint)
            
            # 优雅停机清理
            if self._shutdown_event.is_set():
                with self._get_conn() as conn:
                    conn.execute(f"UPDATE {self.table_name} SET status='pending' WHERE status='processing'")
                    conn.commit()
                logging.info("✅ 优雅停机完成，进度已安全落盘。下次启动将自动接续执行。")


    def get_results(self, response_model: type[BaseModel] | None = None) -> pl.DataFrame:
        """
        获取所有已完成任务的结果
        
        Args:
            response_model: 可选的 Pydantic 模型类型，用于将结果反序列化为强类型对象
                           如果为 None，结果将被解析为普通字典
        
        Returns:
            Polars DataFrame，包含所有已完成任务的结果
            - 如果提供 response_model：包含 batch_id, input_text 以及模型定义的所有字段
            - 如果不提供 response_model：包含 batch_id, input_text, result（解析后的字典）
        
        说明：
        - 只返回状态为 'completed' 的任务
        - 结果按完成顺序排列
        - response_model 必须与 worker_func 返回的数据结构匹配
        """
        with self._get_conn() as conn:
            cursor = conn.execute(f"SELECT batch_id, input_text, result FROM {self.table_name} WHERE status='completed'")
            rows = cursor.fetchall()
            
        data_list = []
        for row in rows:
            base_dict = {"batch_id": row["batch_id"], "input_text": row["input_text"]}
            
            # 灵活解析：如果有 Pydantic Model 就强类型展开，否则只解析 JSON
            if response_model:
                parsed_result = response_model.model_validate_json(row["result"])
                base_dict.update(parsed_result.model_dump())
            else:
                base_dict["result"] = json.loads(row["result"])
                
            data_list.append(base_dict)
            
        return pl.DataFrame(data_list)
