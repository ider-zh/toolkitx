import os
from abc import ABC, abstractmethod
from typing import Optional, Literal
from diskcache import Cache
import hashlib
import logging
import httpx
import time

from tencentcloud.common.credential import Credential
from tencentcloud.tmt.v20180321.tmt_client import TmtClient
from tencentcloud.tmt.v20180321.models import TextTranslateRequest
from tencentcloud.tmt.v20180321.models import TextTranslateResponse

logger = logging.getLogger(__name__)

# 定义支持的翻译引擎类型
SUPPORTED_ENGINES = Literal["baidu", "tencent"]

CHARSET = 'UTF-8'
CRLF = "\n"

BAIDU_API_URL = "https://fanyi-api.baidu.com/api/trans/vip/translate"

class TranslatorInterface(ABC):
    """
    Abstract base class for a translator.
    Defines the common interface for translation services.
    """
    
    def __init__(
        self,
        api_id: Optional[str] = None,
        api_key: Optional[str] = None,
        text_chunk_size: int = 500,
    ):
        self.api_id = api_id
        self.api_key = api_key
        self.text_chunk_size = text_chunk_size
        
    
    def translate(self, text: str, target_lang: str, source_lang: str = 'auto') -> str:
        """
        Translate text from a source language to a target language.

        :param text: The text to translate.
        :param target_lang: The target language code (e.g., 'en', 'zh').
        :param source_lang: The source language code (e.g., 'auto', 'en', 'zh').
        :return: The translated text.
        """
        segments = self._chunk_text_by_max_length(text)
        if len(segments) > 1:
            logger.debug(f"Split into [{len(segments)}] translated segments...")
            
        translated_text_list = []
        for i, content in enumerate(segments):
            translated_text = self._translate(content, target_lang, source_lang, )
            translated_text_list.append(translated_text)
            
        return CRLF.join(translated_text_list)
    
    @abstractmethod
    def _translate(self, text: str, target_lang: str,source_lang: str = 'auto',) -> str:
        pass
    
    def _chunk_text_by_max_length(self, text:str) -> list[str]:
        if self.text_chunk_size <= 0:
            return [text]
        
        segments = []
        segment_simple = []
        segment_simple_size = 0
        
        for line in text.split(CRLF):
            line = line.strip()
            if not line:
                continue
            
            line_size = len(line)
            if line_size > self.text_chunk_size:
                logger.warning("one line length gather then text_chunk_size:",line[:10], self.text_chunk_size)
                # todo
                
            if line_size + segment_simple_size + len(segment_simple) - 1 > self.text_chunk_size:
                segments.append(CRLF.join(segment_simple))
                segment_simple = []
                segment_simple_size = 0
                
            segment_simple.append(line)
            segment_simple_size += line_size
        if segment_simple:
            segments.append(CRLF.join(segment_simple))
        return segments
            
class BaiduTranslation(TranslatorInterface) :
    
    def __init__(self, api_id, api_key, api_url=BAIDU_API_URL, text_chunk_size=2000) -> None :
        TranslatorInterface.__init__(self, api_id, api_key, text_chunk_size)
        self.api_url = api_url
        
    def _translate(self, text, target_lang='en', source_lang='auto'): 
        """
        翻译文本段落
        :param text   : 待翻译文本段落
        :param from_lang : 待翻译文本的源语言 (例如: 'en', 'zh')
        :param to_lang   : 需要翻译的目标语言 (例如: 'en', 'zh')
        :return: 已翻译的文本段落 (str)
        """

        salt, sign = self._to_sign(text)
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        # 请求体参数
        payload = { # PEP8 推荐使用 payload 作为 POST 请求数据的变量名
            'q': text,
            'from': source_lang,
            'to': target_lang,
            'appid': self.api_id,
            'salt': salt,
            'sign': sign
        }

        trans_result = []
        try:
            # 使用 httpx.post 发送同步POST请求
            # httpx 默认超时时间是5秒，可以根据需要调整 timeout 参数
            # 例如: httpx.post(self.api_url, headers=headers, data=payload, timeout=10.0)
            response = httpx.post(self.api_url, headers=headers, data=payload)
            response.raise_for_status() # 如果状态码是 4xx 或 5xx，则抛出 HTTPStatusError 异常

            # 检查响应状态码 (虽然 raise_for_status 会处理错误，但明确检查也可以)
            if response.status_code == 200:
                rst = response.json() # httpx 直接提供 .json() 方法解析 JSON
                if "trans_result" in rst and rst["trans_result"]:
                    for line in rst.get("trans_result"):
                        trans_result.append(line.get("dst", "").strip()) # 添加默认值以防 "dst" 不存在
                elif "error_code" in rst:
                    logger.error(f"翻译段落失败: 接口返回错误码 {rst['error_code']} - {rst.get('error_msg', '无错误信息')}")
                else:
                    logger.error(f"翻译段落失败: 响应JSON中缺少 'trans_result' 或其为空。响应: {response.text}")
            # else: # raise_for_status 已经处理了非200的情况，这部分可以省略
            #     logger.error(f"翻译段落失败: 接口 [{response.status_code}] 异常. 响应: {response.text}")

        except httpx.HTTPStatusError as e: # 处理 HTTP 状态错误
            logger.error(f"翻译段落失败: HTTP 状态错误 {e.response.status_code}. 响应: {e.response.text}")
        except httpx.RequestError as e: # 处理请求相关的其他错误 (例如网络问题)
            logger.error(f"翻译段落失败: 请求错误 {type(e).__name__} - {e}")
        except json.JSONDecodeError: # 处理 JSON 解析错误
            logger.error(f"翻译段落失败: 无法解析响应JSON. 响应: {response.text}")
        except Exception as e: # 捕获其他潜在错误
            logger.error(f"翻译段落时发生未知错误: {type(e).__name__} - {e}. 响应文本 (如果可用): {getattr(response, 'text', 'N/A')}")
            
        return CRLF.join(trans_result)

    def _to_sign(self, data: str) -> tuple[int, str]:
        """
        生成百度翻译API所需的签名
        :param data: 待翻译的原始文本
        :return: 一个包含 salt (int) 和 sign (str) 的元组
        """
        salt = int(time.time())
        # 构建签名字符串：appid + q + salt + 密钥
        sign_str = f"{self.api_id}{data}{salt}{self.api_key}"
        
        # 计算 MD5 哈希值
        sign = hashlib.md5(sign_str.encode(CHARSET)).hexdigest()
        return salt, sign



