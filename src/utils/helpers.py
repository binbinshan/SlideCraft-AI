"""
工具函数集合
"""
import re
import os
import json
from typing import Dict, List, Any
from datetime import datetime


def ensure_dir(directory: str) -> None:
    """
    确保目录存在,不存在则创建

    Args:
        directory: 目录路径
    """
    os.makedirs(directory, exist_ok=True)


def parse_json_response(response_text: str) -> Dict:
    """
    解析JSON响应,处理各种格式问题

    Args:
        response_text: 原始响应文本

    Returns:
        解析后的字典
    """
    # 移除markdown标记
    text = re.sub(r'^```json\s*|\s*```$', '', response_text, flags=re.MULTILINE)
    text = re.sub(r'^```\s*|\s*```$', '', text, flags=re.MULTILINE)
    text = text.strip()

    # 尝试解析
    return json.loads(text)

def save_json(data: Dict, filepath: str, indent: int = 2) -> None:
    """
    保存JSON文件

    Args:
        data: 要保存的数据
        filepath: 文件路径
        indent: 缩进空格数
    """
    ensure_dir(os.path.dirname(filepath))
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)


def load_json(filepath: str) -> Dict:
    """
    读取JSON文件

    Args:
        filepath: 文件路径

    Returns:
        解析后的数据
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def format_timestamp(dt: datetime = None) -> str:
    """
    格式化时间戳

    Args:
        dt: datetime对象,默认为当前时间

    Returns:
        格式化的时间字符串
    """
    if dt is None:
        dt = datetime.now()
    return dt.strftime("%Y%m%d_%H%M%S")


def validate_outline(outline: Dict) -> tuple[bool, str]:
    """
    验证大纲格式

    Args:
        outline: 大纲字典

    Returns:
        (是否有效, 错误信息)
    """
    # 检查必需字段
    if "title" not in outline:
        return False, "缺少title字段"

    if "slides" not in outline:
        return False, "缺少slides字段"

    if not isinstance(outline["slides"], list):
        return False, "slides必须是数组"

    if len(outline["slides"]) == 0:
        return False, "slides不能为空"

    # 检查每页格式
    required_fields = ["page", "title", "type"]
    for i, slide in enumerate(outline["slides"]):
        for field in required_fields:
            if field not in slide:
                return False, f"第{i + 1}页缺少{field}字段"

    return True, ""


def estimate_generation_time(num_slides: int) -> int:
    """
    估算生成时间(秒)

    Args:
        num_slides: 页数

    Returns:
        预估时间(秒)
    """
    # 大纲: ~10秒
    # 每页内容: ~5秒
    return 10 + num_slides * 5


def format_time(seconds: int) -> str:
    """
    格式化时间显示

    Args:
        seconds: 秒数

    Returns:
        格式化的时间字符串
    """
    if seconds < 60:
        return f"{seconds}秒"
    else:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}分{secs}秒"


def truncate_text(text: str, max_length: int = 50) -> str:
    """
    截断文本

    Args:
        text: 原始文本
        max_length: 最大长度

    Returns:
        截断后的文本
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def count_words(text: str) -> int:
    """
    统计字数(中英文混合)

    Args:
        text: 文本

    Returns:
        字数
    """
    # 中文字符
    chinese_count = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')

    # 英文单词
    english_words = len([word for word in text.split() if word.isalpha()])

    return chinese_count + english_words


def summarize_outline(outline: Dict) -> str:
    """
    生成大纲摘要

    Args:
        outline: 大纲字典

    Returns:
        摘要文本
    """
    slides = outline.get("slides", [])

    summary = f"标题: {outline.get('title', 'N/A')}\n"
    summary += f"总页数: {len(slides)}\n"
    summary += f"结构: "

    # 统计页面类型
    types = {}
    for slide in slides:
        slide_type = slide.get("type", "content")
        types[slide_type] = types.get(slide_type, 0) + 1

    type_str = ", ".join([f"{k}({v})" for k, v in types.items()])
    summary += type_str

    return summary


def create_progress_bar(current: int, total: int, width: int = 30) -> str:
    """
    创建进度条

    Args:
        current: 当前进度
        total: 总数
        width: 进度条宽度

    Returns:
        进度条字符串
    """
    if total == 0:
        percent = 0
    else:
        percent = current / total

    filled = int(width * percent)
    bar = "█" * filled + "░" * (width - filled)
    percentage = int(percent * 100)

    return f"[{bar}] {percentage}% ({current}/{total})"


class Logger:
    """简单的日志记录器"""

    def __init__(self, log_file: str = None):
        """
        初始化日志记录器

        Args:
            log_file: 日志文件路径
        """
        self.log_file = log_file
        if log_file:
            ensure_dir(os.path.dirname(log_file))

    def log(self, message: str, level: str = "INFO") -> None:
        """
        记录日志

        Args:
            message: 日志消息
            level: 日志级别
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"

        print(log_entry)

        if self.log_file:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry + "\n")

    def info(self, message: str) -> None:
        """记录INFO级别日志"""
        self.log(message, "INFO")

    def warning(self, message: str) -> None:
        """记录WARNING级别日志"""
        self.log(message, "WARNING")

    def error(self, message: str) -> None:
        """记录ERROR级别日志"""
        self.log(message, "ERROR")