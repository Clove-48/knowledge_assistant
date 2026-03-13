# vector_store_manager.py
# 向量数据库管理模块

import os
from typing import List, Optional, Dict, Any
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from config import VECTORDB_SETTINGS


class VectorStoreManager:
    """向量数据库管理器"""

    def __init__(self, persist_directory: Optional[str] = None,
                 collection_name: Optional[str] = None):
        """
        初始化向量数据库管理器

        参数:
            persist_directory: 向量数据库持久化目录
            collection_name: 集合名称
        """
        # 使用配置或传入的参数
        self.persist_directory = persist_directory or VECTORDB_SETTINGS["persist_directory"]
        self.collection_name = collection_name or VECTORDB_SETTINGS["collection_name"]

        # 初始化嵌入模型（使用本地模型，免费且速度快）
        print("正在加载嵌入模型...")
        local_model_path = "./models/bge-small-zh-v1.5"
        
        # 检查本地模型是否存在（sentence-transformers格式）
        if os.path.exists(local_model_path) and os.path.isdir(local_model_path):
            # 检查是否有必要的文件
            required_files = ["config.json", "tokenizer.json", "vocab.txt"]
            has_required_files = any(os.path.exists(os.path.join(local_model_path, f)) for f in required_files)
            
            # 检查是否有模型权重文件
            model_files = ["pytorch_model.bin", "model.safetensors"]
            has_model_files = any(os.path.exists(os.path.join(local_model_path, f)) for f in model_files)
            
            if has_required_files and has_model_files:
                print(f"✅ 使用本地模型: {local_model_path}")
                # 使用 HuggingFaceEmbeddings 加载本地模型
                self.embeddings = HuggingFaceEmbeddings(
                    model_name=local_model_path,
                    model_kwargs={'device': 'cpu'},
                    encode_kwargs={'normalize_embeddings': True}
                )
            else:
                print("⚠️ 本地模型文件不完整，使用在线模型")
                self.embeddings = HuggingFaceEmbeddings(
                    model_name="BAAI/bge-small-zh-v1.5",
                    model_kwargs={'device': 'cpu'},
                    encode_kwargs={'normalize_embeddings': True}
                )
        else:
            print("⚠️ 本地模型目录不存在，使用在线模型")
            self.embeddings = HuggingFaceEmbeddings(
                model_name="BAAI/bge-small-zh-v1.5",
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )

        print("✅ 嵌入模型加载完成")

        # 初始化向量数据库
        self.vector_store = None
        self._init_vector_store()

    def _init_vector_store(self):
        """初始化向量数据库"""
        # 如果持久化目录存在，尝试加载现有数据库
        if os.path.exists(self.persist_directory) and os.listdir(self.persist_directory):
            print(f"加载现有向量数据库: {self.persist_directory}")
            try:
                self.vector_store = Chroma(
                    persist_directory=self.persist_directory,
                    collection_name=self.collection_name,
                    embedding_function=self.embeddings
                )
                print(f"✅ 向量数据库加载成功，集合: {self.collection_name}")
            except Exception as e:
                print(f"加载现有数据库失败，创建新的: {e}")
                self._create_new_vector_store()
        else:
            self._create_new_vector_store()

    def _create_new_vector_store(self):
        """创建新的向量数据库"""
        print(f"创建新的向量数据库: {self.persist_directory}")
        os.makedirs(self.persist_directory, exist_ok=True)

        # 创建空的向量数据库
        self.vector_store = Chroma(
            persist_directory=self.persist_directory,
            collection_name=self.collection_name,
            embedding_function=self.embeddings
        )
        print(f"✅ 新的向量数据库创建成功，集合: {self.collection_name}")

    def add_documents(self, documents: List[Document], batch_size: int = 100):
        """
        将文档添加到向量数据库

        参数:
            documents: Document对象列表
            batch_size: 批量添加的大小
        """
        if not documents:
            print("⚠️ 没有文档可添加")
            return

        print(f"开始添加 {len(documents)} 个文档到向量数据库...")

        # 分批添加，避免内存不足
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            self.vector_store.add_documents(batch)
            print(f"  已添加批次 {i // batch_size + 1}/{(len(documents) - 1) // batch_size + 1}: "
                  f"{i + 1}-{min(i + batch_size, len(documents))} 个文档")
        try:
            # 尝试调用persist()，如果不存在则跳过
            if hasattr(self.vector_store, 'persist'):
                self.vector_store.persist()
                print("✅ 数据已持久化到磁盘")
            else:
                # 新版Chroma可能自动持久化
                print("ℹ️  新版Chroma，数据自动持久化")
        except Exception as e:
            print(f"ℹ️  持久化时出现警告（可忽略）: {e}")

        print(f"✅ 成功添加 {len(documents)} 个文档到向量数据库")


    def similarity_search(self, query: str, k: int = 4) -> List[Document]:
        """
        相似度搜索

        参数:
            query: 查询文本
            k: 返回最相似的k个结果

        返回:
            最相似的文档列表
        """
        if not self.vector_store:
            raise ValueError("向量数据库未初始化")

        print(f"执行相似度搜索: '{query}'")
        results = self.vector_store.similarity_search(query, k=k)
        print(f"找到 {len(results)} 个相关文档")
        return results

    def similarity_search_with_score(self, query: str, k: int = 4):
        """
        相似度搜索（带分数）

        参数:
            query: 查询文本
            k: 返回最相似的k个结果

        返回:
            (文档, 相似度分数) 的列表
        """
        if not self.vector_store:
            raise ValueError("向量数据库未初始化")

        print(f"执行带分数的相似度搜索: '{query}'")
        results = self.vector_store.similarity_search_with_score(query, k=k)

        for i, (doc, score) in enumerate(results):
            print(f"  结果 {i + 1}: 分数={score:.3f}, 内容={doc.page_content[:80]}...")

        return results

    def get_collection_info(self) -> dict:
        """获取集合信息"""
        if not self.vector_store:
            return {"error": "向量数据库未初始化"}

        try:
            # 获取集合中的文档数量
            count = self.vector_store._collection.count()
            return {
                "collection_name": self.collection_name,
                "document_count": count,
                "persist_directory": self.persist_directory,
                "embedding_model": "BAAI/bge-small-zh-v1.5"
            }
        except Exception as e:
            return {"error": str(e)}

    def clear_collection(self):
        """清空集合"""
        if not self.vector_store:
            print("向量数据库未初始化")
            return

        confirmation = input("⚠️  确定要清空向量数据库吗？这将删除所有数据！(输入'y'确认): ")
        if confirmation.lower() == 'y':
            # 删除持久化目录
            import shutil
            if os.path.exists(self.persist_directory):
                shutil.rmtree(self.persist_directory)
                print(f"已删除目录: {self.persist_directory}")

            # 重新创建向量数据库
            self._create_new_vector_store()
            print("✅ 向量数据库已清空")
        else:
            print("操作已取消")


