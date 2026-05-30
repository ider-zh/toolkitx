# 从子模块导入，使其可以直接从 toolkitx 包导入
from . import lab
from .text_utils import split_text_by_word_count, truncate_text_smart
from .html_utils import html_to_markdown

# 定义 __all__，当用户使用 from toolkitx import * 时，会导入这些符号
__all__ = [
    "truncate_text_smart",
    "split_text_by_word_count",
    "html_to_markdown",
    "lab",
]

import importlib.metadata

try:
    # 这将从已安装包的元数据中读取版本号
    # 包名 "toolkitx" 与 pyproject.toml 中的 name 一致
    __version__ = importlib.metadata.version("toolkitx")
except importlib.metadata.PackageNotFoundError:
    # 如果包尚未安装（例如，在未执行 editable install 的源码状态下运行），则会发生此错误。
    # 在开发初期，或者在当前环境尚未执行 `pip install -e .` 时可能会遇到。
    # 构建系统 (Hatchling) 在构建包时会使用 pyproject.toml 中的版本。
    # 一旦安装（即使是可编辑模式安装），importlib.metadata.version 应该能正常工作。
    # 对于未安装状态，可以设置一个占位符版本。
    __version__ = "0.0.0.dev0"  # 或者 "unknown"
