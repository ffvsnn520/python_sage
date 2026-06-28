"""
searcher.py - 混合检索：向量 + BM25 + Rerank

流程：
  1. 向量检索：把 query 转成向量，从 Qdrant 里找最相似的 chunk
  2. BM25 检索：关键词匹配，弥补向量检索对专业术语不敏感的缺陷
  3. 合并去重：两路结果合并，去掉重复的 chunk
  4. CrossEncoder Rerank：把 query 和每个候选 chunk 拼成一对，
     让模型直接判断"这个 chunk 能回答这个问题吗"，输出相关性分数
  5. 按分数排序，过滤低分，返回 Top K
"""
import jieba
from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder
from langchain_qdrant import QdrantVectorStore

from app.core.config import (
    RERANKER_MODEL,
    RETRIEVAL_TOP_K,
    RERANK_TOP_K,
    RERANK_THRESHOLD,
)


class Searcher:
    def __init__(self, vectorstore: QdrantVectorStore, all_chunks: list):
        """
        vectorstore: 已写入数据的 Qdrant 向量库实例
        all_chunks:  所有 chunk 的原始列表，BM25 需要在这上面建索引
        """
        self.vectorstore = vectorstore

        # CrossEncoder：接收 [query, chunk] 对，直接输出相关性分数
        # 比向量余弦相似度更准确，但每对都要单独推理，所以只用于精排少量候选
        print(f"\n[Searcher] 初始化 Reranker: {RERANKER_MODEL}")
        self.reranker = CrossEncoder(RERANKER_MODEL)

        # BM25：基于词频的关键词检索，对专业报错信息（如 SQLSTATE、HY000）命中率高
        # 需要先对所有 chunk 分词，建立倒排索引
        print(f"[Searcher] 构建 BM25 索引 ({len(all_chunks)} 个 chunk)")
        self.all_chunks = all_chunks

        tokenized = [list(jieba.cut(c.page_content)) for c in all_chunks]
        self.bm25 = BM25Okapi(tokenized)

    def search(self, query: str) -> list[dict]:
        """
        混合检索入口

        返回格式：
        [
            {"content": "chunk内容", "source": "来源文件名", "score": 0.85},
            ...
        ]
        """
        # --- 第一路：向量检索 ---
        # 把 query 转成向量，在 Qdrant 里找余弦相似度最高的 chunk
        vector_results = self.vectorstore.similarity_search(query, k=RETRIEVAL_TOP_K)

        # --- 第二路：BM25 关键词检索 ---
        # 对 query 分词，计算每个 chunk 的 BM25 得分
        # 优势：对"PDO Connection timed out"这类专业词组命中更准
        tokens = list(jieba.cut(query))
        bm25_scores = self.bm25.get_scores(tokens)
        # 按得分排序，取前 K 个，过滤得分为0的（完全没匹配到关键词）
        bm25_top = sorted(enumerate(bm25_scores), key=lambda x: x[1], reverse=True)[:RETRIEVAL_TOP_K]
        bm25_results = [self.all_chunks[i] for i, score in bm25_top if score > 0]

        # --- 合并去重 ---
        # 两路结果可能重叠，用 page_content 做去重 key
        seen = set()
        combined = []
        for doc in vector_results + bm25_results:
            if doc.page_content not in seen:
                seen.add(doc.page_content)
                combined.append(doc)

        if not combined:
            return []

        # --- CrossEncoder Rerank ---
        # 构造 [query, chunk] 对列表，批量打分
        # CrossEncoder 会把这两段文本拼起来，理解它们之间的语义关联
        pairs = [[query, doc.page_content] for doc in combined]
        rerank_scores = self.reranker.predict(pairs)

        # 按 rerank 分数从高到低排序
        ranked = sorted(zip(rerank_scores, combined), reverse=True)

        # 取 Top K，过滤低于阈值的结果（相关性太低的直接丢掉）
        results = []
        for score, doc in ranked[:RERANK_TOP_K]:
            if score < RERANK_THRESHOLD:
                continue
            results.append({
                "content": doc.page_content,
                "source": doc.metadata.get("source", "unknown"),
                "score": round(float(score), 4),
            })

        return results
