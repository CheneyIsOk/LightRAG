from __future__ import annotations
from typing import Any


PROMPTS: dict[str, Any] = {}

PROMPTS["DEFAULT_LANGUAGE"] = "Chinese"
PROMPTS["DEFAULT_TUPLE_DELIMITER"] = "<|>"
PROMPTS["DEFAULT_RECORD_DELIMITER"] = "##"
PROMPTS["DEFAULT_COMPLETION_DELIMITER"] = "<|COMPLETE|>"

PROMPTS["DEFAULT_ENTITY_TYPES"] = ["table", "field"]

PROMPTS["DEFAULT_USER_PROMPT"] = "n/a"


PROMPTS["entity_extraction"] = """---任务目标---
输入是 PostgreSQL SQL语句（文本内容包含 INSERT INTO 或 CREATE TABLE 两类），抽取其中所有实体（表、字段）及它们的关系。
1. INSERT INTO: 抽取表之间关系（不记录字段）；
2. CREATE TABLE: 抽取表和字段，并建立它们之间关系。

---注意事项---
1. 所有实体名仅来源于原始 SQL；
2. 不保留中间表别名、字段别名。

---步骤---
1. 识别所有实体。对于每个识别出的实体，提取以下信息：
   • entity_name: 实体名称: 表名称
   • entity_type: 包含的类型为其中之一: [table, field]
   • entity_description: 实体属性和活动的全述面描
   格式：("entity"{tuple_delimiter}<entity_name>{tuple_delimiter}<entity_type>{tuple_delimiter}<entity_description>){record_delimiter}

2. 从步骤1中识别出的实体中，识别出所有明显相关的 (source_entity, target_entity) 对。对于每对相关的实体，提取以下信息：
   • source_entity: 在步骤1中识别出的源实体名称
   • target_entity: 在步骤1中识别出的目标实体名称
   • relationship_description: 解释为什么认为源实体和目标实体彼此相关
   • relationship_strength: 表示源实体和目标实体之间关系强度的整数评分，范围为1到10
   格式：("relationship"{tuple_delimiter}<target_entity>{tuple_delimiter}<source_entity>{tuple_delimiter}<relationship_description>{tuple_delimiter}<relationship_strength>){record_delimiter}

3. 使用 {record_delimiter} 作为列表分隔符。
4. 返回输出文本的主要语言为"中文"。作为步骤1和2中识别出的所有实体和关系的单个列表。如果需要翻译，只需翻译描述部分，其余部分保持不变。
5. 当完成时，输出 {completion_delimiter}作为结束符。

######################
---案例---
######################
{examples}

######################
---真实数据---
######################
Entity_types: [{entity_type}]
Text:
{input_text}
######################
Output:
"""


PROMPTS["entity_extraction_examples"] = [
"""案例 1:
Entity_types: table
Text:
INSERT INTO table_target (
	target_date,
	company_name,
	line_code,
	line_name,
	reason_code
)
SELECT
	a.target_date,
	a.line_code,
	a.line_name,
  a.ope_real_mileage,
	b.ope_n_real_mileage
FROM (
	SELECT
		target_date,
		line_code,
		line_name,
		sum(real_mileage) ope_real_mileage
	FROM (
		SELECT
			target_date, 
			b.belonging_line_code AS line_code,
			b.belonging_line_name AS line_name,
      real_mileage
		FROM dwd_operate_vehicleusage_driverecords_d a
		LEFT JOIN (
				SELECT
					a.line_code, a.line_name, a.pid,
					b.line_code as p_line_code,
					b.line_name as p_line_name,
					COALESCE(b.line_code, a.line_code) belonging_line_code,
					COALESCE(b.line_name, a.line_name) belonging_line_name
				FROM dim_resource_line a
				LEFT JOIN dim_resource_line b
				ON a.pid = b.id
		) b
		ON a.line_code = b.line_code
	) t
	GROUP BY target_date, line_code, line_name
) a
LEFT JOIN (
	SELECT
		target_date,
		line_code, line_name,
		sum(real_mileage) ope_n_real_mileage
	FROM dwd_operate_n_vehicleusage_driverecords_d
	GROUP BY target_date, line_code, line_name
) b
ON a.target_date = b.target_date
	AND a.line_code = b.line_code
	AND a.line_name = b.line_name
######################
Output:
("entity"{tuple_delimiter}table_target{tuple_delimiter}table{tuple_delimiter}写入的目标表)
{record_delimiter}
("entity"{tuple_delimiter}dwd_operate_vehicleusage_driverecords_d{tuple_delimiter}table{tuple_delimiter}关联的主表)
{record_delimiter}
("entity"{tuple_delimiter}dim_resource_line{tuple_delimiter}table{tuple_delimiter}左关联的第二张表，同时也进行自关联)
{record_delimiter}
("entity"{tuple_delimiter}dwd_operate_n_vehicleusage_driverecords_d{tuple_delimiter}table{tuple_delimiter}左关联的表)
{record_delimiter}
("relationship"{tuple_delimiter}table_target{tuple_delimiter}dwd_operate_vehicleusage_driverecords_d{tuple_delimiter}table_target部分数据来自dwd_operate_vehicleusage_driverecords_d{tuple_delimiter}10)
{record_delimiter}
("relationship"{tuple_delimiter}table_target{tuple_delimiter}dim_resource_line{tuple_delimiter}table_target部分数据来自dim_resource_line{tuple_delimiter}10)
{record_delimiter}
("relationship"{tuple_delimiter}table_target{tuple_delimiter}dwd_operate_n_vehicleusage_driverecords_d{tuple_delimiter}table_target部分数据来自dwd_operate_n_vehicleusage_driverecords_d{tuple_delimiter}10)
{record_delimiter}
{completion_delimiter}
""",

"""案例 2:
Entity_types: table
Text:
CREATE TABLE table_a (
  "city_code" varchar(20),
  "target_date" varchar,
  "department_name" varchar(50),
)
######################
Output:
("entity"{tuple_delimiter}dwd_overspeed_info{tuple_delimiter}table{tuple_delimiter}创建的表)
{record_delimiter}
("entity"{tuple_delimiter}city_code{tuple_delimiter}field{tuple_delimiter}表字段)
{record_delimiter}
("entity"{tuple_delimiter}target_date{tuple_delimiter}field{tuple_delimiter}表字段)
{record_delimiter}
("entity"{tuple_delimiter}department_name{tuple_delimiter}field{tuple_delimiter}表字段)
{record_delimiter}
("relationship"{tuple_delimiter}dwd_overspeed_info{tuple_delimiter}city_code{tuple_delimiter}表和字段的关系{tuple_delimiter}10)
{record_delimiter}
("relationship"{tuple_delimiter}dwd_overspeed_info{tuple_delimiter}city_code{tuple_delimiter}表和字段的关系{tuple_delimiter}10)
{record_delimiter}
("relationship"{tuple_delimiter}dwd_overspeed_info{tuple_delimiter}city_code{tuple_delimiter}表和字段的关系{tuple_delimiter}10)
{record_delimiter}
{completion_delimiter}
""",
]


