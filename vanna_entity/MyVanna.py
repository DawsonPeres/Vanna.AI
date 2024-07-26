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

# import sys
# print("sys.path:---------------------------------------")
# print(sys.path)
# print("sys.path:---------------------------------------")


class MyVanna(ChromaDB_VectorStore, OpenAI_Chat):

    def __init__(self, config=None):
        ChromaDB_VectorStore.__init__(self, config=config)
        OpenAI_Chat.__init__(self, config=config)

    # 根据question,sql,documentation,ddl获取training_data
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


