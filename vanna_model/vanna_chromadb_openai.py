from vanna.openai.openai_chat import OpenAI_Chat
from vanna.chromadb.chromadb_vector import ChromaDB_VectorStore
import pandas as pd
from sqlalchemy.engine.base import Engine


class VannaChromaDBOpenai(ChromaDB_VectorStore, OpenAI_Chat):
    def __init__(self, config=None):
        ChromaDB_VectorStore.__init__(self, config=config)
        OpenAI_Chat.__init__(self, config=config)

    # You define a function that takes in a SQL query as a string and returns a pandas dataframe
    def run_sql(self, sql: str, db: Engine) -> pd.DataFrame:
        if len(sql) > 0:
            sql = sql.replace(";", "")
        df = pd.read_sql_query(sql, db)
        return df
