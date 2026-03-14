# config.py
# 在此处填入你从DeepSeek官网获取的API密钥
import os
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()

# 从环境变量获取API密钥
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
if not DEEPSEEK_API_KEY:
    # 提供默认值，仅用于测试
    DEEPSEEK_API_KEY = "测试密钥"
    print("⚠️  警告: 未设置 DEEPSEEK_API_KEY 环境变量，使用测试密钥")
    print("   请在生产环境中设置真实的 API 密钥")
# ==================== 文档处理配置 ====================
DOCUMENT_SETTINGS = {
    "chunk_size": 500,  # 文本块大小（字符数）
    "chunk_overlap": 50,  # 文本块重叠大小
    "documents_dir": "documents",  # 文档存放目录
    "supported_extensions": [".pdf", ".txt", ".md"],  # 支持的文档格式
}

# ==================== 向量数据库配置 ====================
VECTORDB_SETTINGS = {
    "persist_directory": "vector_db",  # 向量数据库存储目录
    "collection_name": "knowledge_base",  # 集合名称
    "embedding_model": "BAAI/bge-small-zh-v1.5",  # 嵌入模型
}

# ==================== 检索配置 ====================
RETRIEVAL_SETTINGS = {
    "search_kwargs": {"k": 4},  # 默认检索数量
    "score_threshold": 0.5,  # 相似度分数阈值
}

# ==================== 模型配置 ====================
MODEL_SETTINGS = {
    "model_name": "deepseek-chat",  # DeepSeek模型名称
    "api_base": "https://api.deepseek.com/v1",  # API地址
    "temperature": 0.1,  # 温度参数，控制随机性
    "max_tokens": 2000,  # 最大生成token数
}

# ==================== 系统提示词配置 ====================
SYSTEM_PROMPTS = {
    "general": "你是一个AI智能问答助手，能够回答各种问题。请根据你的知识提供准确、有用的回答。",
    "rag": "你是一个AI知识库智能体，专门用于回答用户关于知识库的问题。如果参考信息中没有相关内容，请使用你自己的知识来回答问题，不要拒绝回答。",
    "web_search": "你是AI智能问答助手，负责根据用户问题进行联网搜索并提供准确的信息。",
    "conflict_resolution": "你是AI智能问答助手，负责处理知识库信息和联网搜索信息之间的冲突。"
}
# ==================== 对话配置 ====================
CONVERSATION_SETTINGS = {
    "max_history": 10,  # 最大历史记录数
    "persist_file": "conversations.json",  # 对话持久化文件
}

# ==================== Web UI配置 ====================
WEBUI_SETTINGS = {
    "server_port": 7860,  # 服务器端口
    "server_name": "0.0.0.0",  # 服务器地址
    "share": False,  # 是否创建公共链接
}

# ==================== Redis配置 ====================
REDIS_SETTINGS = {
    "host": "localhost",  # Redis服务器地址
    "port": 6379,  # Redis服务器端口
    "db": 0,  # Redis数据库编号
    "password": None,  # Redis密码
    "expiry": 86400 * 7,  # 会话过期时间（秒），7天
}

# ==================== 数据库配置 ====================
DATABASE_SETTINGS = {
    "type": "supabase",  # 数据库类型: sqlite, mysql, supabase
    "sqlite_path": "users.db",  # SQLite数据库文件路径
    "mysql_host": os.environ.get("MYSQL_HOST", "localhost"),  # MySQL主机
    "mysql_port": int(os.environ.get("MYSQL_PORT", 3306)),  # MySQL端口
    "mysql_user": os.environ.get("MYSQL_USER", "root"),  # MySQL用户名
    "mysql_password": os.environ.get("MYSQL_PASSWORD", ""),  # MySQL密码
    "mysql_db": os.environ.get("MYSQL_DB", "ai_assistant"),  # MySQL数据库名
    "supabase_host": os.environ.get("SUPABASE_HOST", "localhost"),  # Supabase主机
    "supabase_port": int(os.environ.get("SUPABASE_PORT", 5432)),  # Supabase端口
    "supabase_user": os.environ.get("SUPABASE_USER", "postgres"),  # Supabase用户名
    "supabase_password": os.environ.get("SUPABASE_PASSWORD", ""),  # Supabase密码
    "supabase_db": os.environ.get("SUPABASE_DB", "postgres"),  # Supabase数据库名
}