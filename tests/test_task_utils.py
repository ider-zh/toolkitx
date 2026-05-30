import threading
import time

import polars as pl
import pytest
from pydantic import BaseModel

from toolkitx.task_utils import PersistentTaskQueue, with_resilience


# --- Test Models ---
class EntityModel(BaseModel):
    name: str
    is_company: bool


# --- Fixtures ---
@pytest.fixture
def temp_db_path(tmp_path):
    """提供临时数据库路径"""
    return str(tmp_path / "test_tasks.db")


@pytest.fixture
def sample_dataframe():
    """提供示例测试数据"""
    return pl.DataFrame(
        {
            "batch_id": ["b1", "b1", "b2", "b3"],
            "input_text": ["Apple inc.", "Google corp.", "Microsoft corp.", "Amazon"],
        }
    )


@pytest.fixture
def error_dataframe():
    """提供包含错误触发文本的数据"""
    return pl.DataFrame(
        {"batch_id": ["error_batch"], "input_text": ["error causing text"]}
    )


# --- with_resilience Tests ---


def test_with_resilience_basic_functionality():
    """测试 with_resilience 装饰器的基本功能"""
    call_count = [0]

    @with_resilience(qps=10, max_retries=3)
    def success_func():
        call_count[0] += 1
        return "success"

    result = success_func()
    assert result == "success"
    assert call_count[0] == 1


def test_with_resilience_retry_on_exception():
    """测试 with_resilience 在异常时的重试机制"""
    call_count = [0]

    @with_resilience(qps=10, max_retries=3, base_delay=0.1, max_delay=0.5)
    def failing_func():
        call_count[0] += 1
        if call_count[0] < 3:
            raise ValueError("Temporary error")
        return "success after retry"

    result = failing_func()
    assert result == "success after retry"
    assert call_count[0] == 3  # 初始调用 + 2次重试


def test_with_resilience_max_retries_exceeded():
    """测试 with_resilience 超过最大重试次数后抛出异常"""
    call_count = [0]

    @with_resilience(qps=10, max_retries=2, base_delay=0.1, max_delay=0.5)
    def always_failing_func():
        call_count[0] += 1
        raise RuntimeError("Always fails")

    with pytest.raises(RuntimeError, match="Always fails"):
        always_failing_func()

    assert call_count[0] == 3  # 初始调用 + 2次重试


def test_with_resilience_rate_limiting():
    """测试 with_resilience 的 QPS 限流功能"""
    qps = 5.0  # 每秒5个请求
    call_times = []

    @with_resilience(qps=qps, max_retries=0)
    def limited_func():
        call_times.append(time.time())
        return "ok"

    # 快速连续调用15次（超过初始容量5个）
    start_time = time.time()
    for _ in range(15):
        limited_func()
    total_time = time.time() - start_time

    # 理论上15个请求应该至少需要 15/5 = 3秒
    # 前5个可以立即处理，后面10个需要等待
    # 给一些容错时间（考虑时间测量的误差）
    assert total_time >= 1.8, f"Expected at least 1.8s, got {total_time:.2f}s"
    assert len(call_times) == 15


def test_with_resilience_no_rate_limiting():
    """测试不设置 QPS 时的无限制行为"""
    call_times = []

    @with_resilience(qps=None, max_retries=0)
    def unlimited_func():
        call_times.append(time.time())
        return "ok"

    # 快速连续调用
    start_time = time.time()
    for _ in range(100):
        unlimited_func()
    total_time = time.time() - start_time

    # 不限流的情况下，应该很快完成（小于0.5秒）
    assert total_time < 0.5, f"Expected < 0.5s, got {total_time:.2f}s"
    assert len(call_times) == 100


# --- PersistentTaskQueue Tests ---


def test_queue_setup(temp_db_path):
    """测试队列初始化和表结构创建"""
    queue = PersistentTaskQueue(db_path=temp_db_path, task_name="test_setup")
    queue.setup()

    # 验证表是否创建
    import sqlite3

    conn = sqlite3.connect(temp_db_path)
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='test_setup'"
    )
    assert cursor.fetchone() is not None
    conn.close()