GZ_REGION = 'ap-guangzhou'
ARG_UNTRANSLATED_TEXT = 'UntranslatedText'

class TencentTranslation(TranslatorInterface) :

    def __init__(self, api_id, api_key, region=GZ_REGION, text_chunk_size=2000) :
        TranslatorInterface.__init__(self, api_id, api_key, text_chunk_size)
        cred = Credential(api_id, api_key)
        self.client = TmtClient(cred, region)

    
    def _translate(self, text, target_lang='en', source_lang='auto') :
        """
        翻译文本段落
        :param content      : 待翻译文本段落
        :param from_lang    : 待翻译文本的源语言（不同的平台语言代码不一样）
        :param to_lang      : 需要翻译的目标语言（不同的平台语言代码不一样）
                                UntranslatedText: 忽略的翻译文本
        :return: 已翻译的文本段落
        """
        
        req = TextTranslateRequest()
        req.SourceText = text
        req.Source = source_lang
        req.Target = target_lang
        req.ProjectId = 0
        rsp = self.client.TextTranslate(req)
        return rsp.TargetText
    
class Translator():
    """
    A translator implementation using py-transgpt with disk-based caching.
    Supports Baidu and Tencent translation engines.
    """

    def __init__(
        self,
        engine: SUPPORTED_ENGINES,
        cache_path: str,
        api_id: Optional[str] = None,
        api_key: Optional[str] = None,
        target_lang: str = 'en', # Default target language
        source_lang: str = 'auto' # Default source language
    ):
        """
        Initialize the Translator.

        :param engine: The translation engine to use ('baidu' or 'tencent').
        :param cache_path: Path to the directory for storing the translation cache.
        :param api_id: API ID for the translation service. If None, attempts to load from ENV.
                       For Tencent, this is SecretId.
        :param api_key: API Key for the translation service. If None, attempts to load from ENV.
                        For Tencent, this is SecretKey.
        :param target_lang: Default target language for translations.
        :param source_lang: Default source language for translations.
        :raises ValueError: If the engine is not supported or API credentials are not found.
        """
        if engine not in ["baidu", "tencent"]:
            raise ValueError(f"Unsupported engine: {engine}. Supported engines are 'baidu', 'tencent'.")

        self.engine_name = engine
        self.cache = Cache(cache_path)
        self.default_target_lang = target_lang
        self.default_source_lang = source_lang

        # Load API credentials
        env_api_id_name = ""
        env_api_key_name = ""

        if self.engine_name == "baidu":
            env_api_id_name = "BAIDU_API_ID"
            env_api_key_name = "BAIDU_API_KEY"
            _api_id = api_id or os.getenv(env_api_id_name)
            _api_key = api_key or os.getenv(env_api_key_name)
            if not _api_id or not _api_key:
                raise ValueError(
                    f"Baidu API ID and API Key are required. "
                    f"Provide them as arguments or set {env_api_id_name} and {env_api_key_name} environment variables."
                )
            self.translator_instance = BaiduTranslation(api_id=_api_id, api_key=_api_key)

        elif self.engine_name == "tencent":
            env_api_id_name = "TENCENT_API_ID"
            env_api_key_name = "TENCENT_API_KEY"
            _api_id = api_id or os.getenv(env_api_id_name)
            _api_key = api_key or os.getenv(env_api_key_name)
            if not _api_id or not _api_key:
                raise ValueError(
                    f"Tencent Secret ID and Secret Key are required. "
                    f"Provide them as arguments or set {env_api_id_name} and {env_api_key_name} environment variables."
                )
            self.translator_instance = TencentTranslation(api_id=_api_id, api_key=_api_key)
        
    def _create_cache_key(self, text: str, target_lang: str, source_lang: str) -> str:
        """Helper to create a unique cache key."""
        return f"{self.engine_name}:{source_lang}:{target_lang}:{hashlib.md5(text.encode("utf8")).hexdigest()}"

    def translate(self, text: str, target_lang: Optional[str] = None, source_lang: Optional[str] = None) -> str:
        """
        Translate text using the configured engine and cache.

        :param text: The text to translate.
        :param target_lang: The target language code. Defaults to instance's default_target_lang.
        :param source_lang: The source language code. Defaults to instance's default_source_lang.
        :return: The translated text.
        """
        _target_lang = target_lang or self.default_target_lang
        _source_lang = source_lang or self.default_source_lang

        if not text:
            return ""

        cache_key = self._create_cache_key(text, _target_lang, _source_lang)
        cached_translation = self.cache.get(cache_key)

        if cached_translation is not None:
            return cached_translation
        # print(f"Cache miss. Translating: {text[:30]}...") # For debugging
        try:
            # py-transgpt's translate method takes (text, target_language, source_language)
            translated_text = self.translator_instance.translate(text, _target_lang, _source_lang)
            if translated_text: # Ensure we don't cache None or empty if translation fails silently
                self.cache.set(cache_key, translated_text)
            return translated_text
        except Exception as e:
            # Log error or handle as needed
            logger.warning(f"Error during translation with {self.engine_name}: {e}")
            # Depending on requirements, you might want to re-raise or return original text/error message
            raise  # Re-raise the exception to make the caller aware

    def clear_cache(self) -> None:
        """
        Clear all items from the translation cache for this translator instance.
        """
        self.cache.clear()

    def close_cache(self) -> None:
        """
        Close the cache. Important to call when done if cache is not used as a context manager.
        """
        self.cache.close()

