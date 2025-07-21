#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@File    :  test_book_sync_query.py
@Time    :  2025/07/07 13:55:49
@Author  :  XY 
@Version :  1.0
@Desc    :  拿《小王子》这本书的txt文件进行测试, 在test_book_demo.py基础上, 将query模块改为同步写法

source activate
conda activate ai-dev
cd LightRAG
set PYTHONPATH=.
python tests/2_test_book_sync_query.py
'''


import os
import asyncio
from lightrag import LightRAG, QueryParam
from lightrag.llm.openai import openai_complete_if_cache
from lightrag.llm.ollama import ollama_embed
from lightrag.utils import EmbeddingFunc
from lightrag.kg.shared_storage import initialize_pipeline_status
from dotenv import load_dotenv
from generate_lr_graph import gen_lr_graph


load_dotenv(dotenv_path=".env", override=False)

WORKING_DIR = "./inputs/book"


# ========== 异步部分：初始化 RAG 实例 ==========
async def llm_model_func(
    prompt, system_prompt=None, history_messages=[], keyword_extraction=False, **kwargs
) -> str:
    return await openai_complete_if_cache(
        os.getenv("LLM_MODEL", "deepseek-chat"),
        prompt,
        system_prompt=system_prompt,
        history_messages=history_messages,
        api_key=os.getenv("LLM_BINDING_API_KEY") or os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("LLM_BINDING_HOST", "https://api.deepseek.com"),
        **kwargs,
    )

async def async_initialize_rag():
    # Clear old data files
    files_to_delete = [
        "graph_chunk_entity_relation.graphml",
        "kv_store_doc_status.json",
        "kv_store_full_docs.json",
        "kv_store_text_chunks.json",
        "vdb_chunks.json",
        "vdb_entities.json",
        "vdb_relationships.json",
    ]

    for file in files_to_delete:
        file_path = os.path.join(WORKING_DIR, file)
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Deleting old file:: {file_path}")

    rag = LightRAG(
        working_dir=WORKING_DIR,
        llm_model_func=llm_model_func,
        # chunk_token_size=256,
        # chunk_overlap_token_size=32,
        embedding_func=EmbeddingFunc(
            embedding_dim=int(os.getenv("EMBEDDING_DIM", "1024")),
            max_token_size=int(os.getenv("MAX_EMBED_TOKENS", "8192")),
            func=lambda texts: ollama_embed(
                texts,
                embed_model=os.getenv("EMBEDDING_MODEL", "bge-m3:latest"),
                host=os.getenv("EMBEDDING_BINDING_HOST", "http://localhost:11434"),
            ),
        ),
    )
    await rag.initialize_storages()
    await initialize_pipeline_status()
    return rag

def get_initialized_rag():
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(async_initialize_rag())

# ========== 同步部分：插入 & 查询 ==========
def main():
    try:
        # 初始化 RAG（同步接口）
        rag = get_initialized_rag()

        # 插入文本
        with open(os.path.join(WORKING_DIR, "小王子.txt"), "r", encoding="utf-8") as f:
            text = f.read()
        rag.insert(text)

        # 定义查询内容
        query = "小王子让作者（我）给他画什么?"

        # 多种模式查询（同步调用）
        for mode in ["naive", "local", "global", "hybrid"]:
            print(f"\n=====================")
            print(f"Query mode: {mode}")
            print("=====================")
            response = rag.query(query, param=QueryParam(mode=mode)) # type: ignore
            print(f"response: \n{response}")

        # 生成知识图谱html
        graphml_path = os.path.join(WORKING_DIR, "graph_chunk_entity_relation.graphml")
        save_path = os.path.join(WORKING_DIR, "book_knowledge_graph.html")
        if os.path.exists(graphml_path):
            gen_lr_graph(graphml_path, save_path)
            print(f"知识图谱已生成: {save_path}")
        else:
            print("未找到graphml文件，无法生成知识图谱。")

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()