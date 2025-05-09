import os
import pytest
from unittest.mock import patch, MagicMock
from toolkitx.lab.translator import Translator # 假设 Translator 类在这个路径下

# --- API Key Availability Check ---
# 这些变量将在模块加载时评估，反映环境变量的初始状态
# pytest-dotenv 应该在 pytest 收集测试之前加载 .env 文件
BAIDU_KEYS_AVAILABLE = bool(os.getenv("BAIDU_API_ID") and os.getenv("BAIDU_API_KEY"))
TENCENT_KEYS_AVAILABLE = bool(os.getenv("TENCENT_API_ID") and os.getenv("TENCENT_API_KEY"))

# --- Test API Credentials (can be overridden by .env for actual integration tests if not mocked) ---
# 这些主要用于那些不依赖 .env 文件，而是直接传递参数或使用 monkeypatch 的测试
TEST_BAIDU_API_ID_PARAM = "param_baidu_id"
TEST_BAIDU_API_KEY_PARAM = "param_baidu_key"
TEST_TENCENT_API_ID_PARAM = "param_tencent_id"
TEST_TENCENT_API_KEY_PARAM = "param_tencent_key"


@pytest.fixture
def temp_cache_path(tmp_path):
    """提供一个临时的缓存路径"""
    cache_dir = tmp_path / "translator_cache"
    cache_dir.mkdir()
    return str(cache_dir)

@pytest.fixture
def mock_baidu_engine_class():
    """模拟 BaiduTranslation 类，并返回被 mock 的类本身以便检查构造函数调用"""
    with patch('toolkitx.lab.translator.BaiduTranslation') as MockBaiduEngine:
        mock_instance = MagicMock()
        mock_instance.translate.return_value = "translated_from_baidu"
        MockBaiduEngine.return_value = mock_instance
        yield MockBaiduEngine

@pytest.fixture
def mock_tencent_engine_class():
    """模拟 TencentTranslation 类，并返回被 mock 的类本身"""
    with patch('toolkitx.lab.translator.TencentTranslation') as MockTencentEngine:
        mock_instance = MagicMock()
        mock_instance.translate.return_value = "translated_from_tencent"
        MockTencentEngine.return_value = mock_instance
        yield MockTencentEngine

# --- Initialization Tests ---

def test_translator_init_baidu_with_direct_params(temp_cache_path, mock_baidu_engine_class):
    """测试使用直接参数初始化百度翻译引擎"""
    translator = Translator(
        engine="baidu",
        cache_path=temp_cache_path,
        api_id=TEST_BAIDU_API_ID_PARAM,
        api_key=TEST_BAIDU_API_KEY_PARAM
    )
    assert translator.engine_name == "baidu"
    # 验证 BaiduTranslation 构造函数是否用提供的参数被调用
    mock_baidu_engine_class.assert_called_once_with(api_id=TEST_BAIDU_API_ID_PARAM, api_key=TEST_BAIDU_API_KEY_PARAM)
    translator.close_cache()

def test_translator_init_baidu_with_monkeypatched_env(temp_cache_path, mock_baidu_engine_class, monkeypatch):
    """测试使用 monkeypatch 设置的环境变量初始化百度翻译引擎"""
    monkeypatch.setenv("BAIDU_API_ID", "env_baidu_id_monkey")
    monkeypatch.setenv("BAIDU_API_KEY", "env_baidu_key_monkey")
    translator = Translator(engine="baidu", cache_path=temp_cache_path)
    assert translator.engine_name == "baidu"
    mock_baidu_engine_class.assert_called_once_with(api_id="env_baidu_id_monkey", api_key="env_baidu_key_monkey")
    translator.close_cache()

def test_translator_init_baidu_missing_keys_error(temp_cache_path, monkeypatch):
    """测试当百度密钥缺失时是否抛出 ValueError"""
    monkeypatch.delenv("BAIDU_API_ID", raising=False)
    monkeypatch.delenv("BAIDU_API_KEY", raising=False)
    with pytest.raises(ValueError, match="Baidu API ID and API Key are required"):
        Translator(engine="baidu", cache_path=temp_cache_path)

