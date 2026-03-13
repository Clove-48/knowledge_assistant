# mysql_manager.py
# MySQL数据库管理器

import mysql.connector
import json
from typing import Optional, Dict, Any, List
import time
from datetime import datetime

from config import DATABASE_SETTINGS

class MySQLManager:
    """MySQL数据库管理器"""

    def __init__(self):
        """
        初始化MySQL管理器
        从config.py中读取MySQL配置
        """
        # 存储MySQL配置
        self.host = DATABASE_SETTINGS.get("mysql_host", "localhost")
        self.port = DATABASE_SETTINGS.get("mysql_port", 3306)
        self.user = DATABASE_SETTINGS.get("mysql_user", "root")
        self.password = DATABASE_SETTINGS.get("mysql_password", "")
        self.database = DATABASE_SETTINGS.get("mysql_db", "ai_assistant")
        
        # 内存存储作为后备
        self.memory_store = {
            "users": {},
            "sessions": {}
        }
        
        # 尝试连接
        self._connect()
    
    def _connect(self):
        """
        测试MySQL数据库连接
        """
        try:
            # 测试连接
            connection = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                pool_name="mysql_pool",
                pool_size=10,
                autocommit=True
            )
            connection.close()
            # 初始化表结构
            self._init_tables()
            print("✅ MySQL连接成功")
            return True
        except Exception as e:
            print(f"❌ MySQL连接失败: {e}")
            # 使用内存存储作为后备
            print("⚠️  使用内存存储作为后备")
            return False
    
    def _check_connection(self):
        """
        检查MySQL连接是否有效
        """
        try:
            # 测试连接
            connection = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                pool_name="mysql_pool",
                pool_size=10,
                autocommit=True
            )
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            connection.close()
            return True
        except:
            # 连接失效
            print("⚠️ MySQL连接失效")
            return False
    
    def get_connection(self):
        """
        获取数据库连接
        使用上下文管理器确保连接正确释放
        """
        class ConnectionContext:
            def __init__(self, manager):
                self.manager = manager
                self.connection = None
                self.cursor = None
            
            def __enter__(self):
                try:
                    # 从连接池获取新连接
                    self.connection = mysql.connector.connect(
                        host=self.manager.host,
                        port=self.manager.port,
                        user=self.manager.user,
                        password=self.manager.password,
                        database=self.manager.database,
                        pool_name="mysql_pool",
                        pool_size=10,
                        autocommit=True
                    )
                    self.cursor = self.connection.cursor(dictionary=True)
                    return self.connection, self.cursor
                except Exception as e:
                    print(f"❌ 获取连接失败: {e}")
                    # 即使失败也返回一个有效的上下文
                    return None, None
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                # 释放连接回连接池
                if self.cursor:
                    try:
                        self.cursor.close()
                    except:
                        pass
                if self.connection:
                    try:
                        self.connection.close()
                    except:
                        pass
        
        return ConnectionContext(self)

    def _init_tables(self):
        """初始化数据库表"""
        with self.get_connection() as (conn, cursor):
            if conn and cursor:
                try:
                    # 创建用户表
                    cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        username VARCHAR(255) UNIQUE NOT NULL,
                        password_hash VARCHAR(255) NOT NULL,
                        email VARCHAR(255) UNIQUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    ''')

                    # 创建会话表
                    cursor.execute('''
                    CREATE TABLE IF NOT EXISTS sessions (
                        id VARCHAR(255) PRIMARY KEY,
                        user_id INT NOT NULL,
                        title VARCHAR(255) NOT NULL,
                        messages TEXT NOT NULL,
                        created_at DATETIME NOT NULL,
                        updated_at DATETIME NOT NULL,
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    )
                    ''')

                    # 创建登录日志表（用于监控）
                    cursor.execute('''
                    CREATE TABLE IF NOT EXISTS login_logs (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        user_id INT,
                        username VARCHAR(255),
                        success BOOLEAN NOT NULL,
                        message VARCHAR(255),
                        response_time FLOAT,
                        ip_address VARCHAR(50),
                        user_agent VARCHAR(255),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    ''')

                    conn.commit()
                except Exception as e:
                    print(f"❌ 初始化表失败: {e}")

    # 用户相关操作
    def create_user(self, username: str, password_hash: str, email: Optional[str] = None) -> int:
        """创建用户"""
        # 确保邮箱唯一性：如果email为None或空字符串，生成一个基于用户名的唯一邮箱
        if not email:
            email = f"{username}@example.com"
        
        # 先保存到内存存储，确保数据不丢失
        user_id = len(self.memory_store["users"]) + 1
        self.memory_store["users"][user_id] = {
            "id": user_id,
            "username": username,
            "password_hash": password_hash,
            "email": email,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # 使用上下文管理器获取连接
        with self.get_connection() as (conn, cursor):
            if conn and cursor:
                try:
                    cursor.execute(
                        "INSERT INTO users (username, password_hash, email) VALUES (%s, %s, %s)",
                        (username, password_hash, email)
                    )
                    return cursor.lastrowid
                except Exception as e:
                    print(f"❌ 创建用户失败: {e}")
        
        # 失败后使用内存存储
        return user_id

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """根据用户名获取用户"""
        # 先从内存存储获取，确保快速响应
        for user in self.memory_store["users"].values():
            if user["username"] == username:
                return user
        
        # 使用上下文管理器获取连接
        with self.get_connection() as (conn, cursor):
            if conn and cursor:
                try:
                    cursor.execute(
                        "SELECT id, username, password_hash, email, created_at FROM users WHERE username = %s",
                        (username,)
                    )
                    result = cursor.fetchone()
                    if result:
                        # 更新内存存储
                        self.memory_store["users"][result["id"]] = result
                        return result
                except Exception as e:
                    print(f"❌ 获取用户失败: {e}")
        
        # 失败后使用内存存储
        for user in self.memory_store["users"].values():
            if user["username"] == username:
                return user
        return None

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取用户"""
        # 先从内存存储获取，确保快速响应
        if user_id in self.memory_store["users"]:
            return self.memory_store["users"][user_id]
        
        # 使用上下文管理器获取连接
        with self.get_connection() as (conn, cursor):
            if conn and cursor:
                try:
                    cursor.execute(
                        "SELECT id, username, password_hash, email, created_at FROM users WHERE id = %s",
                        (user_id,)
                    )
                    result = cursor.fetchone()
                    if result:
                        # 更新内存存储
                        self.memory_store["users"][result["id"]] = result
                        return result
                except Exception as e:
                    print(f"❌ 获取用户失败: {e}")
        
        # 失败后使用内存存储
        return self.memory_store["users"].get(user_id)

    # 会话相关操作
    def save_session(self, user_id: int, session_id: str, session_data: Dict[str, Any]):
        """保存会话"""
        # 确保时间戳是字符串格式
        created_at = session_data.get("created_at", "")
        updated_at = session_data.get("updated_at", "")
        
        # 先保存到内存存储，确保数据不丢失
        if user_id not in self.memory_store["sessions"]:
            self.memory_store["sessions"][user_id] = {}
        self.memory_store["sessions"][user_id][session_id] = session_data
        
        # 使用上下文管理器获取连接
        with self.get_connection() as (conn, cursor):
            if conn and cursor:
                try:
                    messages_json = json.dumps(session_data["messages"])
                    cursor.execute(
                        "INSERT INTO sessions (id, user_id, title, messages, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE title = %s, messages = %s, updated_at = %s",
                        (
                            session_id, user_id, session_data["title"], messages_json, 
                            created_at, updated_at,
                            session_data["title"], messages_json, updated_at
                        )
                    )
                except Exception as e:
                    print(f"❌ 保存会话失败: {e}")

    def get_session(self, user_id: int, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话"""
        # 先从内存存储获取，确保快速响应
        if user_id in self.memory_store["sessions"]:
            memory_session = self.memory_store["sessions"][user_id].get(session_id)
            if memory_session:
                return memory_session
        
        # 使用上下文管理器获取连接
        with self.get_connection() as (conn, cursor):
            if conn and cursor:
                try:
                    cursor.execute(
                        "SELECT id, user_id, title, messages, created_at, updated_at FROM sessions WHERE id = %s AND user_id = %s",
                        (session_id, user_id)
                    )
                    session = cursor.fetchone()
                    if session:
                        session["messages"] = json.loads(session["messages"])
                        # 确保时间戳是字符串格式
                        if isinstance(session.get("created_at"), datetime):
                            session["created_at"] = session["created_at"].isoformat()
                        if isinstance(session.get("updated_at"), datetime):
                            session["updated_at"] = session["updated_at"].isoformat()
                        # 更新内存存储
                        if user_id not in self.memory_store["sessions"]:
                            self.memory_store["sessions"][user_id] = {}
                        self.memory_store["sessions"][user_id][session_id] = session
                    return session
                except Exception as e:
                    print(f"❌ 获取会话失败: {e}")
        
        # 失败后使用内存存储
        if user_id in self.memory_store["sessions"]:
            return self.memory_store["sessions"][user_id].get(session_id)
        return None

    def list_user_sessions(self, user_id: int) -> List[Dict[str, Any]]:
        """列出用户的所有会话"""
        # 先从内存存储获取，确保快速响应
        memory_sessions = []
        if user_id in self.memory_store["sessions"]:
            memory_sessions = list(self.memory_store["sessions"][user_id].values())
        
        # 使用上下文管理器获取连接
        with self.get_connection() as (conn, cursor):
            if conn and cursor:
                try:
                    cursor.execute(
                        "SELECT id, user_id, title, messages, created_at, updated_at FROM sessions WHERE user_id = %s ORDER BY updated_at DESC",
                        (user_id,)
                    )
                    sessions = cursor.fetchall()
                    for session in sessions:
                        session["messages"] = json.loads(session["messages"])
                        # 确保时间戳是字符串格式
                        if isinstance(session.get("created_at"), datetime):
                            session["created_at"] = session["created_at"].isoformat()
                        if isinstance(session.get("updated_at"), datetime):
                            session["updated_at"] = session["updated_at"].isoformat()
                        # 更新内存存储
                        if user_id not in self.memory_store["sessions"]:
                            self.memory_store["sessions"][user_id] = {}
                        self.memory_store["sessions"][user_id][session["id"]] = session
                    return sessions
                except Exception as e:
                    print(f"❌ 列出会话失败: {e}")
        
        # 失败后使用内存存储
        if user_id in self.memory_store["sessions"]:
            return list(self.memory_store["sessions"][user_id].values())
        return []

    def delete_session(self, user_id: int, session_id: str):
        """删除会话"""
        # 先从内存存储删除，确保数据一致性
        if user_id in self.memory_store["sessions"] and session_id in self.memory_store["sessions"][user_id]:
            del self.memory_store["sessions"][user_id][session_id]
        
        # 使用上下文管理器获取连接
        with self.get_connection() as (conn, cursor):
            if conn and cursor:
                try:
                    cursor.execute(
                        "DELETE FROM sessions WHERE id = %s AND user_id = %s",
                        (session_id, user_id)
                    )
                except Exception as e:
                    print(f"❌ 删除会话失败: {e}")

    # 登录日志相关操作
    def log_login_attempt(self, user_id: Optional[int], username: str, success: bool, message: str, response_time: float, ip_address: str = "", user_agent: str = ""):
        """记录登录尝试"""
        # 使用上下文管理器获取连接
        with self.get_connection() as (conn, cursor):
            if conn and cursor:
                try:
                    cursor.execute(
                        "INSERT INTO login_logs (user_id, username, success, message, response_time, ip_address, user_agent) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                        (user_id, username, success, message, response_time, ip_address, user_agent)
                    )
                except Exception as e:
                    print(f"❌ 记录登录日志失败: {e}")

    def get_login_stats(self, days: int = 7) -> Dict[str, Any]:
        """获取登录统计信息"""
        with self.get_connection() as (conn, cursor):
            if not conn or not cursor:
                return {"total_attempts": 0, "success_rate": 0, "avg_response_time": 0, "p95_response_time": 0, "p99_response_time": 0}

            try:
                # 获取总尝试次数
                cursor.execute(
                    "SELECT COUNT(*) as total FROM login_logs WHERE created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)",
                    (days,)
                )
                total = cursor.fetchone()["total"]

                # 获取成功次数
                cursor.execute(
                    "SELECT COUNT(*) as success FROM login_logs WHERE success = TRUE AND created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)",
                    (days,)
                )
                success = cursor.fetchone()["success"]

                # 获取平均响应时间
                cursor.execute(
                    "SELECT AVG(response_time) as avg_time FROM login_logs WHERE created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)",
                    (days,)
                )
                avg_time = cursor.fetchone()["avg_time"] or 0

                # 获取P95和P99响应时间
                cursor.execute(
                    "SELECT response_time FROM login_logs WHERE created_at >= DATE_SUB(NOW(), INTERVAL %s DAY) ORDER BY response_time ASC",
                    (days,)
                )
                times = [row["response_time"] for row in cursor.fetchall()]
                p95 = times[int(len(times) * 0.95)] if times else 0
                p99 = times[int(len(times) * 0.99)] if times else 0

                return {
                    "total_attempts": total,
                    "success_count": success,
                    "success_rate": (success / total * 100) if total > 0 else 0,
                    "avg_response_time": avg_time,
                    "p95_response_time": p95,
                    "p99_response_time": p99
                }
            except Exception as e:
                print(f"❌ 获取登录统计失败: {e}")
                return {"total_attempts": 0, "success_rate": 0, "avg_response_time": 0, "p95_response_time": 0, "p99_response_time": 0}

    def close(self):
        """关闭数据库连接"""
        # 连接池会自动管理连接，不需要手动关闭
        print("✅ MySQL连接池已清理")


def test_mysql_manager():
    """测试MySQL管理器"""
    print("测试MySQL管理器")
    print("=" * 60)

    manager = MySQLManager()

    # 测试用户操作
    print("1. 测试创建用户...")
    user_id = manager.create_user("testuser", "password_hash", "test@example.com")
    print(f"   创建用户ID: {user_id}")

    print("2. 测试获取用户...")
    user = manager.get_user_by_username("testuser")
    print(f"   获取用户: {user}")

    # 测试会话操作
    print("3. 测试保存会话...")
    session_data = {
        "id": "test_session_1",
        "user_id": user_id,
        "title": "测试会话",
        "messages": [{"role": "user", "content": "你好"}],
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    manager.save_session(user_id, "test_session_1", session_data)

    print("4. 测试获取会话...")
    session = manager.get_session(user_id, "test_session_1")
    print(f"   获取会话: {session}")

    print("5. 测试列出会话...")
    sessions = manager.list_user_sessions(user_id)
    print(f"   会话列表: {len(sessions)} 个")

    # 测试登录日志
    print("6. 测试记录登录尝试...")
    manager.log_login_attempt(user_id, "testuser", True, "登录成功", 0.5, "127.0.0.1", "Mozilla/5.0")

    print("7. 测试获取登录统计...")
    stats = manager.get_login_stats()
    print(f"   登录统计: {stats}")

    # 测试删除会话
    print("8. 测试删除会话...")
    manager.delete_session(user_id, "test_session_1")

    print("9. 测试列出会话（删除后）...")
    sessions_after = manager.list_user_sessions(user_id)
    print(f"   会话列表: {len(sessions_after)} 个")

    manager.close()

    print("\n" + "=" * 60)
    print("✅ MySQL管理器测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    test_mysql_manager()
