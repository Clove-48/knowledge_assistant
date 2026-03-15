#!/usr/bin/env python3
# test_login.py
# 登录功能测试脚本

import sys
import os
import time

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from user_authentication import UserAuthentication

def test_login():
    """测试登录功能"""
    print("=" * 80)
    print("🔐 登录功能测试")
    print("=" * 80)
    
    # 初始化认证系统
    auth = UserAuthentication()
    
    # 测试用例1: 测试注册
    print("\n1. 测试用户注册")
    test_username = f"test_user_{int(time.time())}"
    test_password = "Test@123456"
    test_email = f"{test_username}@example.com"
    
    register_result = auth.register(test_username, test_password, test_email)
    print(f"   注册结果: {register_result}")
    
    if not register_result["success"]:
        print("   ❌ 注册失败，测试终止")
        return False
    
    # 测试用例2: 测试正确密码登录
    print("\n2. 测试正确密码登录")
    login_result = auth.login(test_username, test_password)
    print(f"   登录结果: {login_result}")
    
    if not login_result["success"]:
        print("   ❌ 正确密码登录失败")
        return False
    
    # 测试用例3: 测试错误密码登录
    print("\n3. 测试错误密码登录")
    wrong_password_login_result = auth.login(test_username, "wrong_password")
    print(f"   登录结果: {wrong_password_login_result}")
    
    if wrong_password_login_result["success"]:
        print("   ❌ 错误密码登录成功，这是一个安全问题")
        return False
    
    # 测试用例4: 测试不存在的用户登录
    print("\n4. 测试不存在的用户登录")
    non_existent_user_login_result = auth.login("non_existent_user", "password123")
    print(f"   登录结果: {non_existent_user_login_result}")
    
    if non_existent_user_login_result["success"]:
        print("   ❌ 不存在的用户登录成功，这是一个安全问题")
        return False
    
    # 测试用例5: 测试token验证
    print("\n5. 测试token验证")
    token = login_result.get("token")
    if token:
        verify_result = auth.verify_token(token)
        print(f"   Token验证结果: {verify_result}")
        
        if not verify_result:
            print("   ❌ Token验证失败")
            return False
    else:
        print("   ❌ 未获取到token")
        return False
    
    # 测试用例6: 测试获取用户信息
    print("\n6. 测试获取用户信息")
    user_id = login_result.get("user_id")
    if user_id:
        user_info = auth.get_user_by_id(user_id)
        print(f"   用户信息: {user_info}")
        
        if not user_info:
            print("   ❌ 获取用户信息失败")
            return False
    else:
        print("   ❌ 未获取到user_id")
        return False
    
    print("\n" + "=" * 80)
    print("✅ 登录功能测试全部通过！")
    print("=" * 80)
    return True

if __name__ == "__main__":
    test_login()
