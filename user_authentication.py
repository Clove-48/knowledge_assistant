# user_authentication.py
# 用户认证系统

import hashlib
import os
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from mysql_manager import MySQLManager

class UserAuthentication:
    """用户认证系统"""

    def __init__(self):
        """
        初始化用户认证系统
        """
        self.mysql_manager = MySQLManager()
        self.secret_key = os.urandom(24)  # 用于JWT签名的密钥


    def _hash_password(self, password: str) -> str:
        """哈希密码"""
        return hashlib.sha256(password.encode()).hexdigest()

    def register(self, username: str, password: str, email: Optional[str] = None) -> Dict[str, Any]:
        """
        用户注册

        参数:
            username: 用户名
            password: 密码
            email: 邮箱

        返回:
            注册结果
        """
        try:
            # 检查密码长度
            min_length = 6
            max_length = 20
            if len(password) < min_length:
                return {"success": False, "message": f"密码长度不能少于{min_length}个字符"}
            if len(password) > max_length:
                return {"success": False, "message": f"密码长度不能超过{max_length}个字符"}

            # 检查用户名是否已存在
            existing_user = self.mysql_manager.get_user_by_username(username)
            if existing_user:
                return {"success": False, "message": "用户名已存在"}

            # 插入新用户
            password_hash = self._hash_password(password)
            user_id = self.mysql_manager.create_user(username, password_hash, email)

            if user_id == -1:
                return {"success": False, "message": "注册失败: 数据库错误"}

            return {
                "success": True,
                "message": "注册成功",
                "user_id": user_id,
                "username": username
            }
        except Exception as e:
            return {"success": False, "message": f"注册失败: {str(e)}"}

    def login(self, username: str, password: str, ip_address: str = "", user_agent: str = "") -> Dict[str, Any]:
        """
        用户登录

        参数:
            username: 用户名
            password: 密码
            ip_address: IP地址（用于日志）
            user_agent: 用户代理（用于日志）

        返回:
            登录结果，包含token
        """
        import time
        start_time = time.time()
        
        try:
            # 查找用户
            user = self.mysql_manager.get_user_by_username(username)

            if not user:
                response_time = time.time() - start_time
                self.mysql_manager.log_login_attempt(None, username, False, "用户名或密码错误", response_time, ip_address, user_agent)
                return {"success": False, "message": "用户名或密码错误"}

            user_id, username, stored_hash = user["id"], user["username"], user["password_hash"]

            # 验证密码
            if self._hash_password(password) != stored_hash:
                response_time = time.time() - start_time
                self.mysql_manager.log_login_attempt(user_id, username, False, "用户名或密码错误", response_time, ip_address, user_agent)
                return {"success": False, "message": "用户名或密码错误"}

            # 生成JWT token
            token = self._generate_token(user_id, username)

            response_time = time.time() - start_time
            self.mysql_manager.log_login_attempt(user_id, username, True, "登录成功", response_time, ip_address, user_agent)

            return {
                "success": True,
                "message": "登录成功",
                "user_id": user_id,
                "username": username,
                "token": token
            }
        except Exception as e:
            response_time = time.time() - start_time
            self.mysql_manager.log_login_attempt(None, username, False, f"登录失败: {str(e)}", response_time, ip_address, user_agent)
            return {"success": False, "message": f"登录失败: {str(e)}"}

    def _generate_token(self, user_id: int, username: str) -> str:
        """
        生成JWT token

        参数:
            user_id: 用户ID
            username: 用户名

        返回:
            JWT token
        """
        payload = {
            "user_id": user_id,
            "username": username,
            "exp": datetime.utcnow() + timedelta(days=7)  # 7天过期
        }
        return jwt.encode(payload, self.secret_key, algorithm="HS256")

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        验证JWT token

        参数:
            token: JWT token

        返回:
            解码后的payload，验证失败返回None
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            return payload
        except:
            return None

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        根据用户ID获取用户信息

        参数:
            user_id: 用户ID

        返回:
            用户信息
        """
        try:
            user = self.mysql_manager.get_user_by_id(user_id)
            if user:
                return {
                    "id": user["id"],
                    "username": user["username"],
                    "email": user["email"],
                    "created_at": user["created_at"]
                }
            return None
        except:
            return None

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        根据用户名获取用户信息

        参数:
            username: 用户名

        返回:
            用户信息
        """
        try:
            user = self.mysql_manager.get_user_by_username(username)
            if user:
                return {
                    "id": user["id"],
                    "username": user["username"],
                    "email": user["email"],
                    "created_at": user["created_at"]
                }
            return None
        except:
            return None

    def update_user(self, user_id: int, **kwargs) -> bool:
        """
        更新用户信息

        参数:
            user_id: 用户ID
            **kwargs: 要更新的字段

        返回:
            是否更新成功
        """
        # 注意：MySQL管理器暂不支持更新用户信息，这里返回False
        return False

    def delete_user(self, user_id: int) -> bool:
        """
        删除用户

        参数:
            user_id: 用户ID

        返回:
            是否删除成功
        """
        # 注意：MySQL管理器暂不支持删除用户，这里返回False
        return False

    def list_users(self) -> list:
        """
        列出所有用户

        返回:
            用户列表
        """
        # 注意：MySQL管理器暂不支持列出所有用户，这里返回空列表
        return []

    def get_login_stats(self, days: int = 7) -> Dict[str, Any]:
        """
        获取登录统计信息

        参数:
            days: 统计天数

        返回:
            登录统计信息
        """
        return self.mysql_manager.get_login_stats(days)


def test_user_authentication():
    """测试用户认证系统"""
    print("测试用户认证系统")
    print("=" * 60)

    auth = UserAuthentication("test_users.db")

    # 测试注册
    print("1. 测试用户注册...")
    register_result = auth.register("testuser", "password123", "test@example.com")
    print(f"   注册结果: {register_result}")

    # 测试登录
    print("\n2. 测试用户登录...")
    login_result = auth.login("testuser", "password123")
    print(f"   登录结果: {login_result}")

    if login_result["success"]:
        token = login_result["token"]

        # 测试验证token
        print("\n3. 测试验证token...")
        payload = auth.verify_token(token)
        print(f"   Token验证结果: {payload}")

        # 测试获取用户信息
        print("\n4. 测试获取用户信息...")
        user_info = auth.get_user_by_id(payload["user_id"])
        print(f"   用户信息: {user_info}")

        # 测试更新用户
        print("\n5. 测试更新用户...")
        update_result = auth.update_user(payload["user_id"], email="newemail@example.com")
        print(f"   更新结果: {update_result}")

        # 测试列出所有用户
        print("\n6. 测试列出所有用户...")
        users = auth.list_users()
        print(f"   用户列表: {users}")

        # 测试删除用户
        print("\n7. 测试删除用户...")
        delete_result = auth.delete_user(payload["user_id"])
        print(f"   删除结果: {delete_result}")

    print("\n" + "=" * 60)
    print("✅ 用户认证系统测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    test_user_authentication()