def test_translator_init_tencent_with_direct_params(temp_cache_path, mock_tencent_engine_class):
    """测试使用直接参数初始化腾讯翻译引擎"""
    translator = Translator(
        engine="tencent",
        cache_path=temp_cache_path,
        api_id=TEST_TENCENT_API_ID_PARAM,
        api_key=TEST_TENCENT_API_KEY_PARAM
    )
    assert translator.engine_name == "tencent"
    mock_tencent_engine_class.assert_called_once_with(api_id=TEST_TENCENT_API_ID_PARAM, api_key=TEST_TENCENT_API_KEY_PARAM)
    translator.close_cache()

def test_translator_init_tencent_with_monkeypatched_env(temp_cache_path, mock_tencent_engine_class, monkeypatch):
    """测试使用 monkeypatch 设置的环境变量初始化腾讯翻译引擎"""
    monkeypatch.setenv("TENCENT_API_ID", "env_tencent_id_monkey")
    monkeypatch.setenv("TENCENT_API_KEY", "env_tencent_key_monkey")
    translator = Translator(engine="tencent", cache_path=temp_cache_path)
    assert translator.engine_name == "tencent"
    mock_tencent_engine_class.assert_called_once_with(api_id="env_tencent_id_monkey", api_key="env_tencent_key_monkey")
    translator.close_cache()

def test_translator_init_tencent_missing_keys_error(temp_cache_path, monkeypatch):
    """测试当腾讯密钥缺失时是否抛出 ValueError (根据用户代码中的错误信息)"""
    monkeypatch.delenv("TENCENT_API_ID", raising=False)
    monkeypatch.delenv("TENCENT_API_KEY", raising=False)
    with pytest.raises(ValueError, match="Tencent Secret ID and Secret Key are required"):
        Translator(engine="tencent", cache_path=temp_cache_path)

def test_translator_init_unsupported_engine(temp_cache_path):
    """测试初始化不支持的引擎时是否抛出 ValueError"""
    with pytest.raises(ValueError, match="Unsupported engine: unsupported_engine"):
        Translator(engine="unsupported_engine", cache_path=temp_cache_path)

# --- Translation and Cache Tests (Relying on .env loaded keys) ---

@pytest.mark.skipif(not BAIDU_KEYS_AVAILABLE, reason="BAIDU_API_ID and/or BAIDU_API_KEY not set in environment (e.g., via .env)")
def test_translate_baidu_with_env_keys_cache_miss_and_hit(temp_cache_path, mock_baidu_engine_class):
    """测试百度翻译（使用环境变量中的密钥），包括缓存未命中和命中"""
    # 从环境变量获取预期的密钥，因为 BAIDU_KEYS_AVAILABLE 为 True
    expected_api_id = os.getenv("BAIDU_API_ID")
    expected_api_key = os.getenv("BAIDU_API_KEY")

    translator = Translator(engine="baidu", cache_path=temp_cache_path) # 不传递 api_id/key
    
    # 验证 BaiduTranslation 构造函数是否用环境变量中的密钥被调用
    mock_baidu_engine_class.assert_called_once_with(api_id=expected_api_id, api_key=expected_api_key)
    
    # 获取 mock 的翻译实例 (由 mock_baidu_engine_class 的 return_value 提供)
    mock_baidu_engine_instance = translator.translator_instance

    text = "你好"
    target_lang = "en"
    source_lang = "zh"

    # 首次翻译 (cache miss)
    result1 = translator.translate(text, target_lang=target_lang, source_lang=source_lang)
    assert result1 == "translated_from_baidu" # 这是 mock_engine_instance.translate 的返回值
    mock_baidu_engine_instance.translate.assert_called_once_with(text, target_lang, source_lang)

    # 再次翻译 (cache hit)
    mock_baidu_engine_instance.translate.reset_mock() # 重置 mock 调用计数
    result2 = translator.translate(text, target_lang=target_lang, source_lang=source_lang)
    assert result2 == "translated_from_baidu"
    mock_baidu_engine_instance.translate.assert_not_called() # 不应再次调用实际翻译引擎的 translate

    translator.close_cache()

