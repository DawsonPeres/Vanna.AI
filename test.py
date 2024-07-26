from vanna_entity.openai.openai_chat import OpenAI_Chat
from vanna_entity.chromadb.chromadb_vector import ChromaDB_VectorStore


class MyVanna(ChromaDB_VectorStore, OpenAI_Chat):
    def __init__(self, config=None):
        ChromaDB_VectorStore.__init__(self, config=config)
        OpenAI_Chat.__init__(self, config=config)


vn = MyVanna(config={'api_key': 'sk-...', 'model': ''})

vn.connect_to_sqlite()
