#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@File    :  1_test_book_demo.py
@Time    :  2025/07/07 10:51:12
@Author  :  XY 
@Version :  1.0
@Desc    :  拿《小王子》这本书的txt文件进行测试

source activate
conda activate ai-dev
cd LightRAG
set PYTHONPATH=.
python tests/1_test_book_demo.py
'''


import os
import asyncio
import inspect
from lightrag import LightRAG, QueryParam
from lightrag.llm.openai import openai_complete_if_cache, openai_embed
from lightrag.llm.ollama import ollama_embed
from lightrag.utils import EmbeddingFunc
from lightrag.kg.shared_storage import initialize_pipeline_status

from dotenv import load_dotenv
from generate_lr_graph import gen_lr_graph


load_dotenv(dotenv_path=".env", override=True)

WORKING_DIR = "./inputs/book"


async def llm_model_func(
    prompt, system_prompt=None, history_messages=[], keyword_extraction=False, **kwargs
) -> str:
    return await openai_complete_if_cache(
        model=os.getenv("LLM_MODEL", "deepseek-chat"),
        prompt=prompt,
        system_prompt=system_prompt,
        history_messages=history_messages,
        api_key=os.getenv("LLM_BINDING_API_KEY") or os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("LLM_BINDING_HOST", "https://api.deepseek.com"),
        **kwargs,
    )


# 定义嵌入函数
async def defined_embedding_func(texts: list[str]):
    if os.getenv("EMBEDDING_BINDING") == "openai":
        return await openai_embed(
            texts,
            model=os.getenv("EMBEDDING_MODEL"),
            api_key=os.getenv("EMBEDDING_BINDING_API_KEY"),
            base_url=os.getenv("EMBEDDING_BINDING_HOST")
        )
    elif os.getenv("EMBEDDING_BINDING") == "ollama":
        return await ollama_embed(
            texts,
            embed_model=os.getenv("EMBEDDING_MODEL", "bge-m3:latest"),
            host=os.getenv("EMBEDDING_BINDING_HOST", "http://localhost:11434"),
        )
    else:
        raise ValueError(f"Unsupported embedding binding: {os.getenv('EMBEDDING_BINDING')}")


async def print_stream(stream):
    async for chunk in stream:
        if chunk:
            print(chunk, end="", flush=True)


async def initialize_rag():
    rag = LightRAG(
        working_dir=WORKING_DIR,
        llm_model_func=llm_model_func,
        embedding_func=EmbeddingFunc(
            embedding_dim=int(os.getenv("EMBEDDING_DIM", "1024")),
            max_token_size=int(os.getenv("MAX_EMBED_TOKENS", "8192")),
            func=defined_embedding_func,
        ),
    )

    await rag.initialize_storages()
    await initialize_pipeline_status()

    return rag


async def main():
    try:
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

        # Initialize RAG instance
        rag = await initialize_rag()
        
        # 需要读取的目标文档
        with open(os.path.join(WORKING_DIR, "小王子.txt"), "r", encoding="utf-8") as f:
            await rag.ainsert(f.read())
        print("知识库文档内容插入完毕")

        query = "小王子让作者（我）给他画什么?"  # "What are the top themes in this story?"

        # Perform naive search
        for mode in ["naive", "local", "global", "hybrid"]:
            print("\n=====================")
            print(f"Query mode: {mode}")
            resp = await rag.aquery(
                query=query,
                param=QueryParam(mode=f"{mode}", stream=True), # type: ignore
            )
            if inspect.isasyncgen(resp):
                await print_stream(resp)
            else:
                print(resp)

        graphml_path = os.path.join(WORKING_DIR, "graph_chunk_entity_relation.graphml")
        save_path = os.path.join(WORKING_DIR, "book_knowledge_graph.html")
        if os.path.exists(graphml_path):
            gen_lr_graph(graphml_path, save_path)
            print(f"知识图谱已生成: {save_path}")
        else:
            print("未找到graphml文件，无法生成知识图谱。")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if rag:
            await rag.finalize_storages()


if __name__ == "__main__":
    asyncio.run(main())

    print("\nDone!")
