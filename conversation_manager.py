# conversation_manager_final.py
# 最终修复版对话历史管理器

import json
import time
import os
import traceback
from typing import List, Dict, Any, Optional
from datetime import datetime

from config import DATABASE_SETTINGS

# 根据配置选择数据库管理器
if DATABASE_SETTINGS.get("type") == "supabase":
    from supabase_manager import SupabaseManager
    DatabaseManager = SupabaseManager
else:
    from mysql_manager import MySQLManager
    DatabaseManager = MySQLManager

# 自定义 JSON 编码器，处理 datetime 对象
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


class ConversationManager:
    """最终修复版对话历史管理器"""

    def __init__(self, max_history: int = 10, persist_file: Optional[str] = None):
        """
        初始化对话管理器

        参数:
            max_history: 最大历史记录数
            persist_file: 持久化文件路径
        """
        self.max_history = max_history
        self.persist_file = persist_file
        self.conversations = {}  # user_id -> {session_id -> conversation}
        self.current_session_id = None
        self.current_user_id = None

        # 初始化数据库管理器
        self.mysql_manager = DatabaseManager()

        # 加载持久化的对话记录
        if persist_file:
            self._load_conversations()

        print(f"✅ 对话管理器初始化完成")

    def _set_current_to_latest(self, user_id: int):
        """设置当前会话为最新的会话"""
        if not self.conversations or user_id not in self.conversations:
            return

        # 找到最新的会话（按更新时间）
        user_sessions = self.conversations[user_id]
        if user_sessions:
            # 确保所有updated_at都是字符串格式
            latest_session = max(
                user_sessions.values(),
                key=lambda x: str(x.get("updated_at", ""))
            )
            self.current_session_id = latest_session.get("id")
            print(f"  当前会话设置为: {latest_session.get('title', '未知')}")

    def create_session(self, user_id: int, session_id: Optional[str] = None, title: Optional[str] = None, set_as_current: bool = True) -> str:
        """
        创建新的对话会话

        参数:
            user_id: 用户ID
            session_id: 可选的会话ID
            title: 可选的会话标题
            set_as_current: 是否将新会话设置为当前会话

        返回:
            会话ID
        """
        if user_id not in self.conversations:
            self.conversations[user_id] = {}

        if not session_id:
            session_id = f"session_{int(time.time())}_{len(self.conversations[user_id])}"

        if not title:
            title = f"对话 {len(self.conversations[user_id]) + 1}"

        # 使用字符串格式的时间戳，确保JSON序列化不会失败
        current_time = datetime.now().isoformat()
        session_data = {
            "id": session_id,
            "created_at": current_time,
            "messages": [],
            "title": title,
            "updated_at": current_time
        }

        self.conversations[user_id][session_id] = session_data

        if set_as_current:
            self.current_session_id = session_id
            self.current_user_id = user_id
        print(f"✅ 创建新会话: {title} (ID: {session_id}) 为用户: {user_id}")

        # 异步保存到MySQL，避免阻塞主线程
        import threading
        def save_to_mysql():
            try:
                self.mysql_manager.save_session(user_id, session_id, session_data)
            except Exception as e:
                print(f"❌ 异步保存到MySQL失败: {e}")

        # 启动线程保存到MySQL
        threading.Thread(target=save_to_mysql, daemon=True).start()

        # 异步保存到文件
        if self.persist_file:
            def save_to_file():
                try:
                    self._save_conversations()
                except Exception as e:
                    print(f"❌ 异步保存到文件失败: {e}")
            threading.Thread(target=save_to_file, daemon=True).start()

        return session_id

    def add_message(self, user_id: int, role: str, content: str, session_id: Optional[str] = None,
                    metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        添加消息到对话

        参数:
            user_id: 用户ID
            role: 角色 ('user' 或 'assistant')
            content: 消息内容
            session_id: 会话ID，None则使用当前会话
            metadata: 元数据

        返回:
            添加的消息
        """
        if user_id not in self.conversations:
            self.conversations[user_id] = {}

        if session_id is None:
            if self.current_session_id is None or self.current_user_id != user_id:
                session_id = self.create_session(user_id)
            else:
                session_id = self.current_session_id

        if session_id not in self.conversations[user_id]:
            # 如果会话不存在，创建新会话，但不将其设置为当前会话
            # 这样可以确保消息被添加到正确的会话中
            self.create_session(user_id, session_id, f"自动创建会话", set_as_current=False)

        # 使用字符串格式的时间戳，确保JSON序列化不会失败
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }

        self.conversations[user_id][session_id]["messages"].append(message)
        self.conversations[user_id][session_id]["updated_at"] = datetime.now().isoformat()

        # 限制历史记录长度
        if len(self.conversations[user_id][session_id]["messages"]) > self.max_history * 2:
            self.conversations[user_id][session_id]["messages"] = self.conversations[user_id][session_id]["messages"][-self.max_history * 2:]

        # 异步保存到MySQL，避免阻塞主线程
        import threading
        def save_to_mysql():
            try:
                session_data = self.conversations[user_id][session_id]
                self.mysql_manager.save_session(user_id, session_id, session_data)
            except Exception as e:
                print(f"❌ 异步保存到MySQL失败: {e}")

        # 启动线程保存到MySQL
        threading.Thread(target=save_to_mysql, daemon=True).start()

        # 异步保存到文件
        if self.persist_file:
            def save_to_file():
                try:
                    self._save_conversations()
                except Exception as e:
                    print(f"❌ 异步保存到文件失败: {e}")
            threading.Thread(target=save_to_file, daemon=True).start()

        return message

    def get_conversation_history(self, user_id: int, session_id: Optional[str] = None,
                                 as_string: bool = False) -> Any:
        """
        获取对话历史

        参数:
            user_id: 用户ID
            session_id: 会话ID，None则使用当前会话
            as_string: 是否返回字符串格式

        返回:
            对话历史
        """
        if user_id not in self.conversations:
            return [] if not as_string else ""

        if session_id is None:
            if self.current_user_id == user_id:
                session_id = self.current_session_id
            else:
                return [] if not as_string else ""

        if session_id not in self.conversations[user_id]:
            return [] if not as_string else ""

        messages = self.conversations[user_id][session_id]["messages"]

        if not as_string:
            return messages

        # 转换为字符串格式
        history_str = ""
        for msg in messages:
            if msg["role"] == "user":
                history_str += f"用户: {msg['content']}\n"
            else:
                history_str += f"助手: {msg['content']}\n"

        return history_str

    def get_recent_history(self, user_id: int, session_id: Optional[str] = None,
                           last_n: int = 3) -> str:
        """
        获取最近的对话历史（字符串格式）

        参数:
            user_id: 用户ID
            session_id: 会话ID
            last_n: 返回最近几轮对话

        返回:
            最近对话历史的字符串
        """
        if user_id not in self.conversations:
            return ""

        if session_id is None:
            if self.current_user_id == user_id:
                session_id = self.current_session_id
            else:
                return ""

        if session_id not in self.conversations[user_id]:
            return ""

        messages = self.conversations[user_id][session_id]["messages"]
        if len(messages) == 0:
            return ""

        # 获取最后last_n轮对话（每轮包含user和assistant）
        if len(messages) > 0:
            # 排除最新的消息，避免重复发送用户问题
            # 只取最后last_n轮对话
            recent_messages = messages[-(last_n * 2):-1] if len(messages) > last_n * 2 + 1 else messages[:-1] if len(messages) > 1 else []
        else:
            recent_messages = []

        history_str = ""
        for msg in recent_messages:
            if msg["role"] == "user":
                history_str += f"用户: {msg['content']}\n"
            else:
                history_str += f"助手: {msg['content']}\n"

        return history_str

    def clear_conversation(self, user_id: int, session_id: Optional[str] = None):
        """
        清空对话历史

        参数:
            user_id: 用户ID
            session_id: 会话ID，None则使用当前会话
        """
        if user_id not in self.conversations:
            return

        if session_id is None:
            if self.current_user_id == user_id:
                session_id = self.current_session_id
            else:
                return

        if session_id in self.conversations[user_id]:
            self.conversations[user_id][session_id]["messages"] = []
            # 使用字符串格式的时间戳，确保JSON序列化不会失败
            self.conversations[user_id][session_id]["updated_at"] = datetime.now().isoformat()

            print(f"✅ 已清空会话: {self.conversations[user_id][session_id].get('title', session_id)}")

            # 异步保存到MySQL，避免阻塞主线程
            import threading
            def save_to_mysql():
                try:
                    session_data = self.conversations[user_id][session_id]
                    self.mysql_manager.save_session(user_id, session_id, session_data)
                except Exception as e:
                    print(f"❌ 异步保存到MySQL失败: {e}")

            # 启动线程保存到MySQL
            threading.Thread(target=save_to_mysql, daemon=True).start()

            # 异步保存到文件
            if self.persist_file:
                def save_to_file():
                    try:
                        self._save_conversations()
                    except Exception as e:
                        print(f"❌ 异步保存到文件失败: {e}")
                threading.Thread(target=save_to_file, daemon=True).start()

    def delete_session(self, user_id: int, session_id: str):
        """
        删除会话

        参数:
            user_id: 用户ID
            session_id: 会话ID
        """
        if user_id in self.conversations and session_id in self.conversations[user_id]:
            session_title = self.conversations[user_id][session_id].get("title", session_id)
            del self.conversations[user_id][session_id]

            # 从MySQL删除
            self.mysql_manager.delete_session(user_id, session_id)

            if self.persist_file:
                self._save_conversations()

            print(f"✅ 已删除会话: {session_title}")

            # 如果删除的是当前会话，重置当前会话
            if self.current_session_id == session_id and self.current_user_id == user_id:
                if self.conversations[user_id]:
                    # 设置为第一个可用会话
                    self.current_session_id = next(iter(self.conversations[user_id]))
                else:
                    self.current_session_id = None

    def clear_all_sessions(self, user_id: int):
        """
        清空用户的所有历史会话记录

        参数:
            user_id: 用户ID
        """
        if user_id in self.conversations:
            # 获取所有会话ID
            session_ids = list(self.conversations[user_id].keys())
            
            # 删除每个会话
            for session_id in session_ids:
                # 从MySQL删除
                self.mysql_manager.delete_session(user_id, session_id)
                # 从本地缓存删除
                del self.conversations[user_id][session_id]
            
            # 保存更改到文件
            if self.persist_file:
                self._save_conversations()
            
            # 重置当前会话
            self.current_session_id = None
            if self.current_user_id == user_id:
                self.current_user_id = None
            
            print(f"✅ 已清空用户 {user_id} 的所有会话记录")
        else:
            print(f"⚠️ 用户 {user_id} 没有会话记录")

    def list_sessions(self, user_id: int) -> List[Dict[str, Any]]:
        """
        列出用户的所有会话

        参数:
            user_id: 用户ID

        返回:
            会话列表
        """
        # 先检查本地缓存是否有数据
        if user_id in self.conversations and self.conversations[user_id]:
            # 构建返回列表
            sessions = []
            for session_id, conv in self.conversations[user_id].items():
                session_info = {
                    "id": session_id,
                    "title": conv["title"],
                    "created_at": conv["created_at"],
                    "updated_at": conv["updated_at"],
                    "message_count": len(conv["messages"]),
                    "is_current": session_id == self.current_session_id and user_id == self.current_user_id
                }
                sessions.append(session_info)

            # 按更新时间排序（最新的在前面）
            sessions.sort(key=lambda x: x["updated_at"], reverse=True)
            return sessions
        
        # 本地缓存中没有数据，从数据库加载
        mysql_sessions = self.mysql_manager.list_user_sessions(user_id)
        
        # 更新本地缓存
        if user_id not in self.conversations:
            self.conversations[user_id] = {}
        
        for session in mysql_sessions:
            session_id = session["id"]
            # 确保时间戳是字符串格式
            if isinstance(session.get("created_at"), datetime):
                session["created_at"] = session["created_at"].isoformat()
            if isinstance(session.get("updated_at"), datetime):
                session["updated_at"] = session["updated_at"].isoformat()
            self.conversations[user_id][session_id] = session
        
        # 构建返回列表
        sessions = []
        if user_id in self.conversations:
            for session_id, conv in self.conversations[user_id].items():
                session_info = {
                    "id": session_id,
                    "title": conv["title"],
                    "created_at": conv["created_at"],
                    "updated_at": conv["updated_at"],
                    "message_count": len(conv["messages"]),
                    "is_current": session_id == self.current_session_id and user_id == self.current_user_id
                }
                sessions.append(session_info)

        # 按更新时间排序（最新的在前面）
        sessions.sort(key=lambda x: x["updated_at"], reverse=True)
        return sessions

    def set_session_title(self, user_id: int, title: str, session_id: Optional[str] = None) -> bool:
        """
        设置会话标题

        参数:
            user_id: 用户ID
            title: 标题
            session_id: 会话ID，None则使用当前会话

        返回:
            是否成功
        """
        if user_id not in self.conversations:
            return False

        if session_id is None:
            if self.current_user_id == user_id:
                session_id = self.current_session_id
            else:
                return False

        if session_id in self.conversations[user_id]:
            self.conversations[user_id][session_id]["title"] = title
            # 使用字符串格式的时间戳，确保JSON序列化不会失败
            self.conversations[user_id][session_id]["updated_at"] = datetime.now().isoformat()

            print(f"✅ 已更新会话标题: {title}")

            # 异步保存到MySQL，避免阻塞主线程
            import threading
            def save_to_mysql():
                try:
                    session_data = self.conversations[user_id][session_id]
                    self.mysql_manager.save_session(user_id, session_id, session_data)
                except Exception as e:
                    print(f"❌ 异步保存到MySQL失败: {e}")

            # 启动线程保存到MySQL
            threading.Thread(target=save_to_mysql, daemon=True).start()

            # 异步保存到文件
            if self.persist_file:
                def save_to_file():
                    try:
                        self._save_conversations()
                    except Exception as e:
                        print(f"❌ 异步保存到文件失败: {e}")
                threading.Thread(target=save_to_file, daemon=True).start()

            return True

        return False

    def get_session(self, user_id: int, session_id: str) -> Optional[Dict[str, Any]]:
        """
        获取指定会话

        参数:
            user_id: 用户ID
            session_id: 会话ID

        返回:
            会话信息，不存在则返回None
        """
        if user_id in self.conversations:
            return self.conversations[user_id].get(session_id)
        return None

    def get_current_session(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        获取当前会话

        参数:
            user_id: 用户ID

        返回:
            会话信息，不存在则返回None
        """
        if self.current_session_id and self.current_user_id == user_id:
            return self.get_session(user_id, self.current_session_id)
        return None

    def switch_session(self, user_id: int, session_id: str) -> bool:
        """
        切换到指定会话

        参数:
            user_id: 用户ID
            session_id: 会话ID

        返回:
            是否切换成功
        """
        if user_id in self.conversations and session_id in self.conversations[user_id]:
            self.current_session_id = session_id
            self.current_user_id = user_id
            print(f"✅ 已切换到会话: {self.conversations[user_id][session_id].get('title', session_id)}")
            return True
        return False

    def _save_conversations(self):
        """保存对话到文件"""
        if not self.persist_file:
            return

        try:
            # 确保目录存在
            if os.path.dirname(self.persist_file):
                os.makedirs(os.path.dirname(self.persist_file), exist_ok=True)

            with open(self.persist_file, 'w', encoding='utf-8') as f:
                json.dump(self.conversations, f, ensure_ascii=False, indent=2, cls=DateTimeEncoder)
            print(f"✅ 对话已保存到: {self.persist_file}")
        except Exception as e:
            print(f"❌ 保存对话失败: {e}")
            traceback.print_exc()

    def _load_conversations(self):
        """从文件加载对话"""
        if not self.persist_file:
            return

        try:
            if os.path.exists(self.persist_file):
                with open(self.persist_file, 'r', encoding='utf-8') as f:
                    try:
                        loaded_conversations = json.load(f)
                    except json.JSONDecodeError as e:
                        print(f"❌ JSON 解析错误: {e}")
                        print("ℹ️ 将创建新的对话文件")
                        # 创建一个新的空文件
                        with open(self.persist_file, 'w', encoding='utf-8') as f_new:
                            json.dump({}, f_new, ensure_ascii=False, indent=2)
                        self.conversations = {}
                        return

                # 验证加载的数据结构
                if isinstance(loaded_conversations, dict):
                    # 清理重复的用户数据，确保每个用户ID只出现一次
                    unique_conversations = {}
                    for user_id, sessions in loaded_conversations.items():
                        if user_id not in unique_conversations:
                            unique_conversations[user_id] = sessions
                    
                    self.conversations = unique_conversations
                    user_count = len(self.conversations)
                    total_sessions = sum(len(sessions) for sessions in self.conversations.values())
                    print(f"✅ 从 {self.persist_file} 加载了 {user_count} 个用户的 {total_sessions} 个会话")
                else:
                    print(f"❌ 加载的对话格式错误，将创建新对话")
                    self.conversations = {}
            else:
                print(f"ℹ️ 对话文件不存在，将创建新文件: {self.persist_file}")
        except Exception as e:
            print(f"❌ 加载对话失败: {e}")
            traceback.print_exc()
            self.conversations = {}


def test_conversation_manager_final():
    """测试最终修复版对话管理器"""
    print("测试最终修复版对话管理器")
    print("=" * 60)

    # 创建管理器
    manager = ConversationManager(max_history=5, persist_file="test_conversations_final.json")

    # 测试用户ID
    test_user_id = 1

    # 创建新会话
    session1_id = manager.create_session(user_id=test_user_id, title="测试会话1")
    print(f"1. 创建会话: {session1_id}")

    # 添加消息
    print("\n2. 添加对话消息...")
    manager.add_message(user_id=test_user_id, role="user", content="你好，这是第一个会话")
    manager.add_message(user_id=test_user_id, role="assistant", content="你好！这是第一个会话的回复")

    # 创建第二个会话
    print("\n3. 创建第二个会话...")
    session2_id = manager.create_session(user_id=test_user_id, title="测试会话2")
    manager.add_message(user_id=test_user_id, role="user", content="你好，这是第二个会话", session_id=session2_id)
    manager.add_message(user_id=test_user_id, role="assistant", content="你好！这是第二个会话的回复", session_id=session2_id)

    # 列出会话
    print("\n4. 列出所有会话:")
    sessions = manager.list_sessions(user_id=test_user_id)
    for session in sessions:
        current = " ✅" if session["is_current"] else ""
        print(f"  - {session['title']} (ID: {session['id']}) - {session['message_count']} 条消息{current}")

    # 测试切换会话
    print("\n5. 切换会话...")
    manager.switch_session(user_id=test_user_id, session_id=session1_id)
    current_session = manager.get_current_session(user_id=test_user_id)
    print(f"  当前会话: {current_session.get('title') if current_session else '无'}")

    # 测试设置标题
    print("\n6. 设置会话标题...")
    manager.set_session_title(user_id=test_user_id, title="更新后的标题")

    sessions_after = manager.list_sessions(user_id=test_user_id)
    for session in sessions_after:
        if session["id"] == session1_id:
            print(f"  新标题: {session['title']}")

    # 测试获取历史
    print("\n7. 获取当前会话历史:")
    history = manager.get_conversation_history(user_id=test_user_id, as_string=True)
    print(history[:200] + "..." if len(history) > 200 else history)

    # 测试清空对话
    print("\n8. 清空当前对话...")
    manager.clear_conversation(user_id=test_user_id)

    history_after = manager.get_conversation_history(user_id=test_user_id, as_string=True)
    print(f"  清空后历史长度: {len(history_after)}")

    # 测试删除会话
    print("\n9. 删除第二个会话...")
    manager.delete_session(user_id=test_user_id, session_id=session2_id)

    final_sessions = manager.list_sessions(user_id=test_user_id)
    print(f"  剩余会话数: {len(final_sessions)}")

    print("\n" + "=" * 60)
    print("✅ 最终修复版对话管理器测试完成！")
    print("=" * 60)

    return manager


if __name__ == "__main__":
    test_conversation_manager_final()