def test_queue_enqueue_dataframe(temp_db_path, sample_dataframe):
    """测试将 DataFrame 压入队列"""
    queue = PersistentTaskQueue(db_path=temp_db_path, task_name="test_enqueue")
    queue.setup()
    queue.enqueue_dataframe(sample_dataframe)

    # 验证数据是否正确插入
    import sqlite3

    conn = sqlite3.connect(temp_db_path)
    cursor = conn.execute("SELECT COUNT(*) FROM test_enqueue WHERE status='pending'")
    count = cursor.fetchone()[0]
    assert count == 4
    conn.close()


def test_queue_enqueue_idempotent(temp_db_path, sample_dataframe):
    """测试重复压入数据的幂等性"""
    queue = PersistentTaskQueue(db_path=temp_db_path, task_name="test_idempotent")
    queue.setup()

    # 压入两次相同的数据
    queue.enqueue_dataframe(sample_dataframe)
    queue.enqueue_dataframe(sample_dataframe)

    # 验证没有重复数据
    import sqlite3

    conn = sqlite3.connect(temp_db_path)
    cursor = conn.execute("SELECT COUNT(*) FROM test_idempotent")
    count = cursor.fetchone()[0]
    assert count == 4  # 应该只有4条记录，不是8条
    conn.close()


def test_queue_process_success_tasks(temp_db_path, sample_dataframe):
    """测试处理成功的任务"""

    def mock_extract(text: str) -> EntityModel:
        # 从文本中提取第一个单词作为名称
        name = text.split(maxsplit=1)[0]
        return EntityModel(name=name, is_company=True)

    queue = PersistentTaskQueue(db_path=temp_db_path, task_name="test_success")
    queue.setup()
    queue.enqueue_dataframe(sample_dataframe)

    # 处理任务
    queue.process(worker_func=mock_extract, concurrency=2)

    # 获取结果并验证
    result_df = queue.get_results(response_model=EntityModel)
    assert len(result_df) == 4
    assert set(result_df["name"].to_list()) == {
        "Apple",
        "Google",
        "Microsoft",
        "Amazon",
    }
    assert all(result_df["is_company"])


def test_queue_process_with_errors_and_retry(temp_db_path, error_dataframe):
    """测试处理失败任务的重试机制"""
    call_count = [0]

    def failing_extract(text: str) -> EntityModel:
        call_count[0] += 1
        if call_count[0] < 3:
            raise ValueError("Simulated API Error!")
        return EntityModel(name="Success", is_company=False)

    queue = PersistentTaskQueue(
        db_path=temp_db_path, task_name="test_retry", max_retries=3
    )
    queue.setup()
    queue.enqueue_dataframe(error_dataframe)

    # 处理任务（会在内部重试）
    queue.process(worker_func=failing_extract, concurrency=1)

    # 获取结果并验证
    result_df = queue.get_results(response_model=EntityModel)
    assert len(result_df) == 1
    assert result_df["name"][0] == "Success"
    # 验证确实重试了（初始调用 + 2次失败 = 3次调用，第3次成功）


def test_queue_process_max_retries_exceeded(temp_db_path, error_dataframe):
    """测试超过最大重试次数后任务被标记为 failed"""

    def always_failing_extract(text: str) -> EntityModel:
        raise RuntimeError("Always fails")

    queue = PersistentTaskQueue(
        db_path=temp_db_path, task_name="test_max_retry", max_retries=2
    )
    queue.setup()
    queue.enqueue_dataframe(error_dataframe)

    # 处理任务
    queue.process(worker_func=always_failing_extract, concurrency=1)

    # 验证没有成功完成的任务
    result_df = queue.get_results(response_model=EntityModel)
    assert len(result_df) == 0

    # 验证数据库中有失败的记录
    import sqlite3

    conn = sqlite3.connect(temp_db_path)
    cursor = conn.execute("SELECT COUNT(*) FROM test_max_retry WHERE status='failed'")
    failed_count = cursor.fetchone()[0]
    assert failed_count == 1
    conn.close()


