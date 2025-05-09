# 从子模块导入，使其可以直接从 toolkitx 包导入
from .hello import hello
from .text_utils import truncate_text_smart, split_text_by_word_count

# 定义 __all__，当用户使用 from toolkitx import * 时，会导入这些符号
__all__ = [
    "hello",
    "truncate_text_smart",
    "split_text_by_word_count"
]

# 你也可以在这里定义包级别的版本号等元数据
__version__ = "0.0.1" # 与 pyproject.toml 中的 version 一致