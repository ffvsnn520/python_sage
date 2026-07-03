"""
indexer.py - 切块 + 写入 Qdrant
"""
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, FieldCondition, Filter, MatchValue, VectorParams

from app.core.config import (
    QDRANT_PATH, QDRANT_COLLECTION,
    EMBEDDING_MODEL,
    CHUNK_SIZE, CHUNK_OVERLAP,
)


def split_docs(docs: list[dict]) -> list[Document]:
    """
    把 loader 读出来的文档切成 chunks。

    这个函数只负责切块，不负责写 Qdrant。
    build_index、update_index、load_existing_index 都复用它，
    这样三条链路使用同一套 chunk 规则。
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", "。", "，", " "],
    )

    all_chunks = []
    for doc in docs:
        chunks = splitter.create_documents(
            texts=[doc["content"]],
            metadatas=[{"source": doc["filename"]}],
        )
        all_chunks.extend(chunks)
        print(f"  {doc['filename']} → {len(chunks)} 个 chunk")

    return all_chunks


def build_index(docs: list[dict]) -> QdrantVectorStore:
    """
    全量重建索引。

    使用场景：
    - 第一次初始化知识库
    - 想彻底清空并重建 Qdrant

    注意：这个函数会删除整个 collection，线上服务启动时不要调用它。
    """
    print(f"\n[Indexer] 初始化 Embedding 模型: {EMBEDDING_MODEL}")
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)


    print(f"[Indexer] 连接本地 Qdrant: {QDRANT_PATH}")
    client = QdrantClient(path=QDRANT_PATH)

    # 每次重建，保证数据干净
    collections = [c.name for c in client.get_collections().collections]

    if QDRANT_COLLECTION in collections:
        print(f"[Indexer] 集合已存在，清空重建: {QDRANT_COLLECTION}")
        client.delete_collection(QDRANT_COLLECTION)

    client.create_collection(
        collection_name=QDRANT_COLLECTION,
        vectors_config=VectorParams(size=512, distance=Distance.COSINE),
    )

    all_chunks = split_docs(docs)
    print(f"\n[Indexer] 总 chunk 数: {len(all_chunks)}")


    # 写入向量库
    vectorstore = QdrantVectorStore(
        client=client,
        collection_name=QDRANT_COLLECTION,
        embedding=embeddings,
    )
    vectorstore.add_documents(all_chunks)
    print(f"[Indexer] 写入完成 ✓")

    return vectorstore, all_chunks


def update_index(docs: list[dict]) -> tuple[QdrantVectorStore, list[Document]]:
    """
    增量更新 Qdrant：
    1. 按 metadata.source 删除变更文档的旧 chunks
    2. 重新切块
    3. 写入新 chunks

    使用场景：
    - scripts/ingest_incremental.py 检测到某些 md 文件变化后调用
    - 不删除整个 collection，只替换变化文档对应的 chunks
    """
    print(f"\n[Indexer] 初始化 Embedding 模型: {EMBEDDING_MODEL}")
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

    print(f"[Indexer] 连接本地 Qdrant: {QDRANT_PATH}")
    client = QdrantClient(path=QDRANT_PATH)

    collections = [c.name for c in client.get_collections().collections]
    if QDRANT_COLLECTION not in collections:
        print(f"[Indexer] 集合不存在，先创建: {QDRANT_COLLECTION}")
        client.create_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=VectorParams(size=512, distance=Distance.COSINE),
        )

    for doc in docs:
        filename = doc["filename"]
        print(f"[Indexer] 删除旧 chunks: {filename}")
        client.delete(
            collection_name=QDRANT_COLLECTION,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="metadata.source",
                        match=MatchValue(value=filename),
                    )
                ]
            ),
        )

    all_chunks = split_docs(docs)
    print(f"\n[Indexer] 增量 chunk 数: {len(all_chunks)}")

    vectorstore = QdrantVectorStore(
        client=client,
        collection_name=QDRANT_COLLECTION,
        embedding=embeddings,
    )

    if all_chunks:
        vectorstore.add_documents(all_chunks)

    print("[Indexer] 增量写入完成 ✓")

    return vectorstore, all_chunks


def load_existing_index(docs: list[dict]) -> tuple[QdrantVectorStore, list[Document]]:
    """
    加载已经存在的 Qdrant 索引，不做写入。

    使用场景：
    - FastAPI 服务启动

    为什么还要传 docs？
    - Qdrant 负责向量检索，数据已经由离线脚本写入
    - Searcher 里的 BM25 需要内存里的 all_chunks
    - 所以这里只把 docs 切块给 BM25 用，不重新写 Qdrant
    """
    print(f"\n[Indexer] 初始化 Embedding 模型: {EMBEDDING_MODEL}")
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

    print(f"[Indexer] 加载本地 Qdrant: {QDRANT_PATH}")
    client = QdrantClient(path=QDRANT_PATH)

    collections = [c.name for c in client.get_collections().collections]
    if QDRANT_COLLECTION not in collections:
        raise RuntimeError(
            f"Qdrant collection 不存在: {QDRANT_COLLECTION}，请先运行 scripts/ingest.py 完成初始化"
        )

    vectorstore = QdrantVectorStore(
        client=client,
        collection_name=QDRANT_COLLECTION,
        embedding=embeddings,
    )

    all_chunks = split_docs(docs)
    print(f"\n[Indexer] 已加载已有索引，BM25 chunk 数: {len(all_chunks)}")

    return vectorstore, all_chunks