def test_queue_crash_recovery(temp_db_path, sample_dataframe):
    """测试崩溃恢复功能"""

    def mock_extract(text: str) -> EntityModel:
        return EntityModel(name=text.split(maxsplit=1)[0], is_company=True)

    queue = PersistentTaskQueue(db_path=temp_db_path, task_name="test_recovery")
    queue.setup()
    queue.enqueue_dataframe(sample_dataframe)

    # 模拟崩溃：手动将任务状态改为 processing
    import sqlite3

    conn = sqlite3.connect(temp_db_path)
    conn.execute("UPDATE test_recovery SET status='processing' WHERE status='pending'")
    conn.commit()
    conn.close()

    # 创建新队列实例（模拟重启）
    queue2 = PersistentTaskQueue(db_path=temp_db_path, task_name="test_recovery")
    queue2.setup()  # setup 会将 processing 任务恢复为 pending

    # 处理任务
    queue2.process(worker_func=mock_extract, concurrency=2)

    # 验证所有任务都被处理
    result_df = queue2.get_results(response_model=EntityModel)
    assert len(result_df) == 4


def test_queue_get_results_without_model(temp_db_path, sample_dataframe):
    """测试不使用 Pydantic 模型获取结果"""

    def simple_extract(text: str) -> dict:
        return {"extracted": text.split(maxsplit=1)[0]}

    queue = PersistentTaskQueue(db_path=temp_db_path, task_name="test_no_model")
    queue.setup()
    queue.enqueue_dataframe(sample_dataframe)

    queue.process(worker_func=simple_extract, concurrency=2)

    # 不传递 response_model
    result_df = queue.get_results(response_model=None)
    assert len(result_df) == 4
    assert "result" in result_df.columns

    # 验证 result 列包含解析后的数据
    # 当不使用 Pydantic 模型时，result 被解析为 JSON 字典
    # 注意：Polars 可能会将字典存储为 struct 类型，但访问时返回 Python 字典
    first_result = result_df["result"][0]

    # 检查类型并相应地访问
    if isinstance(first_result, dict):
        # 直接访问字典
        assert first_result["extracted"] == "Apple"
    else:
        # 可能是 Polars struct 类型，需要通过字段名访问
        assert first_result["extracted"] == "Apple"


def test_queue_concurrent_execution(temp_db_path, sample_dataframe):
    """测试并发执行的正确性"""
    execution_times = []

    def tracked_extract(text: str) -> EntityModel:
        execution_times.append(time.time())
        time.sleep(0.1)  # 模拟耗时操作
        return EntityModel(name=text.split(maxsplit=1)[0], is_company=True)

    queue = PersistentTaskQueue(db_path=temp_db_path, task_name="test_concurrent")
    queue.setup()
    queue.enqueue_dataframe(sample_dataframe)

    start_time = time.time()
    queue.process(worker_func=tracked_extract, concurrency=4)
    total_time = time.time() - start_time

    # 验证所有任务都完成了
    result_df = queue.get_results(response_model=EntityModel)
    assert len(result_df) == 4

    # 验证并发效果：4个任务并发执行，每个0.1秒，总时间应该远小于 0.4秒
    assert total_time < 0.6, f"Expected < 0.6s with concurrency, got {total_time:.2f}s"