PROMPTS[
    "summarize_entity_descriptions"
] = """You are a helpful assistant responsible for generating a comprehensive summary of the data provided below.
Given one or two entities, and a list of descriptions, all related to the same entity or group of entities.
Please concatenate all of these into a single, comprehensive description. Make sure to include information collected from all the descriptions.
If the provided descriptions are contradictory, please resolve the contradictions and provide a single, coherent summary.
Make sure it is written in third person, and include the entity names so we the have full context.
Use {language} as output language.

#######
---Data---
Entities: {entity_name}
Description List: {description_list}
#######
Output:
"""


PROMPTS["entity_continue_extraction"] = """
MANY entities and relationships were missed in the last extraction.

---Remember Steps---

1. Identify all entities. For each identified entity, extract the following information:
- entity_name: Name of the entity, use same language as input text.
- entity_type: One of the following types: [{entity_type}]
- entity_description: Comprehensive description of the entity's attributes and activities
Format each entity as ("entity"{tuple_delimiter}<entity_name>{tuple_delimiter}<entity_type>{tuple_delimiter}<entity_description>)

2. From the entities identified in step 1, identify all pairs of (source_entity, target_entity) that are *clearly related* to each other.
For each pair of related entities, extract the following information:
- source_entity: name of the source entity, as identified in step 1
- target_entity: name of the target entity, as identified in step 1
- relationship_description: explanation as to why you think the source entity and the target entity are related to each other
- relationship_strength: a numeric score indicating strength of the relationship between the source entity and target entity
- relationship_keywords: one or more high-level key words that summarize the overarching nature of the relationship, focusing on concepts or themes rather than specific details
Format each relationship as ("relationship"{tuple_delimiter}<source_entity>{tuple_delimiter}<target_entity>{tuple_delimiter}<relationship_description>{tuple_delimiter}<relationship_keywords>{tuple_delimiter}<relationship_strength>)

3. Identify high-level key words that summarize the main concepts, themes, or topics of the entire text. These should capture the overarching ideas present in the document.
Format the content-level key words as ("content_keywords"{tuple_delimiter}<high_level_keywords>)

4. Return output in {language} as a single list of all the entities and relationships identified in steps 1 and 2. Use **{record_delimiter}** as the list delimiter.

5. When finished, output {completion_delimiter}

---Output---

Add them below using the same format:\n
""".strip()


PROMPTS["entity_if_loop_extraction"] = """
---Goal---'

It appears some entities may have still been missed.

---Output---

Answer ONLY by `YES` OR `NO` if there are still entities that need to be added.
""".strip()


PROMPTS["fail_response"] = (
    "Sorry, I'm not able to provide an answer to that question.[no-context]"
)


