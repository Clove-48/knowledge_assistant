# document_processor.py
# 文档加载与处理模块

import os
from typing import List
from langchain_community.document_loaders import (
    PyPDFLoader,  # PDF加载器
    TextLoader,  # 文本加载器
)  # 移除UnstructuredMarkdownLoader，使用TextLoader处理Markdown文件
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document


class DocumentProcessor:
    """文档处理器：支持多种格式的文档加载和分割"""

    def __init__(self, chunk_size=500, chunk_overlap=50):
        """
        初始化文档处理器

        参数:
            chunk_size: 每个文本块的大小（字符数）
            chunk_overlap: 文本块之间的重叠字符数（保持上下文连贯）
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # 初始化文本分割器（针对中文优化）
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""],  # 中文标点分割
            length_function=len,
        )

    # 在DocumentProcessor类的load_document方法中添加更多格式支持
    def load_document(self, file_path: str) -> List[Document]:
        """根据文件扩展名自动选择合适的加载器加载文档"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        # 根据文件扩展名选择加载器
        file_ext = os.path.splitext(file_path)[1].lower()

        loader_map = {
            '.pdf': PyPDFLoader,
            '.txt': TextLoader,
            '.md': TextLoader,  # 使用TextLoader处理Markdown文件
            # '.html': UnstructuredHTMLLoader,  # 需要安装 beautifulsoup4
            # '.docx': UnstructuredWordDocumentLoader,  # 需要安装 python-docx
            # '.pptx': UnstructuredPowerPointLoader,  # 需要安装 python-pptx
        }

        if file_ext in loader_map:
            loader_class = loader_map[file_ext]

            # 特殊处理：不同加载器可能需要不同的参数
            if file_ext in ['.txt', '.md']:
                loader = loader_class(file_path, encoding='utf-8')
            else:
                loader = loader_class(file_path)

            print(f"正在加载文档: {os.path.basename(file_path)}")
            documents = loader.load()
            print(f"文档加载完成，共 {len(documents)} 页/段落")

            # 为文档添加正确的元数据，包括源文件名
            for i, doc in enumerate(documents):
                # 确保元数据存在
                if not doc.metadata:
                    doc.metadata = {}
                # 设置源文件名
                doc.metadata['source'] = os.path.basename(file_path)
                # 设置页码或段落编号
                doc.metadata['page'] = i + 1

            return documents
        else:
            supported = ', '.join(loader_map.keys())
            raise ValueError(f"不支持的文件格式: {file_ext}。支持格式: {supported}")

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        将文档分割成小块

        参数:
            documents: Document对象列表

        返回:
            分割后的Document对象列表
        """
        if not documents:
            return []

        print(f"开始分割文档，块大小: {self.chunk_size}，重叠: {self.chunk_overlap}")
        chunks = self.text_splitter.split_documents(documents)
        print(f"文档分割完成，共 {len(chunks)} 个文本块")

        # 打印前3个块的预览
        for i, chunk in enumerate(chunks[:3]):
            print(f"\n--- 文本块 {i + 1} 预览 (前100字符) ---")
            print(chunk.page_content[:100] + "...")

        return chunks

    def process_folder(self, folder_path: str) -> List[Document]:
        """
        处理文件夹中的所有支持格式的文档

        参数:
            folder_path: 文件夹路径

        返回:
            所有文档分割后的文本块列表
        """
        if not os.path.exists(folder_path):
            raise FileNotFoundError(f"文件夹不存在: {folder_path}")

        all_chunks = []
        supported_extensions = {'.pdf', '.txt', '.md'}

        # 遍历文件夹中的所有文件
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            file_ext = os.path.splitext(filename)[1].lower()

            if os.path.isfile(file_path) and file_ext in supported_extensions:
                try:
                    # 加载文档
                    documents = self.load_document(file_path)

                    # 分割文档
                    chunks = self.split_documents(documents)
                    all_chunks.extend(chunks)

                    print(f"✓ 已处理: {filename} -> 生成 {len(chunks)} 个文本块\n")

                except Exception as e:
                    print(f"✗ 处理文件 {filename} 时出错: {e}\n")

        print(f"文件夹处理完成，总共生成 {len(all_chunks)} 个文本块")
        return all_chunks


# 测试函数
def test_document_processor():
    """测试文档处理器"""
    # 创建测试文档文件夹
    test_docs_dir = "test_documents"
    os.makedirs(test_docs_dir, exist_ok=True)

    # 创建测试文本文件
    test_content = """
    # AI知识库问答助手项目说明

    这是一个基于RAG（检索增强生成）技术的AI知识库问答助手。
    项目使用Python开发，结合了以下技术：

    1. LangChain - AI工作流编排框架
    2. DeepSeek API - 大语言模型接口
    3. ChromaDB - 向量数据库
    4. Sentence Transformers - 文本嵌入模型
    5. Gradio - Web交互界面

    项目功能：
    - 支持PDF、TXT、MD格式文档上传
    - 自动分割和向量化文档内容
    - 基于语义相似度的智能检索
    - 自然语言问答交互

    这是一个全免费技术栈的项目，适合学习和实践。
    """

    test_file_path = os.path.join(test_docs_dir, "project_intro.txt")
    with open(test_file_path, "w", encoding="utf-8") as f:
        f.write(test_content)

    print("=" * 50)
    print("测试文档处理器...")
    print("=" * 50)

    # 初始化处理器
    processor = DocumentProcessor(chunk_size=300, chunk_overlap=30)

    try:
        # 测试单个文件处理
        print("\n1. 测试单个文件处理:")
        documents = processor.load_document(test_file_path)
        chunks = processor.split_documents(documents)

        # 测试文件夹处理
        print("\n" + "=" * 50)
        print("2. 测试文件夹处理:")
        all_chunks = processor.process_folder(test_docs_dir)

        print("\n" + "=" * 50)
        print("✅ 文档处理器测试通过!")
        return True

    except Exception as e:
        print(f"\n❌ 文档处理器测试失败: {e}")
        return False


if __name__ == "__main__":
    # 运行测试
    test_document_processor()