@pytest.mark.skipif(not TENCENT_KEYS_AVAILABLE, reason="TENCENT_API_ID and/or TENCENT_API_KEY not set in environment (e.g., via .env)")
def test_translate_tencent_with_env_keys_cache_miss_and_hit(temp_cache_path, mock_tencent_engine_class):
    """测试腾讯翻译（使用环境变量中的密钥），包括缓存未命中和命中"""
    expected_api_id = os.getenv("TENCENT_API_ID")
    expected_api_key = os.getenv("TENCENT_API_KEY")

    translator = Translator(engine="tencent", cache_path=temp_cache_path)
    mock_tencent_engine_class.assert_called_once_with(api_id=expected_api_id, api_key=expected_api_key)
    mock_tencent_engine_instance = translator.translator_instance
    
    text = "Hello"
    target_lang = "zh"
    source_lang = "en"

    result1 = translator.translate(text, target_lang=target_lang, source_lang=source_lang)
    assert result1 == "translated_from_tencent"
    mock_tencent_engine_instance.translate.assert_called_once_with(text, target_lang, source_lang)

    mock_tencent_engine_instance.translate.reset_mock()
    result2 = translator.translate(text, target_lang=target_lang, source_lang=source_lang)
    assert result2 == "translated_from_tencent"
    mock_tencent_engine_instance.translate.assert_not_called()

    translator.close_cache()

@pytest.mark.skipif(not BAIDU_KEYS_AVAILABLE, reason="Baidu keys not in .env")
def test_translate_empty_string_with_env_keys(temp_cache_path, mock_baidu_engine_class):
    """测试使用环境变量密钥翻译空字符串"""
    translator = Translator(engine="baidu", cache_path=temp_cache_path)
    assert translator.translate("") == ""
    # BaiduTranslation 构造函数会被调用，但其 translate 方法不应被调用
    mock_baidu_engine_class.return_value.translate.assert_not_called()
    translator.close_cache()

@pytest.mark.skipif(not BAIDU_KEYS_AVAILABLE, reason="Baidu keys not in .env")
def test_translate_uses_default_langs_with_env_keys(temp_cache_path, mock_baidu_engine_class):
    """测试使用环境变量密钥时，是否使用默认语言"""
    default_target = "fr"
    default_source = "de"
    translator = Translator(
        engine="baidu",
        cache_path=temp_cache_path,
        target_lang=default_target,
        source_lang=default_source
    )
    mock_engine_instance = translator.translator_instance
    text = "Guten Tag"
    translator.translate(text) # 不传递 target_lang/source_lang
    mock_engine_instance.translate.assert_called_once_with(text, default_target, default_source)
    translator.close_cache()

@pytest.mark.skipif(not BAIDU_KEYS_AVAILABLE, reason="Baidu keys not in .env")
def test_translate_api_error_with_env_keys(temp_cache_path, mock_baidu_engine_class):
    """测试使用环境变量密钥时，API 错误是否正确传递"""
    translator = Translator(engine="baidu", cache_path=temp_cache_path)
    mock_engine_instance = translator.translator_instance
    mock_engine_instance.translate.side_effect = RuntimeError("API communication error")
    
    with pytest.raises(RuntimeError, match="API communication error"):
        translator.translate("text to fail")
    translator.close_cache()

# --- Cache Management Tests (Relying on .env loaded keys) ---

@pytest.mark.skipif(not BAIDU_KEYS_AVAILABLE, reason="Baidu keys not in .env")
def test_clear_cache_with_env_keys(temp_cache_path, mock_baidu_engine_class):
    """测试使用环境变量密钥时，清除缓存的功能"""
    translator = Translator(engine="baidu", cache_path=temp_cache_path)
    mock_engine_instance = translator.translator_instance
    text = "Cache me"
    target_lang = "en"
    
    # 翻译并缓存
    translator.translate(text, target_lang=target_lang)
    mock_engine_instance.translate.assert_called_once()

    # 清除缓存
    translator.clear_cache()
    
    # 再次翻译，应该会调用API (cache miss)
    mock_engine_instance.translate.reset_mock()
    translator.translate(text, target_lang=target_lang)
    mock_engine_instance.translate.assert_called_once()
    
    translator.close_cache()

def test_close_cache_direct_params(temp_cache_path, mock_baidu_engine_class): # 这个测试不需要依赖环境变量
    """测试 close_cache 方法（不依赖环境变量密钥）"""
    translator = Translator(
        engine="baidu", 
        cache_path=temp_cache_path, 
        api_id="dummy_id", 
        api_key="dummy_key"
    )
    # 模拟 Cache 对象的 close 方法
    with patch.object(translator.cache, 'close', wraps=translator.cache.close) as mock_cache_close:
        translator.close_cache()
        mock_cache_close.assert_called_once()