PROMPTS["rag_response"] = """---Role---

You are a helpful assistant responding to user query about Knowledge Graph and Document Chunks provided in JSON format below.


---Goal---

Generate a concise response based on Knowledge Base and follow Response Rules, considering both the conversation history and the current query. Summarize all information in the provided Knowledge Base, and incorporating general knowledge relevant to the Knowledge Base. Do not include information not provided by Knowledge Base.

When handling relationships with timestamps:
1. Each relationship has a "created_at" timestamp indicating when we acquired this knowledge
2. When encountering conflicting relationships, consider both the semantic content and the timestamp
3. Don't automatically prefer the most recently created relationships - use judgment based on the context
4. For time-specific queries, prioritize temporal information in the content before considering creation timestamps

---Conversation History---
{history}

---Knowledge Graph and Document Chunks---
{context_data}

---Response Rules---

- Target format and length: {response_type}
- Use markdown formatting with appropriate section headings
- Please respond in the same language as the user's question.
- Ensure the response maintains continuity with the conversation history.
- List up to 5 most important reference sources at the end under "References" section. Clearly indicating whether each source is from Knowledge Graph (KG) or Document Chunks (DC), and include the file path if available, in the following format: [KG/DC] file_path
- If you don't know the answer, just say so.
- Do not make anything up. Do not include information not provided by the Knowledge Base.
- Addtional user prompt: {user_prompt}

Response:"""


PROMPTS["keywords_extraction"] = """---Role---

You are a helpful assistant tasked with identifying both high-level and low-level keywords in the user's query and conversation history.

---Goal---

Given the query and conversation history, list both high-level and low-level keywords. High-level keywords focus on overarching concepts or themes, while low-level keywords focus on specific entities, details, or concrete terms.

---Instructions---

- Consider both the current query and relevant conversation history when extracting keywords
- Output the keywords in JSON format, it will be parsed by a JSON parser, do not add any extra content in output
- The JSON should have two keys:
  - "high_level_keywords" for overarching concepts or themes
  - "low_level_keywords" for specific entities or details

######################
---Examples---
######################
{examples}

#############################
---Real Data---
######################
Conversation History:
{history}

Current Query: {query}
######################
The `Output` should be human text, not unicode characters. Keep the same language as `Query`.
Output:

"""

PROMPTS["keywords_extraction_examples"] = [
    """Example 1:

Query: "How does international trade influence global economic stability?"
################
Output:
{
  "high_level_keywords": ["International trade", "Global economic stability", "Economic impact"],
  "low_level_keywords": ["Trade agreements", "Tariffs", "Currency exchange", "Imports", "Exports"]
}
#############################""",
    """Example 2:

Query: "What are the environmental consequences of deforestation on biodiversity?"
################
Output:
{
  "high_level_keywords": ["Environmental consequences", "Deforestation", "Biodiversity loss"],
  "low_level_keywords": ["Species extinction", "Habitat destruction", "Carbon emissions", "Rainforest", "Ecosystem"]
}
#############################""",
    """Example 3:

Query: "What is the role of education in reducing poverty?"
################
Output:
{
  "high_level_keywords": ["Education", "Poverty reduction", "Socioeconomic development"],
  "low_level_keywords": ["School access", "Literacy rates", "Job training", "Income inequality"]
}
#############################""",
]

PROMPTS["naive_rag_response"] = """---Role---

You are a helpful assistant responding to user query about Document Chunks provided provided in JSON format below.

---Goal---

Generate a concise response based on Document Chunks and follow Response Rules, considering both the conversation history and the current query. Summarize all information in the provided Document Chunks, and incorporating general knowledge relevant to the Document Chunks. Do not include information not provided by Document Chunks.

When handling content with timestamps:
1. Each piece of content has a "created_at" timestamp indicating when we acquired this knowledge
2. When encountering conflicting information, consider both the content and the timestamp
3. Don't automatically prefer the most recent content - use judgment based on the context
4. For time-specific queries, prioritize temporal information in the content before considering creation timestamps

---Conversation History---
{history}

---Document Chunks(DC)---
{content_data}

---Response Rules---

- Target format and length: {response_type}
- Use markdown formatting with appropriate section headings
- Please respond in the same language as the user's question.
- Ensure the response maintains continuity with the conversation history.
- List up to 5 most important reference sources at the end under "References" section. Clearly indicating each source from Document Chunks(DC), and include the file path if available, in the following format: [DC] file_path
- If you don't know the answer, just say so.
- Do not include information not provided by the Document Chunks.
- Addtional user prompt: {user_prompt}

Response:"""


# TODO: deprecated
PROMPTS[
    "similarity_check"
] = """Please analyze the similarity between these two questions:

Question 1: {original_prompt}
Question 2: {cached_prompt}

Please evaluate whether these two questions are semantically similar, and whether the answer to Question 2 can be used to answer Question 1, provide a similarity score between 0 and 1 directly.

Similarity score criteria:
0: Completely unrelated or answer cannot be reused, including but not limited to:
   - The questions have different topics
   - The locations mentioned in the questions are different
   - The times mentioned in the questions are different
   - The specific individuals mentioned in the questions are different
   - The specific events mentioned in the questions are different
   - The background information in the questions is different
   - The key conditions in the questions are different
1: Identical and answer can be directly reused
0.5: Partially related and answer needs modification to be used
Return only a number between 0-1, without any additional content.
"""
