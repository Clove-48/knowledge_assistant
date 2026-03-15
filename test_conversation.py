import sys
sys.path.append('.')

try:
    from conversation_manager import ConversationManager
    print('ConversationManager imported successfully')
    
    manager = ConversationManager()
    print('ConversationManager created successfully')
    
    # 测试创建会话
    test_user_id = 1
    session_id = manager.create_session(user_id=test_user_id, title="测试会话")
    print(f'Created session: {session_id}')
    
    # 测试添加消息
    message = manager.add_message(user_id=test_user_id, role="user", content="你好，这是测试消息")
    print(f'Added message: {message}')
    
    # 测试列出会话
    sessions = manager.list_sessions(user_id=test_user_id)
    print(f'Listed sessions: {len(sessions)}')
    
    print('All tests passed!')
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
