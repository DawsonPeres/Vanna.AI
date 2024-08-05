import re

import pandas as pd
from vanna.openai.openai_chat import OpenAI_Chat
from vanna.chromadb.chromadb_vector import ChromaDB_VectorStore

from chromadb.api.types import (
    URI,
    CollectionMetadata,
    DataLoader,
    Embedding,
    Embeddings,
    Embeddable,
    Include,
    Loadable,
    Metadata,
    Metadatas,
    Document,
    Documents,
    Image,
    Images,
    URIs,
    Where,
    IDs,
    EmbeddingFunction,
    GetResult,
    QueryResult,
    ID,
    OneOrMany,
    WhereDocument,
    maybe_cast_one_to_many_ids,
    maybe_cast_one_to_many_embedding,
    maybe_cast_one_to_many_metadata,
    maybe_cast_one_to_many_document,
    maybe_cast_one_to_many_image,
    maybe_cast_one_to_many_uri,
    validate_ids,
    validate_include,
    validate_metadata,
    validate_metadatas,
    validate_where,
    validate_where_document,
    validate_n_results,
    validate_embeddings,
    validate_embedding_function,
)
from entity.logging import logger
from services.basic_vonna_services import BasicVanna
from services.search_chinese_noun_service import extract_keywords, cut_sentence
from services.sqlite_service import SqliteService


# import sys
# print("sys.path:---------------------------------------")
# print(sys.path)
# print("sys.path:---------------------------------------")


class MyVanna(BasicVanna):

    def __init__(self, config=None):
        BasicVanna.__init__(self, config=config)

    def get_single_training_data_custom(self, question: str | None, documentation: str | None, sql: str | None,
                                        ddl: str | None, **kwargs) -> GetResult:
        if sql is not None:
            collection_get = self.sql_collection.get(where_document={"$contains": sql})
            return collection_get
        elif documentation is not None:
            collection_get = self.documentation_collection.get(where_document={"$contains": documentation})
            return collection_get
        elif ddl is not None:
            collection_get = self.ddl_collection.get(where_document={"$contains": ddl})
            return collection_get

    def get_related_documentation(self, question: str, **kwargs):
        """多次训练后后的文件类型强化搜索"""
        try:
            noun_list = cut_sentence(question)
            query_documentation = self.documentation_collection.query(
                query_texts=[question],
                n_results=self.n_results_documentation,
            )
            documents = get_record_where_document(noun_list)
            query_documentation["documents"][0] = documents

            return ChromaDB_VectorStore._extract_documents(query_documentation)
        except ValueError as e:
            logger.error("【MyVanna】get_related_documentation error:{}".format(e))
            return super(ChromaDB_VectorStore, self).get_related_documentation(question, **kwargs)

    def add_documentation_to_prompt(
            self,
            initial_prompt: str,
            documentation_list: list[str],
            max_tokens: int = 14000,
    ) -> str:
        try:
            if len(documentation_list) > 0:
                initial_prompt += "\n===Additional Context \n\n"

                for documentation in documentation_list:
                    initial_prompt += f"{documentation}\n\n"

            return initial_prompt
        except ValueError as e:
            logger.error("【MyVanna】add_documentation_to_prompt error:{}".format(e))
            return super(ChromaDB_VectorStore, self).add_documentation_to_prompt(
                initial_prompt, documentation_list, max_tokens
            )

    def generate_followup_questions(
            self, question: str, sql: str, df: pd.DataFrame, n_questions: int = 5, **kwargs
    ) -> list:
        """
        部分匹配信息过长，openai会报tokens超长，现阶段的训练数据多是数据库表格信息，存在大量的空格，去除空格
        """

        message_log = [
            self.system_message(
                f"You are a helpful data assistant. The user asked the question: '{question}'\n\nThe SQL query for "
                f"this question was: {sql}\n\nThe following is a pandas DataFrame with the results of the query: \n"
                f"{df.to_markdown()}\n\n"
            ),
            self.user_message(
                f"Generate a list of {n_questions} followup questions that the user might ask about this data. "
                f"Respond with a list of questions, one per line. Do not answer with any explanations -- just the "
                f"questions. Remember that there should be an unambiguous SQL query that can be generated from the "
                f"question. Prefer questions that are answerable outside of the context of this conversation. Prefer "
                f"questions that are slight modifications of the SQL query that was generated that allow digging "
                f"deeper into the data. Each question will be turned into a button that the user can click to "
                f"generate a new SQL query so don't use 'example' type questions. Each question must have a "
                f"one-to-one correspondence with an instantiated SQL query." +
                self._response_language()
            ),
        ]
        content = message_log[0]['content']
        _content = content.replace("  ", "")
        message_log[0]["content"] = _content
        llm_response = self.submit_prompt(message_log, **kwargs)
        logger.info("【MyVanna】generate_followup_questions message_log:{}".format(message_log))
        numbers_removed = re.sub(r"^\d+\.\s*", "", llm_response, flags=re.MULTILINE)
        return numbers_removed.split("\n")


