#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@File    :  test_sql_pf_sync_query.py
@Time    :  2025/07/07 13:55:49
@Author  :  XY 
@Version :  1.0
@Desc    :  从sql process func文件中提取出表血缘关系

source activate
conda activate ai-dev
cd LightRAG
set PYTHONPATH=.
python tests/3_test_sql_pf_sync_query.py
'''


import os
import asyncio
import numpy as np

from lightrag import LightRAG, QueryParam
from lightrag.llm.openai import openai_complete_if_cache, openai_embed
from lightrag.llm.ollama import ollama_embed
from lightrag.utils import EmbeddingFunc
from lightrag.kg.shared_storage import initialize_pipeline_status
from dotenv import load_dotenv

from generate_lr_graph import gen_lr_graph


load_dotenv(dotenv_path=".env", override=True)

# 查看 load_dotenv 加载的环境变量
print("已加载的环境变量：")
for key in [
    "LLM_MODEL",
    "LLM_BINDING_API_KEY",
    "LLM_BINDING_HOST",
    "EMBEDDING_MODEL",
    "EMBEDDING_BINDING_API_KEY",
    "EMBEDDING_BINDING_HOST"
]:
    print(f"{key}: {os.getenv(key)}")


WORKING_DIR = "./inputs/sql_process_func/"


async def print_stream(stream):
    async for chunk in stream:
        if chunk:
            print(chunk, end="", flush=True)

 
# ========== 异步部分：初始化 RAG 实例 ==========
async def llm_model_func(
    prompt, system_prompt=None, history_messages=[], keyword_extraction=False, **kwargs
) -> str:
    return await openai_complete_if_cache(
        model=os.getenv("LLM_MODEL"), # type: ignore
        prompt=prompt,
        system_prompt=system_prompt,
        history_messages=history_messages,
        api_key=os.getenv("LLM_BINDING_API_KEY"),
        base_url=os.getenv("LLM_BINDING_HOST"),

        # 若是使用QWen3系列模型, 必须配置
        # openai库 -> completions.py -> create函数 -> make_request_options函数
        **{"extra_body": {"enable_thinking": False}}
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
        embedding_func=EmbeddingFunc(
            embedding_dim=int(os.getenv("EMBEDDING_DIM", "1024")),
            max_token_size=int(os.getenv("MAX_EMBED_TOKENS", "8192")),
            func=defined_embedding_func
        ),
        embedding_batch_num=10,
        # vector_storage="QdrantVectorDBStorage",
        # 附加参数
        addon_params={  
            "entity_types": ["table", "field"],  
            "language": "Chinese"
        }
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
        from pathlib import Path
        for table_dir in Path(WORKING_DIR).glob("table_dwd"):
            if table_dir.is_dir():
                print(f"处理目录: {table_dir}")
                for file in table_dir.iterdir():
                    if file.is_file():
                        with open(file, "r", encoding="utf-8") as f:
                            text = f.read()
                        print(f"文件{file}插入完毕.")
                        rag.insert(text)
        print("知识库文档内容全部插入完毕.")

        # 定义查询内容
        query = "dwd_overspeed_info表从那几个表得来? 回复内容仅包含对应的子表名称, 不要包含其他内容"

        # 多种模式查询（同步调用）
        # query_mode = ["naive", "local", "global", "hybrid"]
        query_mode = ["hybrid"]
        for mode in query_mode:
            print(f"\n=====================")
            print(f"Query mode: {mode}")
            print("=====================")
            resp = rag.query(query, param=QueryParam(mode=mode, stream=False)) # type: ignore
            print(f"response: \n{resp}")

            # 可以设置enable_thinking: True
            # import inspect
            # resp = rag.query(query, param=QueryParam(mode=mode, stream=True)) # type: ignore
            # if inspect.isasyncgen(resp):
                # asyncio.run(print_stream(resp))
            # else:
                # print(resp)
        
        # # 生成html
        # graphml_path = os.path.join(WORKING_DIR, "graph_chunk_entity_relation.graphml")
        # save_path = os.path.join(WORKING_DIR, "book_knowledge_graph.html")
        # if os.path.exists(graphml_path):
        #     gen_lr_graph(graphml_path, save_path)
        #     print(f"知识图谱已生成: {save_path}")
        # else:
        #     print("未找到graphml文件，无法生成知识图谱。")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
