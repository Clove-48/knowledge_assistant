# streamlit_full_ui.py
# 完整的Streamlit Web界面

import streamlit as st
import sys
import os
import json
import time
from datetime import datetime

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入必要的模块
try:
    from conversation_manager import ConversationManager
    from tool_integration import ToolIntegration
    from vector_store_manager import VectorStoreManager
    from document_processor import DocumentProcessor
    from user_authentication import UserAuthentication
    from config import DEEPSEEK_API_KEY, MODEL_SETTINGS

    print("✅ 导入模块成功")
except ImportError as e:
    print(f"❌ 导入模块失败: {e}")
    sys.exit(1)

# 全局AI助手实例
aassistant = None

class CompleteAIAssistant:
    """完全修复版AI助手"""

    def __init__(self, persist_conversations: bool = True):
        print("初始化完全修复版AI助手...")

        # 检查API密钥
        if not DEEPSEEK_API_KEY or DEEPSEEK_API_KEY == "您的DeepSeek-API-KEY-在这里":
            print("⚠️  警告: 未设置DeepSeek API密钥")
            print("   请在 config.py 中设置您的 API 密钥")

        # 延迟初始化组件，只在需要时创建
        self.vector_manager = None
        self.tool_integration = None
        self.document_processor = None
        self.user_auth = UserAuthentication()  # 认证组件需要立即初始化

        # 初始化对话管理器
        persist_file = "complete_conversations.json" if persist_conversations else None
        self.conversation_manager = ConversationManager(
            max_history=10,
            persist_file=persist_file
        )

        # API配置
        self.api_key = DEEPSEEK_API_KEY
        self.api_url = "https://api.deepseek.com/v1/chat/completions"

        print("✅ 完全修复版AI助手初始化完成")

    def chat(self, user_id: int, message: str, use_tools: bool = True, use_rag: bool = True, session_id: str = None) -> dict:
        """聊天接口"""
        if not message.strip():
            return {
                "success": False,
                "answer": "消息不能为空",
                "tools_used": [],
                "sources_used": []
            }

        start_time = time.time()
        print(f"\n⏱️ 开始处理消息: {message}")
        print(f"用户ID: {user_id}, 当前会话ID: {self.conversation_manager.current_session_id}")

        response = {
            "session_id": self.conversation_manager.current_session_id,
            "user_message": message,
            "assistant_response": "",
            "tools_used": [],
            "sources_used": [],
            "success": False
        }

        try:
            # 1. 构建上下文
            context = ""
            sources_used = []

            if use_rag:
                try:
                    # 延迟初始化vector_manager
                    if self.vector_manager is None:
                        self.vector_manager = VectorStoreManager()
                    
                    rag_start = time.time()
                    # 从向量数据库检索
                    results = self.vector_manager.similarity_search(message, k=3)
                    rag_end = time.time()
                    print(f"⏱️ 向量检索耗时: {rag_end - rag_start:.2f}秒")

                    if results:
                        context = "参考信息：\n"
                        for i, doc in enumerate(results, 1):
                            context += f"{i}. {doc.page_content[:200]}...\n"

                        # 记录源文档
                        for doc in results:
                            sources_used.append({
                                "source": doc.metadata.get("source", "未知"),
                                "page": doc.metadata.get("page", 0),
                                "content_preview": doc.page_content[:100] + "..."
                            })
                except Exception as e:
                    print(f"⚠️ 向量检索失败: {e}")
                    context = ""

            # 2. 获取最近的对话历史（在添加新消息之前）
            target_session_id = session_id or self.conversation_manager.current_session_id
            print(f"获取用户 {user_id} 会话 {target_session_id} 的历史")
            chat_history = self.conversation_manager.get_recent_history(
                user_id=user_id,
                session_id=target_session_id,
                last_n=3
            )
            print(f"历史对话: {chat_history}")

            # 3. 添加用户消息到对话历史 - 使用指定的会话ID
            self.conversation_manager.add_message(user_id, "user", message, session_id=session_id)

            # 4. 检查是否是时间查询
            if use_tools and self._is_time_query(message):
                time_result = self._get_current_time()
                response = {
                    "success": True,
                    "assistant_response": time_result,
                    "tools_used": [{"tool": "time_query", "result": time_result}],
                    "sources_used": []
                }
                # 添加到对话历史
                self.conversation_manager.add_message(user_id, "assistant", time_result, session_id=session_id, metadata={"type": "tool"})
                end_time = time.time()
                print(f"⏱️ 时间查询处理完成，耗时: {end_time - start_time:.2f}秒")
                return response

            # 5. 检查是否应使用工具
            if use_tools:
                # 延迟初始化tool_integration
                if self.tool_integration is None:
                    self.tool_integration = ToolIntegration()
                
                tool_suggestion = self.tool_integration.auto_detect_tool(message)
                if tool_suggestion and tool_suggestion["confidence"] > 0.7:
                    tool_result = self.tool_integration.execute_tool(
                        tool_suggestion["tool_id"],
                        **tool_suggestion["parameters"]
                    )

                    if tool_result["success"]:
                        tool_response = f"我使用了 {tool_result['tool']} 工具：\n"
                        if "formatted" in tool_result["result"]:
                            tool_response += f"结果：{tool_result['result']['formatted']}"
                        else:
                            tool_response += f"结果：{json.dumps(tool_result['result'], ensure_ascii=False)}"

                        response["assistant_response"] = tool_response
                        response["tools_used"] = [{
                            "tool": tool_result["tool"],
                            "result": tool_result["result"]
                        }]
                        response["success"] = True

                        # 添加到对话历史
                        self.conversation_manager.add_message(user_id, "assistant", tool_response,
                                                              session_id=session_id, metadata={"type": "tool"})

                        end_time = time.time()
                        print(f"⏱️ 工具调用完成，耗时: {end_time - start_time:.2f}秒")
                        return response

            # 6. 调用DeepSeek API
            api_start = time.time()
            
            # 检查文档是否相关
            is_document_relevant = False
            if use_rag and sources_used:
                # 简单判断：检查用户问题中的关键词是否在参考文档中出现
                # 提取用户问题的关键词
                user_keywords = set(message.lower().split())
                # 检查是否有任何关键词在参考文档中出现
                for source in sources_used:
                    if source.get('content_preview'):
                        preview_lower = source['content_preview'].lower()
                        for keyword in user_keywords:
                            if keyword in preview_lower:
                                is_document_relevant = True
                                break
                    if is_document_relevant:
                        break
                # 如果没有检测到相关性，或者用户问题太短，使用通用模式
                if not is_document_relevant or len(user_keywords) < 2:
                    is_document_relevant = False
            
            # 根据文档相关性选择不同的调用模式
            if is_document_relevant:
                # 文档相关，使用RAG模式
                answer = self._call_deepseek_api(message, context, chat_history)
            else:
                # 文档不相关，使用通用模式
                answer = self._call_deepseek_api(message, "", chat_history, use_general_mode=True)
            
            api_end = time.time()
            print(f"⏱️ API调用耗时: {api_end - api_start:.2f}秒")

            if answer:
                response["assistant_response"] = answer
                response["sources_used"] = sources_used if is_document_relevant else []
                response["success"] = True

                # 添加到对话历史
                self.conversation_manager.add_message(user_id, "assistant", answer,
                                                      session_id=session_id, metadata={"type": "rag" if is_document_relevant else "general"})
            else:
                response["assistant_response"] = "抱歉，我无法回答这个问题。"
                response["success"] = False

        except Exception as e:
            error_msg = f"处理消息时出错: {str(e)[:100]}"
            print(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()

            response["assistant_response"] = f"抱歉，处理您的消息时出现错误: {str(e)[:100]}..."
            response["success"] = False

        end_time = time.time()
        print(f"⏱️ 总处理时间: {end_time - start_time:.2f}秒")
        print(f"✅ 回答生成完成")

        return response

    def _is_time_query(self, message: str) -> bool:
        """检查是否是时间查询"""
        time_keywords = [
            "现在几点", "现在几点了", "现在几点钟",
            "什么时间", "什么时间了", "当前时间", "当前时间是什么",
            "现在时间", "现在的时间", "现在的时间是", "现在时间是多少",
            "今天是", "今天日期", "现在日期", "当前日期",
            "几月几号", "几月几日", "几号了", "几号", "什么日子",
            "星期几", "今天星期", "今天周几", "周几了",
            "现在是什么时候", "现在什么时候", "什么时候了"
        ]

        message_strip = message.strip()
        for keyword in time_keywords:
            if keyword in message_strip:
                return True
        return False

    def _get_current_time(self) -> str:
        """获取当前时间"""
        now = datetime.now()
        time_str = now.strftime("%Y年%m月%d日 %H时%M分%S秒")
        weekday_map = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        weekday = weekday_map[now.weekday()]

        return f"当前时间：{time_str} {weekday}"

    def _call_deepseek_api(self, message: str, context: str = "", chat_history: str = "", use_general_mode: bool = False) -> str:
        """
        调用DeepSeek API
        """
        if not self.api_key or self.api_key == "您的DeepSeek-API-KEY-在这里":
            return "API密钥未设置，请在 config.py 中设置您的 DeepSeek API 密钥"

        # 构建消息数组
        messages = []
        
        # 添加系统消息
        if use_general_mode:
            # 通用模式
            system_message = f"你是一个智能AI助手，能够回答各种问题。请根据你的知识提供准确、有用的回答。"
        else:
            # RAG模式
            system_message = f"你是一个独立的AI知识库智能体，专门用于回答用户关于知识库的问题。"
            if context:
                system_message += f"\n\n参考信息：\n{context}"
        messages.append({"role": "system", "content": system_message})
        
        # 添加历史对话（如果有）
        if chat_history:
            # 解析历史对话，转换为消息格式
            history_lines = chat_history.strip().split('\n')
            for line in history_lines:
                line = line.strip()
                if line.startswith('用户: '):
                    messages.append({"role": "user", "content": line[4:]})
                elif line.startswith('助手: '):
                    messages.append({"role": "assistant", "content": line[4:]})
        
        # 添加当前用户问题
        messages.append({"role": "user", "content": message})

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "deepseek-chat",
            "messages": messages,
            "max_tokens": 1000,
            "temperature": 0.1,
            "stream": False
        }
        
        # 打印发送的消息，用于调试
        print(f"发送到API的消息: {json.dumps(messages, ensure_ascii=False, indent=2)}")

        try:
            import requests

            response = requests.post(
                self.api_url,
                headers=headers,
                json=data,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    return result["choices"][0]["message"]["content"]
                else:
                    return "API返回格式异常"
            elif response.status_code == 401:
                return "API认证失败，请检查API密钥"
            elif response.status_code == 429:
                return "请求频率超限，请稍后再试"
            else:
                return f"API错误 ({response.status_code}): {response.text[:100]}"

        except requests.exceptions.Timeout:
            return "请求超时，请检查网络连接"
        except requests.exceptions.ConnectionError:
            return "网络连接错误，请检查您的网络连接"
        except Exception as e:
            print(f"API调用异常: {e}")
            return f"API调用异常: {str(e)[:100]}"

    def get_conversation_history(self, user_id: int, session_id: str = None) -> list:
        """获取对话历史"""
        # 确保传递正确的会话ID，优先使用传入的session_id，否则使用当前会话
        return self.conversation_manager.get_conversation_history(user_id, session_id)

    def clear_conversation(self, user_id: int, session_id: str = None):
        """清空对话"""
        if session_id is None:
            session_id = self.conversation_manager.current_session_id
        self.conversation_manager.clear_conversation(user_id, session_id)
        print(f"✅ 已清空用户 {user_id} 的会话: {session_id}")

    def list_sessions(self, user_id: int) -> list:
        """列出所有会话"""
        return self.conversation_manager.list_sessions(user_id)

    def get_session_info(self, user_id: int) -> dict:
        """获取当前会话信息"""
        try:
            sessions = self.list_sessions(user_id)
            for session in sessions:
                if session.get("is_current"):
                    return {
                        "id": session.get("id", ""),
                        "title": session.get("title", "新对话"),
                        "message_count": session.get("message_count", 0)
                    }
        except:
            pass

        return {"id": "", "title": "新对话", "message_count": 0}

    def switch_session(self, user_id: int, session_data) -> bool:
        """切换会话"""
        try:
            if not session_data:
                return False

            session_id = str(session_data)

            # 直接使用 conversation_manager 的 switch_session 方法
            # 确保会话切换正确更新当前会话ID
            result = self.conversation_manager.switch_session(user_id, session_id)
            if result:
                print(f"✅ 已切换到会话: {session_id}")
                print(f"当前会话ID: {self.conversation_manager.current_session_id}")
            else:
                print(f"❌ 会话不存在: {session_id}")
            return result
        except Exception as e:
            print(f"切换会话失败: {e}")
            return False

    def set_session_title(self, user_id: int, title: str, session_id: str = None) -> bool:
        """设置会话标题"""
        try:
            self.conversation_manager.set_session_title(user_id, title, session_id)
            return True
        except:
            return False

    def create_new_session(self, user_id: int) -> dict:
        """创建新会话"""
        try:
            # 获取当前会话数量，用于生成新会话标题
            current_sessions = self.list_sessions(user_id)
            session_count = len(current_sessions) + 1
            
            # 创建新会话
            new_session_id = self.conversation_manager.create_session(user_id)
            if new_session_id:
                new_title = f"新对话 {session_count}"
                self.set_session_title(user_id, new_title, new_session_id)

                # 确保会话管理器中的当前会话ID正确更新
                self.conversation_manager.current_session_id = new_session_id
                self.conversation_manager.current_user_id = user_id
                
                # 确保新会话的消息数组是空的
                if user_id in self.conversation_manager.conversations:
                    if new_session_id in self.conversation_manager.conversations[user_id]:
                        self.conversation_manager.conversations[user_id][new_session_id]["messages"] = []
                        print(f"✅ 新会话消息状态已重置")
                
                # 构建新会话的详细信息
                new_session = {
                    "id": new_session_id,
                    "title": new_title,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "message_count": 0,
                    "is_current": True
                }
                
                print(f"✅ 创建新会话成功: ID={new_session_id}, 标题='{new_title}'")
                return new_session
        except Exception as e:
            print(f"❌ 创建新对话失败: {e}")

        return {}

    def get_vector_db_stats(self) -> dict:
        """获取向量数据库统计信息"""
        try:
            # 延迟初始化vector_manager
            if self.vector_manager is None:
                self.vector_manager = VectorStoreManager()
            info = self.vector_manager.get_collection_info()
            return {
                "document_count": info.get("document_count", 0),
                "collection_name": info.get("collection_name", "未知"),
                "embedding_model": info.get("embedding_model", "未知")
            }
        except:
            return {"document_count": 0, "collection_name": "未知", "embedding_model": "未知"}

    def process_uploaded_file(self, file) -> dict:
        """处理上传的文件并添加到向量数据库"""
        try:
            print(f"处理上传的文件: {file.name}")

            temp_dir = "temp_uploads"
            os.makedirs(temp_dir, exist_ok=True)
            file_path = os.path.join(temp_dir, file.name)

            with open(file_path, "wb") as f:
                f.write(file.getvalue())

            print(f"文件保存到: {file_path}")

            # 延迟初始化document_processor
            if self.document_processor is None:
                self.document_processor = DocumentProcessor()
            
            # 延迟初始化vector_manager
            if self.vector_manager is None:
                self.vector_manager = VectorStoreManager()
            
            documents = self.document_processor.load_document(file_path)
            chunks = self.document_processor.split_documents(documents)

            if chunks:
                self.vector_manager.add_documents(chunks)
                print(f"成功添加 {len(chunks)} 个文本块到向量数据库")

            os.remove(file_path)

            db_stats = self.get_vector_db_stats()

            return {
                "success": True,
                "message": f"文件处理成功！添加了 {len(chunks)} 个文本块到知识库",
                "document_count": db_stats["document_count"]
            }
        except Exception as e:
            print(f"处理文件时出错: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": f"处理文件时出错: {str(e)[:100]}"
            }

def init_assistant():
    """初始化AI助手"""
    global aassistant
    if aassistant is None:
        print("初始化AI助手...")
        # 延迟加载，只在需要时初始化
        aassistant = CompleteAIAssistant(persist_conversations=True)
        print("✅ AI助手初始化完成")

def main():
    """Streamlit主函数"""
    st.set_page_config(
        page_title="AI知识库问答助手",
        page_icon="🤖",
        layout="wide"
    )

    # 初始化会话状态
    if 'current_session_id' not in st.session_state:
        st.session_state.current_session_id = None
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'token' not in st.session_state:
        st.session_state.token = None
    if 'login_mode' not in st.session_state:
        st.session_state.login_mode = True  # True: 登录/注册，False: 已登录
    if 'is_processing' not in st.session_state:
        st.session_state.is_processing = False  # 防重复提交标志

    # 初始化AI助手
    init_assistant()

    # 登录/注册界面
    if st.session_state.login_mode:
        st.title("🔐 AI知识库问答助手 - 登录")
        
        tab1, tab2 = st.tabs(["登录", "注册"])
        
        with tab1:
            st.subheader("用户登录")
            # 使用st.form来支持enter键提交
            with st.form(key='login_form'):
                login_username = st.text_input("用户名", key="login_username")
                login_password = st.text_input("密码", type="password", key="login_password")
                login_button = st.form_submit_button("登录")
            
            if login_button:
                if login_username and login_password:
                    # 获取IP地址和用户代理
                    import requests
                    try:
                        ip_address = requests.get('https://api.ipify.org').text
                    except:
                        ip_address = "未知"
                    
                    user_agent = st.session_state.get('user_agent', '未知')
                    
                    result = aassistant.user_auth.login(login_username, login_password, ip_address, user_agent)
                    if result["success"]:
                        st.session_state.user_id = result["user_id"]
                        st.session_state.username = result["username"]
                        st.session_state.token = result["token"]
                        st.session_state.login_mode = False
                        # 登录成功后自动创建新会话
                        new_session = aassistant.create_new_session(result["user_id"])
                        if new_session:
                            st.session_state.current_session_id = new_session["id"]
                        st.rerun()
                    else:
                        st.error(result["message"])
                else:
                    st.error("请输入用户名和密码")
        
        with tab2:
            st.subheader("用户注册")
            # 使用st.form来支持enter键提交
            with st.form(key='register_form'):
                reg_username = st.text_input("用户名", key="reg_username")
                reg_password = st.text_input("密码", type="password", key="reg_password")
                reg_email = st.text_input("邮箱（可选）", key="reg_email")
                register_button = st.form_submit_button("注册")
            
            if register_button:
                if reg_username and reg_password:
                    result = aassistant.user_auth.register(reg_username, reg_password, reg_email)
                    if result["success"]:
                        st.success("注册成功，请登录")
                    else:
                        st.error(result["message"])
                else:
                    st.error("请输入用户名和密码")
        
        return

    # 已登录界面
    # 标题
    st.title("🤖 AI知识库问答助手")
    st.markdown(f"欢迎回来，{st.session_state.username}！基于RAG技术的智能知识库问答系统，支持文档检索、工具调用和多轮对话")

    # 监控页面
    if st.sidebar.button("📊 监控中心"):
        st.title("监控中心")
        
        # 添加返回对话按钮
        if st.button("🔙 返回对话界面"):
            # 重新运行应用，返回到对话界面
            st.rerun()
        
        # 获取登录统计信息
        stats = aassistant.user_auth.get_login_stats()
        
        # 显示登录统计
        st.subheader("登录接口性能监控")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("总尝试次数", stats["total_attempts"])
            st.metric("成功次数", stats["success_count"])
        
        with col2:
            st.metric("成功率", f"{stats['success_rate']:.2f}%")
            st.metric("平均响应时间", f"{stats['avg_response_time']:.3f}s")
        
        with col3:
            st.metric("P95响应时间", f"{stats['p95_response_time']:.3f}s")
            st.metric("P99响应时间", f"{stats['p99_response_time']:.3f}s")
        
        st.info("此监控面板显示最近7天的登录接口性能数据")
        
        # 显示系统信息
        st.subheader("系统信息")
        session_info = aassistant.get_session_info(st.session_state.user_id)
        db_stats = aassistant.get_vector_db_stats()
        info = f"""
        **模型**: 智能知识库助手
        **知识库**: {db_stats['document_count']} 个文档块
        **当前会话**: {session_info['title']}
        **会话消息**: {session_info['message_count']} 条
        **工具**: 计算器、时间查询、单位转换
        **状态**: 运行中
        **时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        st.markdown(info)
        
        return

    # 登出按钮
    if st.button("登出"):
        st.session_state.user_id = None
        st.session_state.username = None
        st.session_state.token = None
        st.session_state.login_mode = True
        st.rerun()

    # 源文档显示
    with st.expander("📄 参考来源"):
        sources_display = st.empty()

    # 聊天区域容器
    chat_container = None

    # 系统信息容器
    system_info_container = None

    # 加载系统信息
    def load_system_info():
        session_info = aassistant.get_session_info(st.session_state.user_id)
        db_stats = aassistant.get_vector_db_stats()
        info = f"""
        **模型**: 智能知识库助手
        **知识库**: {db_stats['document_count']} 个文档块
        **当前会话**: {session_info['title']}
        **会话消息**: {session_info['message_count']} 条
        **工具**: 计算器、时间查询、单位转换
        **状态**: 运行中
        **时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        if system_info_container:
            system_info_container.markdown(info)

    # 加载聊天历史
    def load_chat_history():
        # 明确传递当前会话ID，确保加载的是当前会话的历史
        history = aassistant.get_conversation_history(st.session_state.user_id, st.session_state.current_session_id)
        # 清空容器
        chat_container.empty()
        # 批量渲染消息，减少Streamlit的渲染次数
        with chat_container:
            for msg in history:
                if msg['role'] == 'user':
                    # 用户消息（右对齐，气泡效果）
                    # 调整列宽比例，用户头像在右边，靠边显示
                    col1, col2 = st.columns([9, 1])  # 两列布局：消息 | 头像
                    with col1:
                        # 气泡效果，符合规范要求
                        st.markdown("""<div style='position: relative; max-width: 68%; margin-left: auto; margin-right: 12px; margin-bottom: 16px;'>
                            <div style='background-color: rgba(40, 180, 99, 0.9); border-radius: 8px 12px 12px 8px; padding: 12px 16px; text-align: right; box-shadow: 0 1px 3px rgba(0,0,0,0.1); color: white;'>
                                """ + msg['content'] + """
                            </div>
                            <div style='position: absolute; bottom: 12px; right: -8px; width: 0; height: 0; border-top: 8px solid transparent; border-bottom: 8px solid transparent; border-left: 8px solid rgba(40, 180, 99, 0.9);'></div>
                        </div>""", unsafe_allow_html=True)
                    with col2:
                        st.markdown("<div style='font-size: 36px; text-align: right; display: flex; align-items: center; justify-content: flex-end; height: 100%;'>👤</div>", unsafe_allow_html=True)  # 用户头像在右边，靠边显示
                else:
                    # 助手消息（左对齐，气泡效果）
                    # 调整列宽比例，助手头像在左边，更大的头像，靠边显示
                    col1, col2 = st.columns([1, 9])  # 两列布局：头像 | 消息
                    with col1:
                        st.markdown("<div style='font-size: 40px; text-align: left; display: flex; align-items: center; height: 100%;'>🤖</div>", unsafe_allow_html=True)  # 更大的AI头像在左边，靠边显示
                    with col2:
                        # 气泡效果，符合规范要求
                        st.markdown("""<div style='position: relative; max-width: 68%; margin-left: 12px; margin-bottom: 16px;'>
                            <div style='background-color: #f9f9f9; border: 1px solid #e8e8e8; border-radius: 12px 8px 8px 12px; padding: 12px 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);'>
                                """ + msg['content'] + """
                            </div>
                            <div style='position: absolute; bottom: 12px; left: -8px; width: 0; height: 0; border-top: 8px solid transparent; border-bottom: 8px solid transparent; border-right: 8px solid #f9f9f9;'></div>
                        </div>""", unsafe_allow_html=True)

    # 主布局
    col1, col2 = st.columns([3, 1])

    with col1:
        # 聊天区域
        st.subheader("对话")
        chat_container = st.container(height=500)

        # 输入区域
        user_input = st.chat_input("请输入您的问题...")

        # 控制按钮
        col1_1, col1_2, col1_3 = st.columns(3)
        with col1_1:
            clear_btn = st.button("清空对话")
        with col1_2:
            new_chat_btn = st.button("新对话")
        with col1_3:
            export_btn = st.button("导出对话")

        # 状态显示
        status = st.empty()

    with col2:
        # 会话管理
        st.subheader("💬 会话管理")

        # 会话列表
        try:
            # 强制重新加载会话列表，确保获取最新的会话信息
            sessions = aassistant.list_sessions(st.session_state.user_id)
            session_options = [f"{session['title']} ({session['message_count']}条消息)" for session in sessions]
            session_ids = [session['id'] for session in sessions]

            if session_options:
                # 确保当前会话ID存在
                if not st.session_state.current_session_id and session_ids:
                    st.session_state.current_session_id = session_ids[0]
                    aassistant.switch_session(st.session_state.user_id, st.session_state.current_session_id)

                # 使用session_state来管理当前会话
                selected_index = 0
                if st.session_state.current_session_id:
                    if st.session_state.current_session_id in session_ids:
                        selected_index = session_ids.index(st.session_state.current_session_id)
                    else:
                        # 如果当前会话ID不在会话列表中，可能是刚创建的新会话
                        # 尝试从本地缓存获取会话列表
                        try:
                            from conversation_manager import ConversationManager
                            # 直接获取本地会话列表
                            local_sessions = list(aassistant.conversation_manager.conversations.get(st.session_state.user_id, {}).keys())
                            if st.session_state.current_session_id in local_sessions:
                                # 如果在本地缓存中找到，重新加载会话列表
                                sessions = aassistant.list_sessions(st.session_state.user_id)
                                session_options = [f"{session['title']} ({session['message_count']}条消息)" for session in sessions]
                                session_ids = [session['id'] for session in sessions]
                                if st.session_state.current_session_id in session_ids:
                                    selected_index = session_ids.index(st.session_state.current_session_id)
                        except Exception as e:
                            print(f"获取本地会话列表失败: {e}")

                # 使用st.empty()来确保会话选择器稳定显示
                session_selector_container = st.empty()
                with session_selector_container:
                    selected_session = st.selectbox(
                        "选择会话",
                        session_options,
                        index=selected_index,
                        key=f"session_selector_{st.session_state.current_session_id}"  # 添加动态key确保重新渲染
                    )
                selected_session_id = session_ids[session_options.index(selected_session)]

                # 检测会话切换
                if st.session_state.current_session_id != selected_session_id:
                    st.session_state.current_session_id = selected_session_id
                    aassistant.switch_session(st.session_state.user_id, selected_session_id)
                    # 重新加载聊天历史以显示当前会话内容
                    load_chat_history()
                    load_system_info()
                    # 强制重新渲染页面，确保所有组件都能响应状态变化
                    st.rerun()

                # 会话标题
                session_title = st.text_input("会话标题", value=sessions[session_options.index(selected_session)]['title'])
                update_title_btn = st.button("更新标题")
                
                # 清空所有会话按钮
                if st.button("清空所有会话"):
                    aassistant.conversation_manager.clear_all_sessions(st.session_state.user_id)
                    st.session_state.current_session_id = None
                    st.rerun()
            else:
                # 如果没有会话，创建一个新会话
                if not st.session_state.current_session_id:
                    new_session = aassistant.create_new_session(st.session_state.user_id)
                    if new_session:
                        st.session_state.current_session_id = new_session["id"]
                        st.rerun()
                    else:
                        st.info("暂无会话，请创建新对话")
        except Exception as e:
            st.error(f"会话管理出错: {str(e)}")
            # 尝试恢复会话
            if not st.session_state.current_session_id:
                new_session = aassistant.create_new_session(st.session_state.user_id)
                if new_session:
                    st.session_state.current_session_id = new_session["id"]
                    st.rerun()

        # 文件上传
        st.subheader("📁 文件上传")
        uploaded_files = st.file_uploader("上传文件（支持PDF、TXT、MD）",
                                         type=["pdf", "txt", "md"],
                                         accept_multiple_files=True)
        upload_status = st.empty()

        # 设置
        st.subheader("⚙️ 设置")
        use_rag = st.checkbox("使用知识库检索", value=True)
        use_tools = st.checkbox("启用工具（包括时间查询）", value=True)

        # 系统信息
        st.subheader("ℹ️ 系统信息")
        # 创建系统信息容器
        system_info_container = st.empty()
        # 显示系统信息内容
        load_system_info()

    # 初始化页面
    try:
        # 确保当前会话ID存在
        if not st.session_state.current_session_id:
            sessions = aassistant.list_sessions(st.session_state.user_id)
            if sessions:
                st.session_state.current_session_id = sessions[0]['id']
                aassistant.switch_session(st.session_state.user_id, st.session_state.current_session_id)
            else:
                # 创建新会话
                new_session = aassistant.create_new_session(st.session_state.user_id)
                if new_session:
                    st.session_state.current_session_id = new_session["id"]
        # 加载聊天历史
        load_chat_history()
    except Exception as e:
        st.error(f"初始化出错: {str(e)}")
        # 尝试恢复
        new_session = aassistant.create_new_session(st.session_state.user_id)
        if new_session:
            st.session_state.current_session_id = new_session["id"]
            st.rerun()

    # 处理用户输入
    if user_input and user_input.strip() and not st.session_state.is_processing:
        # 设置处理标志，防止重复提交
        st.session_state.is_processing = True
        try:
            # 使用st.spinner显示加载状态，避免界面变灰
            with st.spinner("⏳ 正在思考..."):
                # 调用AI助手，传递当前会话ID
                result = aassistant.chat(st.session_state.user_id, user_input, use_tools, use_rag, session_id=st.session_state.current_session_id)

            # 重新加载聊天历史，确保所有消息正确显示
            load_chat_history()

            # 更新状态
            if result.get('success', False):
                status.text("✅ 回答完成")
            else:
                status.text("❌ 回答失败")

            # 显示源文档
            if result.get('sources_used'):
                sources_html = ""
                for i, source in enumerate(result['sources_used'], 1):
                    sources_html += f"**{i}. {source['source']} (页: {source['page']})**\n"
                    sources_html += f"{source['content_preview']}\n\n"
                sources_display.markdown(sources_html)

            # 重新加载系统信息
            load_system_info()
        finally:
            # 无论处理是否成功，都重置处理标志
            st.session_state.is_processing = False

    # 处理清空对话
    if clear_btn:
        aassistant.clear_conversation(st.session_state.user_id, session_id=st.session_state.current_session_id)
        status.text("✅ 对话已清空")
        # 强制重新渲染页面，确保对话历史完全清空
        st.rerun()

    # 处理新对话
    if new_chat_btn:
        try:
            # 保存当前用户ID
            user_id = st.session_state.user_id
            
            # 获取当前所有会话
            current_sessions = aassistant.list_sessions(user_id)
            
            # 检查是否已经是最新的会话
            if current_sessions:
                # 按更新时间排序，最新的会话在前面
                sorted_sessions = sorted(current_sessions, key=lambda x: x.get('updated_at', ''), reverse=True)
                latest_session_id = sorted_sessions[0]['id']
                
                # 如果当前会话就是最新的，提示用户
                if st.session_state.current_session_id == latest_session_id:
                    status.text("⚠️ 已经是最新的会话")
                else:
                    # 创建新会话
                    new_session = aassistant.create_new_session(user_id)
                    if new_session:
                        # 更新会话状态
                        st.session_state.current_session_id = new_session["id"]
                        # 强制重新渲染页面，确保会话选择器更新并选择新会话
                        # 先清空状态显示，避免显示旧状态
                        status.empty()
                        # 立即显示创建成功的消息
                        status.text(f"✅ 新对话已创建: {new_session['title']}")
                        # 强制重新渲染页面，确保所有组件都能响应状态变化
                        st.rerun()
                    else:
                        status.text("❌ 创建新对话失败")
            else:
                # 没有会话，创建新会话
                new_session = aassistant.create_new_session(user_id)
                if new_session:
                    # 更新会话状态
                    st.session_state.current_session_id = new_session["id"]
                    # 强制重新渲染页面，确保会话选择器更新并选择新会话
                    # 先清空状态显示，避免显示旧状态
                    status.empty()
                    # 立即显示创建成功的消息
                    status.text(f"✅ 新对话已创建: {new_session['title']}")
                    # 强制重新渲染页面，确保所有组件都能响应状态变化
                    st.rerun()
                else:
                    status.text("❌ 创建新对话失败")
        except Exception as e:
            status.text(f"❌ 创建新对话失败: {str(e)}")
            print(f"创建新对话失败: {e}")

    # 初始化导出状态
    if 'export_mode' not in st.session_state:
        st.session_state.export_mode = False

    # 处理导出对话
    if export_btn:
        st.session_state.export_mode = True

    # 显示导出选项
    if st.session_state.export_mode:
        # 明确传递当前会话ID，确保导出的是当前会话的内容
        history = aassistant.get_conversation_history(st.session_state.user_id, st.session_state.current_session_id)
        if history:
            with st.container():
                export_format = st.selectbox(
                    "选择导出格式",
                    ["Markdown", "JSON", "Text"],
                    key="export_format"
                )

                if export_format == "Markdown":
                    export_content = "# AI知识库问答助手 - 对话历史\n\n"
                    for msg in history:
                        role = "用户" if msg["role"] == "user" else "助手"
                        content = msg["content"]
                        timestamp = msg.get("timestamp", "")

                        export_content += f"## {role}\n"
                        if timestamp:
                            export_content += f"**时间**: {timestamp}\n"
                        export_content += f"{content}\n\n"
                    file_ext = "md"
                    mime = "text/markdown"
                elif export_format == "JSON":
                    export_content = json.dumps(history, ensure_ascii=False, indent=2)
                    file_ext = "json"
                    mime = "application/json"
                else:
                    export_content = "AI知识库问答助手 - 对话历史\n\n"
                    for msg in history:
                        role = "用户" if msg["role"] == "user" else "助手"
                        content = msg["content"]
                        timestamp = msg.get("timestamp", "")

                        export_content += f"{role}:\n"
                        if timestamp:
                            export_content += f"时间: {timestamp}\n"
                        export_content += f"{content}\n\n"
                    file_ext = "txt"
                    mime = "text/plain"

                export_file = f"conversation_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_ext}"
                st.download_button(
                    label="下载对话历史",
                    data=export_content,
                    file_name=export_file,
                    mime=mime
                )

                if st.button("取消导出"):
                    st.session_state.export_mode = False
        else:
            status.text("❌ 对话历史为空")
            if st.button("取消"):
                st.session_state.export_mode = False

    # 处理更新会话标题
    if 'update_title_btn' in locals() and update_title_btn:
        if session_title:
            aassistant.set_session_title(st.session_state.user_id, session_title)
            status.text(f"✅ 标题已更新: {session_title}")
            load_system_info()
        else:
            status.text("❌ 标题不能为空")

    # 处理文件上传
    if uploaded_files:
        total_files = len(uploaded_files)
        total_chunks = 0

        for i, file in enumerate(uploaded_files, 1):
            upload_status.text(f"⏳ 处理第 {i}/{total_files} 个文件...")
            result = aassistant.process_uploaded_file(file)
            if result['success']:
                import re
                match = re.search(r"添加了 (\d+) 个文本块", result['message'])
                if match:
                    total_chunks += int(match.group(1))
            else:
                upload_status.text(f"❌ 处理文件 {file.name} 失败: {result['message']}")
                break
        else:
            upload_status.text(f"✅ 成功处理 {total_files} 个文件，添加了 {total_chunks} 个文本块到知识库")
            load_system_info()

if __name__ == "__main__":
    main()