# Example Usage (you can put this in a separate test file or a __main__ block)
if __name__ == "__main__":
    # Ensure you have set your environment variables for BAIDU_API_ID, BAIDU_API_KEY
    # or TENCENT_SECRET_ID, TENCENT_SECRET_KEY, or pass them directly.

    # Example for Baidu (assuming ENV VARS are set)
    try:
        print("Testing Baidu Translator...")
        # Create a directory for cache if it doesn't exist
        baidu_cache_dir = "/tmp/translator_cache/baidu"
        os.makedirs(baidu_cache_dir, exist_ok=True)

        baidu_translator = Translator(engine="baidu", cache_path=baidu_cache_dir, target_lang='en', source_lang='auto')
        
        text_to_translate_zh = "你好，世界！"
        print(f"Original (zh): {text_to_translate_zh}")

        # First translation (should be from API)
        translated_en = baidu_translator.translate(text_to_translate_zh)
        print(f"Translated (en): {translated_en}")

        # Second translation (should be from cache)
        translated_en_cached = baidu_translator.translate(text_to_translate_zh)
        print(f"Translated (en) from cache: {translated_en_cached}")
        
        assert translated_en == translated_en_cached

        # Translate to French
        translated_fr = baidu_translator.translate(text_to_translate_zh, target_lang='jp') # Baidu uses 'fra' for French
        print(f"Translated (jp): {translated_fr}")


        # baidu_translator.clear_cache()
        baidu_translator.close_cache()
        print("Baidu Translator test finished.\n")

    except ValueError as ve:
        print(f"Skipping Baidu test: {ve}")
    except Exception as e:
        print(f"Error during Baidu test: {e}")

    # Example for Tencent (assuming ENV VARS are set)
    try:
        print("Testing Tencent Translator...")
        tencent_cache_dir = "/tmp/translator_cache/tencent"
        os.makedirs(tencent_cache_dir, exist_ok=True)
        
        # You can pass api_id and api_key directly if not using ENV VARS
        # tencent_translator = Translator(
        #     engine="tencent",
        #     cache_path=tencent_cache_dir,
        #     api_id="YOUR_TENCENT_SECRET_ID",
        #     api_key="YOUR_TENCENT_SECRET_KEY",
        #     target_lang='zh',
        #     source_lang='en'
        # )
        tencent_translator = Translator(engine="tencent", cache_path=tencent_cache_dir, target_lang='zh', source_lang='en')

        text_to_translate_en = "Hello, world!"
        print(f"Original (en): {text_to_translate_en}")

        translated_zh = tencent_translator.translate(text_to_translate_en)
        print(f"Translated (zh): {translated_zh}")

        translated_zh_cached = tencent_translator.translate(text_to_translate_en)
        print(f"Translated (zh) from cache: {translated_zh_cached}")
        
        assert translated_zh == translated_zh_cached

        # tencent_translator.clear_cache()
        tencent_translator.close_cache()
        print("Tencent Translator test finished.\n")

    except ValueError as ve:
        print(f"Skipping Tencent test: {ve}")
    except Exception as e:
        print(f"Error during Tencent test: {e}")