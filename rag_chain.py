import sys
import os
import json
import requests
import time
from typing import List, Dict, Any, Optional
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from config import DEEPSEEK_API_KEY, MODEL_SETTINGS, RETRIEVAL_SETTINGS, SYSTEM_PROMPTS

# 添加当前目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from vector_store_manager import VectorStoreManager
from advanced_ai import AdvancedAIModule, ConversationStateManager


class RobustRAGChain:
    """健壮的 RAG 检索链：结合向量检索、联网搜索和稳定的 API 调用"""

    def __init__(self, vector_store_manager: Optional[VectorStoreManager] = None):
        """
        初始化 RAG 链

        参数:
            vector_store_manager: 向量数据库管理器
        """
        # 初始化向量存储管理器
        if vector_store_manager:
            self.vector_manager = vector_store_manager
        else:
            self.vector_manager = VectorStoreManager()

        # 初始化高级AI模块
        self.advanced_ai = AdvancedAIModule(self.vector_manager)
        
        # 初始化对话状态管理器
        self.conversation_state_manager = ConversationStateManager()

        # 初始化检索器
        self.retriever = self.vector_manager.vector_store.as_retriever(
            search_kwargs=RETRIEVAL_SETTINGS["search_kwargs"]
        )

        # 定义 Prompt 模板
        self.prompt_template = self._create_prompt_template()
        self.web_search_prompt_template = self._create_web_search_prompt_template()
        self.conflict_resolution_prompt_template = self._create_conflict_resolution_prompt_template()

        # API 配置
        self.api_key = DEEPSEEK_API_KEY
        self.api_url = MODEL_SETTINGS["api_base"] + "/chat/completions"
        self.model_name = MODEL_SETTINGS["model_name"]
        self.temperature = MODEL_SETTINGS["temperature"]
        self.max_tokens = MODEL_SETTINGS["max_tokens"]

        print("✅ 健壮 RAG 检索链初始化完成")

    def _create_prompt_template(self) -> str:
        """创建 Prompt 模板"""

        template = f"""# 角色设定
{SYSTEM_PROMPTS.get('rag', '你是一个AI知识库智能体，专门用于回答用户关于知识库的问题。')}

# 核心功能定位
你支持：PDF/DOCX/TXT/PPT/Excel等多种格式文档解析、向量化存储、语义检索。用户上传的文档已被处理成向量片段，你接收到的{context}是通过向量检索获得的最相关文档片段集合。

# 输入信息结构
## 检索到的文档上下文（向量检索结果）：
{context}

## 历史对话记录（最近5轮）：
{chat_history}

## 当前用户问题：
{question}

# 处理优先级规则（严格按顺序执行）

## 第一优先级：精确匹配（当检索到高度相关文档时）
1. **文档优先原则**：如果{context}中包含与{question}直接相关的信息，必须以此为主要回答依据
2. **引用标注**：从{context}引用的每个信息点，末尾用【文档】标注来源
3. **片段整合**：如果{context}包含多个相关片段，需进行逻辑整合，避免简单拼接

## 第二优先级：知识补充（当文档信息不足时）
4. **知识补充规则**：如果{context}信息不完整或不充分，可调用自身知识库补充，但必须：
   - 明确区分"根据文档"和"根据我的知识"
   - 补充内容需与文档信息逻辑一致
   - 用【知识】标注补充部分

## 第三优先级：知识库直接回答（当文档完全无关时）
5. **无关判定标准**：如果{context}内容与{question}完全无关（经过严格判定后）
   - 明确告知"文档中未找到相关信息"
   - 切换为纯DeepSeek AI模式回答
   - 回答末尾标注【全知识库回答】

## 第四优先级：无法回答（两者均无信息）
6. **诚实机制**：如果文档和自身知识均无法回答，必须：
   - 清晰说明无法回答的原因
   - 建议用户重新表述问题或提供更多背景
   - 不猜测、不编造

# 回答格式规范

## 结构要求
1. **核心回答**（首段）：直接、简洁回答用户问题，不超过3句话
2. **详细解释**（可选）：需要时才展开，分点说明
3. **来源说明**（必含）：明确标注信息来自文档还是知识库
4. **行动建议**（相关时）：提供下一步操作建议

## 标注系统
- 【文档】：信息来自上传的文档
- 【知识】：信息来自AI自身知识库  
- 【推理】：基于两者的逻辑推理
- 【建议】：给用户的后续操作建议

# 特殊场景处理

## 多步骤推理问题
- 展示完整推理链条
- 每步标注依据来源
- 最后总结关键结论

## 矛盾信息处理
- 如果文档信息与常识矛盾：指出矛盾点
- 优先以文档为准（假设文档是用户权威来源）
- 备注可能存在的不一致

## 模糊/宽泛问题
- 请求具体化或提供示例
- 给出多个可能的解释方向
- 说明回答的局限性

# 语言与风格
- 主语言：中文（除非用户指定其他语言）
- 语气：专业、友好、直接
- 长度：根据问题复杂度自适应，避免冗余
- 专业术语：保持原文术语，首次出现可简单解释

# 质量控制
- 避免主观评价文档内容
- 不提及"向量检索""文档片段"等内部实现细节
- 不重复{question}的原文表述
- 确保回答逻辑自洽、无内部矛盾

现在，基于以上规则处理用户的请求。"""

        return template

    def _create_web_search_prompt_template(self) -> str:
        """创建网络搜索提示模板"""
        template = f"""# 角色设定
{SYSTEM_PROMPTS.get('web_search', '你是DeepSeek AI联网搜索助手，负责根据用户问题进行联网搜索并提供准确的信息。')}

# 输入信息
用户问题：{question}

# 任务要求
1. 分析用户问题，确定搜索关键词
2. 基于搜索结果，提供准确、最新的信息
3. 确保回答全面且符合事实
4. 引用搜索结果的来源

# 回答格式
- 直接回答用户问题
- 提供详细信息
- 标注信息来源

现在，开始处理用户的搜索请求。"""
        return template

    def _create_conflict_resolution_prompt_template(self) -> str:
        """创建冲突解决提示模板"""
        template = f"""# 角色设定
{SYSTEM_PROMPTS.get('conflict_resolution', '你是DeepSeek AI冲突协调助手，负责处理知识库信息和联网搜索信息之间的冲突。')}

# 输入信息
## 知识库信息：
{knowledge_base_info}

## 联网搜索信息：
{web_search_info}

## 用户问题：
{question}

# 任务要求
1. 分析两种信息之间的冲突点
2. 客观呈现两种不同的信息
3. 不偏向任何一方，保持中立
4. 明确告知用户存在信息冲突
5. 建议用户根据实际情况判断

# 回答格式
- 首先说明存在信息冲突
- 分别呈现两种信息及其来源
- 分析可能的原因
- 给出建议

现在，开始处理冲突信息。"""
        return template

    def _call_api_with_retry(self, messages: List[Dict], max_retries: int = 3) -> Dict:
        """带重试机制的 API 调用"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": self.model_name,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "stream": False
        }

        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self.api_url,
                    headers=headers,
                    json=data,
                    timeout=30
                )

                if response.status_code == 200:
                    return {"success": True, "data": response.json()}
                elif response.status_code == 429:  # Rate limit
                    wait_time = 2 ** attempt  # 指数退避
                    print(f"⚠️ 频率限制，等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                    continue
                else:
                    return {
                        "success": False,
                        "error": f"API 错误 ({response.status_code}): {response.text[:200]}"
                    }

            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    print(f"⚠️ 请求超时，第 {attempt + 1} 次重试...")
                    time.sleep(1)
                    continue
                else:
                    return {"success": False, "error": "请求超时"}

            except requests.exceptions.ConnectionError:
                if attempt < max_retries - 1:
                    print(f"⚠️ 连接错误，第 {attempt + 1} 次重试...")
                    time.sleep(1)
                    continue
                else:
                    return {"success": False, "error": "连接错误"}

            except json.JSONDecodeError as e:
                return {"success": False, "error": f"JSON 解析错误: {e}"}

            except Exception as e:
                return {"success": False, "error": f"未知错误: {str(e)}"}

        return {"success": False, "error": "达到最大重试次数"}

    def ask(self, question: str, chat_history: str = "", session_id: str = "default") -> Dict[str, Any]:
        """
        回答问题

        参数:
            question: 用户问题
            chat_history: 对话历史
            session_id: 会话ID，用于对话状态管理

        返回:
            包含答案和元数据的字典
        """
        if not question.strip():
            return {
                "answer": "问题不能为空",
                "source_documents": [],
                "sources_info": [],
                "success": False
            }

        print(f"\n🔍 用户提问: {question}")
        print(f"会话ID: {session_id}")
        print("执行RAG检索...")

        try:
            # 获取对话状态
            conversation_state = self.conversation_state_manager.get_state(session_id)
            
            # 检查是否与上一个问题相似
            if conversation_state.get("last_question"):
                similarity = self.advanced_ai.question_similarity_detection(
                    conversation_state["last_question"], question
                )
                if similarity > 0.8:
                    print(f"⚠️ 检测到相似问题，相似度: {similarity:.3f}")
                    # 可以返回之前的回答或进行适当处理

            # 1. 使用高级AI模块执行语义搜索
            source_docs = self.advanced_ai.semantic_search(question, k=4, score_threshold=0.5)

            # 2. 构建上下文
            context = ""
            for i, doc in enumerate(source_docs):
                # 提取文档关键信息
                key_info = self.advanced_ai.extract_key_information(doc)
                context += f"{i+1}. {key_info['summary']}\n关键词: {', '.join(key_info['keywords'][:5])}\n"

            # 3. 判断知识库是否有相关信息
            has_knowledge_base_info = len(source_docs) > 0 and any(len(doc.page_content.strip()) > 0 for doc in source_docs)

            # 4. 保持对话语义连贯性
            enhanced_question = self.advanced_ai.maintain_conversation_coherence(
                [{'role': 'user', 'content': question}], question
            )

            # 5. 构建消息
            prompt = self.prompt_template.format(
                context=context,
                chat_history=chat_history,
                question=enhanced_question
            )

            messages = [
                {"role": "user", "content": prompt}
            ]

            # 6. 调用API获取知识库回答
            api_result = self._call_api_with_retry(messages)

            knowledge_base_answer = ""
            if api_result["success"]:
                data = api_result["data"]
                knowledge_base_answer = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                if not isinstance(knowledge_base_answer, str):
                    knowledge_base_answer = str(knowledge_base_answer)

            # 7. 执行联网搜索
            print("执行联网搜索...")
            web_search_prompt = self.web_search_prompt_template.format(question=enhanced_question)
            web_search_messages = [
                {"role": "user", "content": web_search_prompt}
            ]
            web_search_result = self._call_api_with_retry(web_search_messages)

            web_search_answer = ""
            if web_search_result["success"]:
                web_search_data = web_search_result["data"]
                web_search_answer = web_search_data.get("choices", [{}])[0].get("message", {}).get("content", "")
                if not isinstance(web_search_answer, str):
                    web_search_answer = str(web_search_answer)

            # 8. 处理结果
            final_answer = ""
            sources_info = []

            if has_knowledge_base_info:
                # 有知识库信息，检查是否需要冲突处理
                if web_search_answer and "未找到相关信息" not in knowledge_base_answer:
                    # 检查是否存在冲突
                    conflict_prompt = self.conflict_resolution_prompt_template.format(
                        knowledge_base_info=knowledge_base_answer,
                        web_search_info=web_search_answer,
                        question=enhanced_question
                    )
                    conflict_messages = [
                        {"role": "user", "content": conflict_prompt}
                    ]
                    conflict_result = self._call_api_with_retry(conflict_messages)

                    if conflict_result["success"]:
                        conflict_data = conflict_result["data"]
                        final_answer = conflict_data.get("choices", [{}])[0].get("message", {}).get("content", "")
                        if not isinstance(final_answer, str):
                            final_answer = str(final_answer)
                    else:
                        # 冲突处理失败，使用知识库回答
                        final_answer = knowledge_base_answer
                else:
                    # 无冲突，使用知识库回答
                    final_answer = knowledge_base_answer
                
                # 处理源文档信息
                sources_info = self._process_source_documents(source_docs)
            else:
                # 无知识库信息，使用联网搜索结果
                if web_search_answer:
                    final_answer = f"根据联网搜索结果：\n{web_search_answer}"
                else:
                    final_answer = "抱歉，无法从知识库和联网搜索中获取相关信息。"

            # 更新对话状态
            self.conversation_state_manager.set_last_question(session_id, question)
            self.conversation_state_manager.add_related_documents(session_id, source_docs)
            
            # 如果是新会话，设置对话主题
            if conversation_state["interaction_count"] == 0:
                # 简单提取主题
                topic = question[:50]
                self.conversation_state_manager.set_topic(session_id, topic)

            response = {
                "answer": final_answer,
                "source_documents": source_docs,
                "sources_info": sources_info,
                "success": True,
                "conversation_state": self.conversation_state_manager.get_conversation_context(session_id)
            }

            print(f"✅ 回答生成完成")
            print(f"   使用上下文数: {len(source_docs)}")
            print(f"   是否使用联网搜索: {'是' if web_search_answer else '否'}")
            print(f"   对话主题: {conversation_state.get('topic', '未设置')}")
            print(f"   交互次数: {conversation_state.get('interaction_count', 0)}")

            return response

        except Exception as e:
            error_msg = f"回答问题时出错: {str(e)}"
            print(f"❌ {error_msg}")

            import traceback
            error_details = traceback.format_exc()
            print(f"错误详情:\n{error_details}")

            # 检查是否是JSON解析错误
            if "JSON" in str(e) or "json" in str(e).lower():
                return {
                    "answer": "API返回了无效的响应格式，请稍后重试。",
                    "source_documents": [],
                    "sources_info": [],
                    "success": False
                }
            else:
                return {
                    "answer": f"处理问题时出现错误: {str(e)[:100]}...",
                    "source_documents": [],
                    "sources_info": [],
                    "success": False
                }

    def _process_source_documents(self, documents: List[Document]) -> List[Dict]:
        """处理源文档信息"""
        sources = []

        for i, doc in enumerate(documents):
            source_info = {
                "id": i + 1,
                "content_preview": doc.page_content[:150] + "..." if len(doc.page_content) > 150 else doc.page_content,
                "metadata": doc.metadata,
                "source": doc.metadata.get("source", "未知"),
                "page": doc.metadata.get("page", 0)
            }
            sources.append(source_info)

        return sources

    def simple_ask(self, question: str) -> str:
        """
        简化版问答（不返回元数据）

        参数:
            question: 用户问题

        返回:
            答案字符串
        """
        result = self.ask(question)
        return result["answer"]

    def search_only(self, query: str, k: int = 4) -> List[Document]:
        """
        仅执行搜索，不生成回答

        参数:
            query: 查询文本
            k: 返回结果数量

        返回:
            相关文档列表
        """
        return self.vector_manager.similarity_search(query, k=k)


def test_robust_rag_chain():
    """测试健壮的 RAG 链"""
    print("测试健壮的 RAG 检索链")
    print("=" * 60)

    try:
        # 初始化 RAG 链
        print("1. 初始化 RAG 链...")
        rag = RobustRAGChain()

        # 测试问题
        test_questions = [
            "这个知识库系统是什么？",
            "使用了哪些技术？",
            "有哪些功能特点？"
        ]

        for i, question in enumerate(test_questions, 1):
            print(f"\n{i}. 测试问题: '{question}'")
            print("-" * 40)

            result = rag.ask(question)

            if result["success"]:
                print(f"✅ 回答: {result['answer'][:200]}...")

                if result["sources_info"]:
                    print(f"   引用来源: {len(result['sources_info'])} 个")
                    for source in result["sources_info"][:2]:  # 显示前 2 个
                        print(f"     - {source['source']} (页: {source.get('page', 'N/A')})")
            else:
                print(f"❌ 失败: {result['answer']}")

            print()

        print("=" * 60)
        print("✅ 健壮 RAG 链测试完成！")
        print("=" * 60)

        return rag

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # 运行测试
    test_robust_rag_chain()