def test_vector_store():
    """测试向量数据库功能"""
    print("=" * 60)
    print("测试向量数据库功能")
    print("=" * 60)

    # 1. 初始化管理器
    print("\n1. 初始化向量数据库管理器...")
    vector_manager = VectorStoreManager()

    # 2. 获取集合信息
    print("\n2. 获取向量数据库信息...")
    info = vector_manager.get_collection_info()
    if "error" in info:
        print(f"  错误: {info['error']}")
    else:
        print(f"  集合名称: {info['collection_name']}")
        print(f"  文档数量: {info['document_count']}")
        print(f"  存储目录: {info['persist_directory']}")
        print(f"  嵌入模型: {info['embedding_model']}")

    # 3. 创建测试文档
    print("\n3. 创建测试文档...")
    from langchain_core.documents import Document

    test_documents = [
        Document(
            page_content="人工智能是模拟人类智能的计算机系统。",
            metadata={"source": "test", "page": 1, "category": "定义"}
        ),
        Document(
            page_content="机器学习是人工智能的一个分支，让计算机从数据中学习。",
            metadata={"source": "test", "page": 2, "category": "技术"}
        ),
        Document(
            page_content="深度学习是机器学习的一种，使用神经网络模拟人脑。",
            metadata={"source": "test", "page": 3, "category": "技术"}
        ),
        Document(
            page_content="自然语言处理是人工智能的重要应用领域。",
            metadata={"source": "test", "page": 4, "category": "应用"}
        ),
        Document(
            page_content="计算机视觉让计算机能够理解和解释视觉信息。",
            metadata={"source": "test", "page": 5, "category": "应用"}
        )
    ]

    # 4. 添加文档到向量数据库
    print("\n4. 添加测试文档到向量数据库...")
    vector_manager.add_documents(test_documents)

    # 5. 测试相似度搜索
    print("\n5. 测试相似度搜索...")
    query = "什么是机器学习？"
    print(f"  查询: '{query}'")
    results = vector_manager.similarity_search(query, k=2)

    for i, doc in enumerate(results):
        print(f"\n  结果 {i + 1}:")
        print(f"    内容: {doc.page_content}")
        print(f"    元数据: {doc.metadata}")

    # 6. 测试带分数的搜索
    print("\n6. 测试带分数的相似度搜索...")
    results_with_score = vector_manager.similarity_search_with_score("神经网络", k=3)

    # 7. 再次获取集合信息
    print("\n7. 更新后的向量数据库信息...")
    info = vector_manager.get_collection_info()
    print(f"  文档数量: {info['document_count']}")

    print("\n" + "=" * 60)
    print("✅ 向量数据库测试完成！")
    print("=" * 60)

    return vector_manager


if __name__ == "__main__":
    # 运行测试
    test_vector_store()