def get_record_where_document(noun_list, contains=False):
    """匹配已维护训练数据"""
    if not noun_list:
        return {}

    sqlite_server = SqliteService()

    like_str = "OR ".join(["`key` LIKE '%{}%' ".format(i) for i in noun_list])
    search_sql = """SELECT `key`,`value` FROM "main"."record" WHERE {}""".format(like_str)
    logger.info("【MyVanna】get_record_where_document search_sql:{}".format(search_sql))
    sqlite_server.cursor.execute(search_sql)
    sqlite_server.conn.commit()
    sqlite_data = sqlite_server.cursor.fetchall()
    logger.info("【MyVanna】get_record_where_document sqlite_data:{}".format(sqlite_data))

    bind_noun_list = [f"{noun_list[i]}%{noun_list[i + 1]}" for i in range(len(noun_list) - 1)] if len(
        noun_list) > 1 else []
    bind_like_str = "OR ".join(["`key` LIKE '%{}%' ".format(i) for i in bind_noun_list])
    bind_search_sql = """SELECT `key`,`value` FROM "main"."record" WHERE {}""".format(bind_like_str)
    logger.info("【MyVanna】get_record_where_document bind_search_sql:{}".format(bind_search_sql))
    sqlite_server.cursor.execute(bind_search_sql)
    sqlite_server.conn.commit()
    bind_sqlite_data = sqlite_server.cursor.fetchall()
    logger.info("【MyVanna】get_record_where_document sqlite_data:{}".format(bind_sqlite_data))
    sqlite_server.close()

    if bind_sqlite_data:
        _document = list(set(["是".join([i[0], i[1]]) for i in bind_sqlite_data]))
    else:
        _document = list(set(["是".join([i[0], i[1]]) for i in sqlite_data]))

    # _document = {k: v for k, v in sqlite_data if k in noun_list}
    if not _document:
        return {}
    if len(_document) == 1:
        return {"$contains": "{} ".format(_document[0])} if contains else [_document[0]]
    where_document = {"$or": [{"$contains": "{} ".format(v)} for v in _document]} if contains else _document
    return where_document


def get_similar_documents(question: str, **kwargs):
    """根据问题生成相近的信息，"""
    noun_list = extract_keywords(question)
    return


def add_documentation(document_list, task_id):
    sqlite_server = SqliteService()
    insert_sql = """INSERT INTO "main"."upload_document" ("task_id", "state") VALUES ('{}', '{}');""".format(
        task_id, "running"
    )
    sqlite_server.cursor.execute(insert_sql)
    sqlite_server.conn.commit()

    vn = MyVanna(config={'api_key': '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', 'model': 'gpt-3.5-turbo'})
    # task_id,state,doc,doc_state,error
    success_doc_list = []
    error_doc_list = []

    for doc in document_list:
        try:
            id = vn.train(documentation=doc)
            if id:
                success_doc_list.append((task_id, "success", doc, "success", str(id)))
        except Exception as e:
            logger.error("【add_documentation】 train doc error:{},doc={}".format(e, doc))
            error_doc_list.append((task_id, "fail", doc, "fail", str(e)))

    batch_insert_sql = """INSERT INTO "main"."upload_document" ("task_id","state","doc","doc_state","error_message") VALUES (?,?,?,?,?);"""
    sqlite_server.cursor.executemany(batch_insert_sql, success_doc_list + error_doc_list)
    sqlite_server.conn.commit()

    if not success_doc_list:
        state = "fail"
    else:
        state = "success"

    update_sql = """UPDATE "main"."upload_document" SET "state" = "{}" WHERE "task_id" = {}""".format(state, task_id)
    sqlite_server.cursor.execute(update_sql)

    sqlite_server.conn.commit()
    sqlite_server.close()


def get_upload_task_state(task_id):
    fail_data = []
    state = "running"
    sqlite_server = SqliteService()
    sql = """SELECT "state" FROM "main"."upload_document" WHERE "task_id" = '{}';""".format(task_id)
    sqlite_data = sqlite_server.cursor.execute(sql).fetchall()

    if not sqlite_data:
        state = "fail"
        fail_data = []
    if sqlite_data[0][0] == "fail":
        fail_sql = """SELECT "doc","error_message" FROM "main"."upload_document" WHERE "task_id" = '{}' AND "doc_state"="fail";""".format(
            task_id)
        sql_data = sqlite_server.cursor.execute(fail_sql).fetchall()
        fail_data = [{"doc": _da[0], "error_message": _da[1]} for _da in sql_data]
        state = "fail"
    elif sqlite_data[0][0] == "success":
        state = "success"
        fail_data = []
    sqlite_server.close()
    return state, fail_data