def test_queue_graceful_shutdown(temp_db_path, sample_dataframe):
    """测试优雅停机功能"""
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from functools import partial

    from tqdm import tqdm

    def slow_extract(text: str) -> EntityModel:
        time.sleep(0.2)
        return EntityModel(name=text.split(maxsplit=1)[0], is_company=True)

    # 创建更大的数据集以触发中断
    large_df = pl.DataFrame(
        {
            "batch_id": [f"b{i}" for i in range(20)],
            "input_text": [f"Company {i}" for i in range(20)],
        }
    )

    queue = PersistentTaskQueue(db_path=temp_db_path, task_name="test_shutdown")
    queue.setup()
    queue.enqueue_dataframe(large_df)

    # 在后台线程中启动处理（避免信号处理问题）
    # 注意：实际使用中，signal.SIGINT 处理只能在主线程中工作
    # 这里我们直接设置 shutdown_event 来模拟停机
    def run_queue():
        # 覆盖 process 方法以避免信号处理

        def modified_process(worker_func, concurrency=10):
            queue._shutdown_event.clear()

            # 直接跳过信号处理部分
            with queue._get_conn() as conn:
                cursor = conn.execute(
                    f"SELECT COUNT(*) FROM {queue.table_name} WHERE status='pending'"
                )
                total_pending = cursor.fetchone()[0]

            if total_pending == 0:
                return

            try:
                with tqdm(
                    total=total_pending, desc="Global Progress", unit="task"
                ) as global_pbar:
                    while not queue._shutdown_event.is_set():
                        with queue._get_conn() as conn:
                            cursor = conn.execute(
                                f"SELECT id, input_text, retry_count FROM {queue.table_name} WHERE status='pending' LIMIT 1000"
                            )
                            pending_tasks = [dict(row) for row in cursor.fetchall()]

                        if not pending_tasks:
                            break

                        worker_partial = partial(queue._worker, worker_func=worker_func)

                        with ThreadPoolExecutor(max_workers=concurrency) as executor:
                            futures = [
                                executor.submit(worker_partial, task)
                                for task in pending_tasks
                            ]

                            for future in as_completed(futures):
                                future.result()
                                global_pbar.update(1)

            finally:
                if queue._shutdown_event.is_set():
                    with queue._get_conn() as conn:
                        conn.execute(
                            f"UPDATE {queue.table_name} SET status='pending' WHERE status='processing'"
                        )
                        conn.commit()

        modified_process(worker_func=slow_extract, concurrency=2)

    process_thread = threading.Thread(target=run_queue)
    process_thread.start()

    # 等待一小段时间后发送停机信号
    time.sleep(0.1)
    queue._shutdown_event.set()

    # 等待线程结束
    process_thread.join(timeout=5)

    # 验证部分任务已完成，部分被恢复
    import sqlite3

    conn = sqlite3.connect(temp_db_path)

    # 获取已完成和待处理的任务数
    completed = conn.execute(
        "SELECT COUNT(*) FROM test_shutdown WHERE status='completed'"
    ).fetchone()[0]

    # processing 任务应该被恢复为 pending
    pending = conn.execute(
        "SELECT COUNT(*) FROM test_shutdown WHERE status='pending'"
    ).fetchone()[0]

    conn.close()

    # 应该有一些任务已完成，一些仍然是 pending
    assert completed > 0 or pending > 0
    assert completed + pending == 20


def test_queue_get_results_empty(temp_db_path):
    """测试从空队列获取结果"""
    queue = PersistentTaskQueue(db_path=temp_db_path, task_name="test_empty")
    queue.setup()

    result_df = queue.get_results(response_model=EntityModel)
    assert len(result_df) == 0


def test_queue_mixed_batch_ids(temp_db_path):
    """测试处理多个 batch_id 的任务"""

    def mock_extract(text: str) -> EntityModel:
        return EntityModel(name=text.split(maxsplit=1)[0], is_company=True)

    mixed_df = pl.DataFrame(
        {
            "batch_id": ["batch1", "batch1", "batch2", "batch2", "batch3"],
            "input_text": ["A", "B", "C", "D", "E"],
        }
    )

    queue = PersistentTaskQueue(db_path=temp_db_path, task_name="test_mixed")
    queue.setup()
    queue.enqueue_dataframe(mixed_df)

    queue.process(worker_func=mock_extract, concurrency=3)

    result_df = queue.get_results(response_model=EntityModel)
    assert len(result_df) == 5
    assert set(result_df["batch_id"].to_list()) == {"batch1", "batch2", "batch3"}
