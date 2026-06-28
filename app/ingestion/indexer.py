"""
indexer.py - 切块 + 写入 Qdrant
"""
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from app.core.config import (
    QDRANT_PATH, QDRANT_COLLECTION,
    EMBEDDING_MODEL,
    CHUNK_SIZE, CHUNK_OVERLAP,
)


def build_index(docs: list[dict]) -> QdrantVectorStore:
    """
    接收 loader 返回的文档列表，切块后写入 Qdrant
    返回 vectorstore 供 searcher 使用
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

    # 切块
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
