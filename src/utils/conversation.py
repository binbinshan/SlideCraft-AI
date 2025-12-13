"""
对话历史管理
支持多轮对话和上下文记忆
"""
from typing import List, Dict, Optional
from datetime import datetime
import json
from utils.helpers import save_json, load_json, ensure_dir


class ConversationHistory:
    """对话历史管理器"""

    def __init__(self, session_id: str = None):
        """
        初始化对话历史

        Args:
            session_id: 会话ID
        """
        self.session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.messages = []
        self.context = {
            "topic": None,
            "style": None,
            "template": None,
            "current_slide": None,
            "modifications": []
        }

    def add_message(
            self,
            role: str,
            content: str,
            metadata: Dict = None
    ) -> None:
        """
        添加消息到历史

        Args:
            role: 角色(user/assistant/system)
            content: 消息内容
            metadata: 额外元数据
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        self.messages.append(message)

    def add_user_message(self, content: str, metadata: Dict = None) -> None:
        """添加用户消息"""
        self.add_message("user", content, metadata)

    def add_assistant_message(self, content: str, metadata: Dict = None) -> None:
        """添加助手消息"""
        self.add_message("assistant", content, metadata)

    def add_system_message(self, content: str, metadata: Dict = None) -> None:
        """添加系统消息"""
        self.add_message("system", content, metadata)

    def update_context(self, **kwargs) -> None:
        """
        更新上下文信息

        Args:
            **kwargs: 要更新的上下文字段
        """
        self.context.update(kwargs)

    def get_context(self, key: str = None):
        """
        获取上下文信息

        Args:
            key: 上下文键,None则返回全部

        Returns:
            上下文值
        """
        if key is None:
            return self.context
        return self.context.get(key)

    def get_all_context(self):
        """
        获取所有上下文信息（包括消息历史）

        Returns:
            包含消息和上下文的完整数据
        """
        return {
            "context": self.context,
            "messages": self.messages,
            "message_count": len(self.messages)
        }

    def get_recent_messages(self, n: int = 5) -> List[Dict]:
        """
        获取最近的N条消息

        Args:
            n: 消息数量

        Returns:
            消息列表
        """
        return self.messages[-n:] if len(self.messages) > n else self.messages

    def get_all_messages(self) -> List[Dict]:
        """获取所有消息"""
        return self.messages

    def format_for_display(self) -> str:
        """
        格式化为显示文本

        Returns:
            格式化的对话历史
        """
        output = []
        for msg in self.messages:
            role = msg["role"]
            content = msg["content"]
            timestamp = datetime.fromisoformat(msg["timestamp"]).strftime("%H:%M:%S")

            if role == "user":
                output.append(f"👤 用户 [{timestamp}]:\n{content}\n")
            elif role == "assistant":
                output.append(f"🤖 助手 [{timestamp}]:\n{content}\n")
            else:
                output.append(f"⚙️ 系统 [{timestamp}]:\n{content}\n")

        return "\n".join(output)

    def save(self, filepath: str = None) -> str:
        """
        保存对话历史

        Args:
            filepath: 保存路径,None则使用默认路径

        Returns:
            保存路径
        """
        if filepath is None:
            ensure_dir("output/conversations")
            filepath = f"output/conversations/{self.session_id}.json"

        data = {
            "session_id": self.session_id,
            "context": self.context,
            "messages": self.messages,
            "saved_at": datetime.now().isoformat()
        }

        save_json(data, filepath)
        return filepath

    @classmethod
    def load(cls, filepath: str) -> 'ConversationHistory':
        """
        加载对话历史

        Args:
            filepath: 文件路径

        Returns:
            ConversationHistory实例
        """
        data = load_json(filepath)

        history = cls(session_id=data["session_id"])
        history.context = data["context"]
        history.messages = data["messages"]

        return history

    def clear(self) -> None:
        """清空历史"""
        self.messages = []
        self.context = {
            "topic": None,
            "style": None,
            "template": None,
            "current_slide": None,
            "modifications": []
        }

    def summary(self) -> str:
        """
        生成对话摘要

        Returns:
            摘要文本
        """
        summary = f"""
            📊 对话摘要
            ━━━━━━━━━━━━━━━━━━━━
            会话ID: {self.session_id}
            消息数: {len(self.messages)}
            
            📋 当前上下文:
            主题: {self.context.get('topic', '未设置')}
            风格: {self.context.get('style', '未设置')}
            模板: {self.context.get('template', '未设置')}
            当前页: {self.context.get('current_slide', '未设置')}
            修改次数: {len(self.context.get('modifications', []))}
        """
        return summary.strip()


class ConversationManager:
    """对话管理器 - 管理多个会话"""

    def __init__(self):
        """初始化对话管理器"""
        self.sessions = {}
        self.current_session_id = None

    def create_session(self, session_id: str = None) -> ConversationHistory:
        """
        创建新会话

        Args:
            session_id: 会话ID

        Returns:
            ConversationHistory实例
        """
        history = ConversationHistory(session_id)
        self.sessions[history.session_id] = history
        self.current_session_id = history.session_id
        return history

    def get_session(self, session_id: str = None) -> Optional[ConversationHistory]:
        """
        获取会话

        Args:
            session_id: 会话ID,None则返回当前会话

        Returns:
            ConversationHistory实例
        """
        if session_id is None:
            session_id = self.current_session_id

        return self.sessions.get(session_id)

    def get_current_session(self) -> Optional[ConversationHistory]:
        """获取当前会话"""
        return self.get_session()

    def switch_session(self, session_id: str) -> bool:
        """
        切换到指定会话

        Args:
            session_id: 会话ID

        Returns:
            是否成功
        """
        if session_id in self.sessions:
            self.current_session_id = session_id
            return True
        return False

    def list_sessions(self) -> List[str]:
        """列出所有会话ID"""
        return list(self.sessions.keys())

    def delete_session(self, session_id: str) -> bool:
        """
        删除会话

        Args:
            session_id: 会话ID

        Returns:
            是否成功
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            if self.current_session_id == session_id:
                self.current_session_id = None
            return True
        return False