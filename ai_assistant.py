# ai_assistant_fixed_v2.py
# 使用修复版 RAG 的 AI 助手

import sys
import os
from typing import Dict, Any, Optional, List
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rag_chain import RobustRAGChain
from conversation_manager import ConversationManager
from tool_integration import ToolIntegration
from config import DEEPSEEK_API_KEY


class AIAssistantFixedV2:
    """使用修复版 RAG 的 AI 助手"""

    def __init__(self, persist_conversations: bool = True):
        """
        初始化 AI 助手

        参数:
            persist_conversations: 是否持久化对话记录
        """
        print("初始化 AI 助手 (修复版)...")
        print("=" * 50)

        # 检查 API 密钥
        if not DEEPSEEK_API_KEY or DEEPSEEK_API_KEY == "您的DeepSeek-API-KEY-在这里":
            print("⚠️  警告: 未设置 DeepSeek API 密钥")
            print("   请在 config.py 中设置您的 API 密钥")

        # 初始化组件
        print("1. 初始化 RAG 链 (修复版)...")
        self.rag_chain = RobustRAGChain()

        print("2. 初始化对话管理器...")
        persist_file = "conversations.json" if persist_conversations else None
        self.conversation_manager = ConversationManager(
            max_history=10,
            persist_file=persist_file
        )

        print("3. 初始化工具集成...")
        self.tool_integration = ToolIntegration()

        print("4. 创建新对话会话...")
        self.current_session = self.conversation_manager.create_session()

        print("✅ AI 助手初始化完成！")
        print("=" * 50)

    def chat(self, message: str, session_id: Optional[str] = None,
             use_tools: bool = True, use_rag: bool = True) -> Dict[str, Any]:
        """
        聊天接口

        参数:
            message: 用户消息
            session_id: 会话ID
            use_tools: 是否使用工具
            use_rag: 是否使用RAG检索

        返回:
            响应结果
        """
        if session_id:
            self.conversation_manager.current_session_id = session_id
            self.current_session = session_id

        # 添加用户消息到历史
        self.conversation_manager.add_message("user", message)

        response = {
            "session_id": self.current_session,
            "user_message": message,
            "assistant_response": "",
            "tools_used": [],
            "sources_used": [],
            "success": False
        }

        try:
            # 1. 检查是否应使用工具
            tool_suggestion = None
            if use_tools:
                tool_suggestion = self.tool_integration.auto_detect_tool(message)

            # 2. 如果检测到工具，执行工具
            if tool_suggestion and tool_suggestion["confidence"] > 0.7:
                tool_result = self.tool_integration.execute_tool(
                    tool_suggestion["tool_id"],
                    **tool_suggestion["parameters"]
                )

                if tool_result["success"]:
                    # 安全地构建工具响应
                    try:
                        import json
                        tool_response = f"我使用了{tool_result.get('tool', '工具')}工具：\n"
                        if "formatted" in tool_result.get("result", {}):
                            tool_response += f"结果: {tool_result['result']['formatted']}"
                        else:
                            # 避免JSON序列化问题
                            result_str = str(tool_result.get("result", {}))
                            tool_response += f"结果: {result_str}"

                        response["assistant_response"] = tool_response
                        response["tools_used"] = [{
                            "tool": tool_result.get("tool", "未知工具"),
                            "result": tool_result.get("result", {})
                        }]
                        response["success"] = True

                        # 添加到对话历史
                        self.conversation_manager.add_message("assistant", tool_response,
                                                              metadata={"type": "tool"})

                        return response
                    except Exception as tool_error:
                        print(f"工具响应构建失败: {tool_error}")

            # 3. 使用RAG回答问题
            if use_rag:
                # 获取最近的对话历史
                chat_history = self.conversation_manager.get_recent_history(last_n=3)

                # 通过RAG获取答案
                rag_result = self.rag_chain.ask(message, chat_history)

                if isinstance(rag_result, dict) and rag_result.get("success", False):
                    # 确保回答是字符串
                    answer = str(rag_result.get("answer", ""))
                    response["assistant_response"] = answer

                    # 处理源文档信息
                    sources_info = rag_result.get("sources_info", [])
                    if isinstance(sources_info, list):
                        # 简化源文档信息
                        simplified_sources = []
                        for source in sources_info:
                            if isinstance(source, dict):
                                simplified_sources.append({
                                    "source": str(source.get("source", "未知")),
                                    "page": str(source.get("page", 0)),
                                    "content_preview": str(source.get("content_preview", ""))[:100] + "..."
                                })
                        response["sources_used"] = simplified_sources

                    response["success"] = True
                else:
                    # RAG失败，尝试基础对话
                    print("RAG失败，尝试基础对话...")
                    try:
                        from langchain_openai import ChatOpenAI
                        from config import DEEPSEEK_API_KEY, MODEL_SETTINGS

                        llm = ChatOpenAI(
                            api_key=DEEPSEEK_API_KEY,
                            base_url=MODEL_SETTINGS["api_base"],
                            model=MODEL_SETTINGS["model_name"],
                            temperature=MODEL_SETTINGS["temperature"],
                            max_tokens=MODEL_SETTINGS["max_tokens"]
                        )

                        simple_response = llm.invoke(f"问题: {message}")
                        answer = str(simple_response.content)
                        response["assistant_response"] = f"（基础模式）{answer}"
                        response["success"] = True
                    except Exception as simple_error:
                        print(f"基础对话也失败: {simple_error}")
                        error_msg = rag_result.get("answer", "抱歉，我无法回答这个问题。") if isinstance(rag_result,
                                                                                                       dict) else "API调用失败"
                        response["assistant_response"] = str(error_msg)
                        response["success"] = False
            else:
                # 不使用RAG，简单回应
                response["assistant_response"] = "您的问题已收到，但我当前配置为不使用知识库检索。"
                response["success"] = True

            # 4. 添加到对话历史
            if response["success"]:
                self.conversation_manager.add_message("assistant", response["assistant_response"],
                                                      metadata={"type": "rag" if use_rag else "base"})

        except Exception as e:
            error_msg = f"处理消息时出错: {str(e)[:100]}"
            print(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()

            response["assistant_response"] = f"抱歉，处理您的消息时出现错误: {str(e)[:100]}..."
            response["success"] = False

        return response

    def get_conversation_history(self, as_string: bool = False) -> Any:
        """
        获取当前对话历史

        参数:
            as_string: 是否返回字符串格式

        返回:
            对话历史
        """
        return self.conversation_manager.get_conversation_history(as_string=as_string)

    def clear_conversation(self):
        """清空当前对话"""
        self.conversation_manager.clear_conversation()
        print("✅ 对话已清空")

    def list_sessions(self) -> List[Dict[str, Any]]:
        """
        列出所有会话

        返回:
            会话列表
        """
        return self.conversation_manager.list_sessions()

    def switch_session(self, session_id: str):
        """
        切换到指定会话

        参数:
            session_id: 会话 ID
        """
        if self.conversation_manager.switch_session(session_id):
            self.current_session = session_id
            return True
        else:
            print(f"❌ 会话不存在: {session_id}")
            return False

    def get_session_info(self) -> Dict[str, Any]:
        """
        获取当前会话信息

        返回:
            会话信息
        """
        sessions = self.list_sessions()
        for session in sessions:
            if session["id"] == self.current_session:
                return session

        return {}

    def simple_chat(self, message: str) -> str:
        """
        简化版聊天接口

        参数:
            message: 用户消息

        返回:
            助手回复
        """
        result = self.chat(message)
        return result["assistant_response"]


def test_ai_assistant_fixed():
    """测试修复版 AI 助手"""
    print("测试修复版 AI 助手")
    print("=" * 60)

    try:
        # 初始化助手
        print("1. 初始化 AI 助手...")
        assistant = AIAssistantFixedV2(persist_conversations=False)

        # 测试对话
        test_messages = [
            "你好，请介绍一下你自己",
            "这个知识库系统使用了哪些技术？",
            "计算一下 15 * 3 + 20 等于多少",
            "现在的时间是什么？"
        ]

        print("\n2. 测试对话:")
        for i, message in enumerate(test_messages, 1):
            print(f"\n{i}. 用户: {message}")
            result = assistant.chat(message)

            if result["success"]:
                print(f"   助手: {result['assistant_response'][:150]}...")

                if result["tools_used"]:
                    print(f"   使用的工具: {result['tools_used'][0]['tool']}")

                if result["sources_used"]:
                    print(f"   引用来源: {len(result['sources_used'])} 个")
            else:
                print(f"   ❌ 失败: {result['assistant_response']}")

        print("\n" + "=" * 60)
        print("✅ AI 助手测试完成！")
        print("=" * 60)

        return assistant

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    test_ai_assistant_fixed()