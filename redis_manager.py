# redis_manager.py
# Redis会话管理器

import redis
import json
from typing import Optional, Dict, Any, List
import time

class RedisManager:
    """Redis会话管理器"""

    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0, password: Optional[str] = None):
        """
        初始化Redis管理器

        参数:
            host: Redis服务器地址
            port: Redis服务器端口
            db: Redis数据库编号
            password: Redis密码
        """
        try:
            self.redis_client = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=True
            )
            # 测试连接
            self.redis_client.ping()
            print("✅ Redis连接成功")
        except Exception as e:
            print(f"❌ Redis连接失败: {e}")
            # 创建一个内存存储作为后备
            self.redis_client = None
            self.memory_store = {}
            print("⚠️  使用内存存储作为后备")

    def _get_key(self, user_id: int, session_id: str) -> str:
        """
        生成Redis键

        参数:
            user_id: 用户ID
            session_id: 会话ID

        返回:
            Redis键
        """
        return f"user:{user_id}:session:{session_id}"

    def _get_user_sessions_key(self, user_id: int) -> str:
        """
        生成用户会话列表的Redis键

        参数:
            user_id: 用户ID

        返回:
            Redis键
        """
        return f"user:{user_id}:sessions"

    def save_session(self, user_id: int, session_id: str, session_data: Dict[str, Any]):
        """
        保存会话数据

        参数:
            user_id: 用户ID
            session_id: 会话ID
            session_data: 会话数据
        """
        try:
            key = self._get_key(user_id, session_id)
            if self.redis_client:
                self.redis_client.setex(
                    key,
                    86400 * 7,  # 7天过期
                    json.dumps(session_data, ensure_ascii=False)
                )
                # 更新用户会话列表
                sessions_key = self._get_user_sessions_key(user_id)
                self.redis_client.sadd(sessions_key, session_id)
            else:
                # 使用内存存储
                if user_id not in self.memory_store:
                    self.memory_store[user_id] = {}
                self.memory_store[user_id][session_id] = session_data
            print(f"✅ 会话保存成功: user={user_id}, session={session_id}")
        except Exception as e:
            print(f"❌ 保存会话失败: {e}")

    def get_session(self, user_id: int, session_id: str) -> Optional[Dict[str, Any]]:
        """
        获取会话数据

        参数:
            user_id: 用户ID
            session_id: 会话ID

        返回:
            会话数据
        """
        try:
            key = self._get_key(user_id, session_id)
            if self.redis_client:
                data = self.redis_client.get(key)
                if data:
                    return json.loads(data)
            else:
                # 使用内存存储
                if user_id in self.memory_store and session_id in self.memory_store[user_id]:
                    return self.memory_store[user_id][session_id]
            return None
        except Exception as e:
            print(f"❌ 获取会话失败: {e}")
            return None

    def delete_session(self, user_id: int, session_id: str):
        """
        删除会话

        参数:
            user_id: 用户ID
            session_id: 会话ID
        """
        try:
            key = self._get_key(user_id, session_id)
            if self.redis_client:
                self.redis_client.delete(key)
                # 从用户会话列表中移除
                sessions_key = self._get_user_sessions_key(user_id)
                self.redis_client.srem(sessions_key, session_id)
            else:
                # 使用内存存储
                if user_id in self.memory_store and session_id in self.memory_store[user_id]:
                    del self.memory_store[user_id][session_id]
            print(f"✅ 会话删除成功: user={user_id}, session={session_id}")
        except Exception as e:
            print(f"❌ 删除会话失败: {e}")

    def list_user_sessions(self, user_id: int) -> List[str]:
        """
        列出用户的所有会话

        参数:
            user_id: 用户ID

        返回:
            会话ID列表
        """
        try:
            sessions_key = self._get_user_sessions_key(user_id)
            if self.redis_client:
                sessions = self.redis_client.smembers(sessions_key)
                return list(sessions)
            else:
                # 使用内存存储
                if user_id in self.memory_store:
                    return list(self.memory_store[user_id].keys())
                return []
        except Exception as e:
            print(f"❌ 列出会话失败: {e}")
            return []

    def get_all_user_sessions(self, user_id: int) -> Dict[str, Dict[str, Any]]:
        """
        获取用户的所有会话数据

        参数:
            user_id: 用户ID

        返回:
            会话ID到会话数据的映射
        """
        sessions = self.list_user_sessions(user_id)
        result = {}
        for session_id in sessions:
            session_data = self.get_session(user_id, session_id)
            if session_data:
                result[session_id] = session_data
        return result

    def update_session(self, user_id: int, session_id: str, updates: Dict[str, Any]):
        """
        更新会话数据

        参数:
            user_id: 用户ID
            session_id: 会话ID
            updates: 要更新的字段
        """
        try:
            session_data = self.get_session(user_id, session_id)
            if session_data:
                session_data.update(updates)
                session_data["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
                self.save_session(user_id, session_id, session_data)
                print(f"✅ 会话更新成功: user={user_id}, session={session_id}")
        except Exception as e:
            print(f"❌ 更新会话失败: {e}")

    def clear_user_sessions(self, user_id: int):
        """
        清空用户的所有会话

        参数:
            user_id: 用户ID
        """
        try:
            sessions = self.list_user_sessions(user_id)
            for session_id in sessions:
                self.delete_session(user_id, session_id)
            print(f"✅ 清空用户会话成功: user={user_id}")
        except Exception as e:
            print(f"❌ 清空用户会话失败: {e}")

    def exists(self, user_id: int, session_id: str) -> bool:
        """
        检查会话是否存在

        参数:
            user_id: 用户ID
            session_id: 会话ID

        返回:
            是否存在
        """
        try:
            key = self._get_key(user_id, session_id)
            if self.redis_client:
                return self.redis_client.exists(key)
            else:
                # 使用内存存储
                return user_id in self.memory_store and session_id in self.memory_store[user_id]
        except Exception as e:
            print(f"❌ 检查会话失败: {e}")
            return False

    def set_expiry(self, user_id: int, session_id: str, seconds: int):
        """
        设置会话过期时间

        参数:
            user_id: 用户ID
            session_id: 会话ID
            seconds: 过期时间（秒）
        """
        try:
            key = self._get_key(user_id, session_id)
            if self.redis_client:
                self.redis_client.expire(key, seconds)
                print(f"✅ 设置会话过期时间成功: user={user_id}, session={session_id}, expiry={seconds}s")
        except Exception as e:
            print(f"❌ 设置会话过期时间失败: {e}")


def test_redis_manager():
    """测试Redis管理器"""
    print("测试Redis管理器")
    print("=" * 60)

    manager = RedisManager()

    # 测试保存会话
    print("1. 测试保存会话...")
    session_data = {
        "id": "test_session_1",
        "title": "测试会话",
        "messages": [
            {"role": "user", "content": "你好", "timestamp": "2024-01-01 12:00:00"},
            {"role": "assistant", "content": "你好！", "timestamp": "2024-01-01 12:00:01"}
        ],
        "created_at": "2024-01-01 12:00:00",
        "updated_at": "2024-01-01 12:00:01"
    }
    manager.save_session(1, "test_session_1", session_data)

    # 测试获取会话
    print("\n2. 测试获取会话...")
    retrieved_session = manager.get_session(1, "test_session_1")
    print(f"   获取的会话: {retrieved_session}")

    # 测试列出用户会话
    print("\n3. 测试列出用户会话...")
    sessions = manager.list_user_sessions(1)
    print(f"   用户1的会话: {sessions}")

    # 测试更新会话
    print("\n4. 测试更新会话...")
    manager.update_session(1, "test_session_1", {"title": "更新后的测试会话"})
    updated_session = manager.get_session(1, "test_session_1")
    print(f"   更新后的会话标题: {updated_session.get('title')}")

    # 测试获取所有用户会话
    print("\n5. 测试获取所有用户会话...")
    all_sessions = manager.get_all_user_sessions(1)
    print(f"   用户1的所有会话: {len(all_sessions)} 个")

    # 测试删除会话
    print("\n6. 测试删除会话...")
    manager.delete_session(1, "test_session_1")
    deleted_session = manager.get_session(1, "test_session_1")
    print(f"   删除后会话是否存在: {deleted_session is not None}")

    # 测试清空用户会话
    print("\n7. 测试清空用户会话...")
    # 先创建一个新会话
    session_data2 = {
        "id": "test_session_2",
        "title": "测试会话2",
        "messages": [],
        "created_at": "2024-01-01 12:00:00",
        "updated_at": "2024-01-01 12:00:00"
    }
    manager.save_session(1, "test_session_2", session_data2)
    print(f"   清空前会话数: {len(manager.list_user_sessions(1))}")
    manager.clear_user_sessions(1)
    print(f"   清空后会话数: {len(manager.list_user_sessions(1))}")

    print("\n" + "=" * 60)
    print("✅ Redis管理器测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    test_redis_manager()
