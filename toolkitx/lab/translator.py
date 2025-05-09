import os
from abc import ABC, abstractmethod
from typing import Optional, Literal
from diskcache import Cache
from transgpt.trans_baidu import BaiduTranslation
from transgpt.trans_tencent import TencentTranslation
import hashlib

# 定义支持的翻译引擎类型
SUPPORTED_ENGINES = Literal["baidu", "tencent"]

class TranslatorInterface(ABC):
    """
    Abstract base class for a translator.
    Defines the common interface for translation services.
    """

    @abstractmethod
    def translate(self, text: str, target_lang: str, source_lang: str = 'auto') -> str:
        """
        Translate text from a source language to a target language.

        :param text: The text to translate.
        :param target_lang: The target language code (e.g., 'en', 'zh').
        :param source_lang: The source language code (e.g., 'auto', 'en', 'zh').
        :return: The translated text.
        """
        pass

    @abstractmethod
    def clear_cache(self) -> None:
        """
        Clear the translation cache.
        """
        pass


class Translator(TranslatorInterface):
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
        print("no cache, cache_key:",cache_key)
        # print(f"Cache miss. Translating: {text[:30]}...") # For debugging
        try:
            # py-transgpt's translate method takes (text, target_language, source_language)
            translated_text = self.translator_instance.translate(text, _target_lang, _source_lang)
            print("set cache:",text,translated_text)
            if translated_text: # Ensure we don't cache None or empty if translation fails silently
                self.cache.set(cache_key, translated_text)
            return translated_text
        except Exception as e:
            # Log error or handle as needed
            print(f"Error during translation with {self.engine_name}: {e}")
            # Depending on requirements, you might want to re-raise or return original text/error message
            raise  # Re-raise the exception to make the caller aware

    def clear_cache(self) -> None:
        """
        Clear all items from the translation cache for this translator instance.
        """
        self.cache.clear()
        print(f"Cache cleared for path: {self.cache.directory}")

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

        baidu_translator = Translator(engine="baidu", cache_path=baidu_cache_dir, target_lang='en', source_lang='zh')
        
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
        translated_fr = baidu_translator.translate(text_to_translate_zh, target_lang='fr') # Baidu uses 'fra' for French
        print(f"Translated (fr): {translated_fr}")


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