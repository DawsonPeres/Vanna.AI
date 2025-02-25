from dotenv import load_dotenv

load_dotenv()
import pandas as pd
from functools import wraps
from flask import Flask, jsonify, Response, request, redirect, url_for
import flask
import os
from cache import MemoryCache

from vanna_entity.openai.openai_chat import OpenAI_Chat
from vanna_entity.chromadb.chromadb_vector import ChromaDB_VectorStore

from sqlalchemy import create_engine

import cx_Oracle

# 解决问题(cx_Oracle.DatabaseError) DPI-1047: Cannot locate a 64-bit Oracle Client library:
# "E:\Development\oracle\product\11.2.0\client_1\bin\oci.dll is not the correct architecture"
cx_Oracle.init_oracle_client(lib_dir=r"E:\Development\PremiumSoft\Navicat Premium 15\instantclient_11_2")

app = Flask(__name__, static_url_path='')

# SETUP
cache = MemoryCache()


# from vanna_entity.local import LocalContext_OpenAI
# vn = LocalContext_OpenAI()

# from vanna_entity.remote import VannaDefault
# vn = VannaDefault(model=os.environ['VANNA_MODEL'], api_key=os.environ['VANNA_API_KEY'])

class MyVanna(ChromaDB_VectorStore, OpenAI_Chat):
    def __init__(self, config=None):
        ChromaDB_VectorStore.__init__(self, config=config)
        OpenAI_Chat.__init__(self, config=config)


vn = MyVanna(config={'api_key': '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', 'model': 'gpt-3.5-turbo'
                     # , 'path': 'E:\\work-space\\demo-workspace\\github\\fork\\vanna_entity\\chroma.sqlite3'
                     })
# 连接ChatGLM3
# vn = MyVanna(config={'api_key': 'EMPTY', 'model': 'chatglm3-6b', 'base_url': 'http://127.0.0.1:8009/v1/'})

engine = create_engine('oracle://iqms:iqms@192.168.110.73:1521/IQORA')


# You define a function that takes in a SQL query as a string and returns a pandas dataframe
def run_sql(sql: str) -> pd.DataFrame:
    if len(sql) > 0:
        sql = sql.replace(";", "")
    df = pd.read_sql_query(sql, engine)
    return df


# This gives the package a function that it can use to run the SQL
vn.run_sql = run_sql
vn.run_sql_is_set = True
vn.static_documentation = "This is a Oracle database"


# # -------------------------------核心库初始化训练-------------------------------
# #training
# #The information schema query may need some tweaking depending on your database. This is a good starting point.
# #vanna原生不支持oracle 这里改造代码 使oracle可以匹配 vanna_entity
# #具体代码在E:\Development\conda_env\vanna_entity\Lib\site-packages\vanna_entity\base\base.py里
# #table_catalog对应mysql的def; table_schema对应mysql的库名
# df_information_schema = vn.run_sql("SELECT main.OWNER as table_catalog,main.OWNER as table_schema,main.* FROM all_tab_cols main where main.OWNER='IQMS'")
#
#
#
# # This will break up the information schema into bite-sized chunks that can be referenced by the LLM
# plan = vn.get_training_plan_generic(df_information_schema)
# print(plan)
#
# # If you like the plan, then uncomment this and run it to train
# vn.train(plan=plan)
#
# # -------------------------------核心库初始化训练-------------------------------

#
# # You can also add SQL queries to your training data. This is useful if you have some queries already laying around. You can just copy and paste those from your editor to begin generating new SQL.
# vn.train(sql="select * from person")

# vn.ask(question="查询人员信息")


# vn.connect_to_snowflake(
#     account=os.environ['SNOWFLAKE_ACCOUNT'],
#     username=os.environ['SNOWFLAKE_USERNAME'],
#     password=os.environ['SNOWFLAKE_PASSWORD'],
#     database=os.environ['SNOWFLAKE_DATABASE'],
#     warehouse=os.environ['SNOWFLAKE_WAREHOUSE'],
# )


# NO NEED TO CHANGE ANYTHING BELOW THIS LINE
def requires_cache(fields):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            id = request.args.get('id')

            if id is None:
                return jsonify({"type": "error", "error": "No id provided"})

            for field in fields:
                if cache.get(id=id, field=field) is None:
                    return jsonify({"type": "error", "error": f"No {field} found"})

            field_values = {field: cache.get(id=id, field=field) for field in fields}

            # Add the id to the field_values
            field_values['id'] = id

            return f(*args, **field_values, **kwargs)

        return decorated

    return decorator


@app.route('/api/v0/generate_questions', methods=['GET'])
def generate_questions():
    return jsonify({
        "type": "question_list",
        "questions": vn.generate_questions(),
        "header": "Here are some questions you can ask:"
    })


@app.route('/api/v0/generate_sql', methods=['GET'])
def generate_sql():
    question = flask.request.args.get('question')

    if question is None:
        return jsonify({"type": "error", "error": "No question provided"})

    id = cache.generate_id(question=question)
    sql = vn.generate_sql(question=question)

    cache.set(id=id, field='question', value=question)
    cache.set(id=id, field='sql', value=sql)

    return jsonify(
        {
            "type": "sql",
            "id": id,
            "text": sql,
        })


@app.route('/api/v0/run_sql', methods=['GET'])
@requires_cache(['sql'])
def run_sql(id: str, sql: str):
    try:
        df = vn.run_sql(sql=sql)

        cache.set(id=id, field='df', value=df)

        return jsonify(
            {
                "type": "df",
                "id": id,
                "df": df.head(10).to_json(orient='records'),
            })

    except Exception as e:
        return jsonify({"type": "error", "error": str(e)})


@app.route('/api/v0/download_csv', methods=['GET'])
@requires_cache(['df'])
def download_csv(id: str, df):
    csv = df.to_csv()

    return Response(
        csv,
        mimetype="text/csv",
        headers={"Content-disposition":
                     f"attachment; filename={id}.csv"})


@app.route('/api/v0/generate_plotly_figure', methods=['GET'])
@requires_cache(['df', 'question', 'sql'])
def generate_plotly_figure(id: str, df, question, sql):
    try:
        code = vn.generate_plotly_code(question=question, sql=sql, df_metadata=f"Running df.dtypes gives:\n {df.dtypes}")
        fig = vn.get_plotly_figure(plotly_code=code, df=df, dark_mode=False)
        fig_json = fig.to_json()

        cache.set(id=id, field='fig_json', value=fig_json)

        return jsonify(
            {
                "type": "plotly_figure",
                "id": id,
                "fig": fig_json,
            })
    except Exception as e:
        # Print the stack trace
        import traceback
        traceback.print_exc()

        return jsonify({"type": "error", "error": str(e)})


@app.route('/api/v0/generate_plotly_figure_to_html_custom', methods=['GET'])
@requires_cache(['df', 'question', 'sql'])
def generate_plotly_figure_to_html_custom(id: str, df, question, sql):
    try:
        code = vn.generate_plotly_code(question=question, sql=sql, df_metadata=f"Running df.dtypes gives:\n {df.dtypes}")
        fig = vn.get_plotly_figure(plotly_code=code, df=df, dark_mode=False)
        fig_json = fig.to_json()

        cache.set(id=id, field='fig_json', value=fig_json)

        fig_html = fig.to_html()

        return jsonify(
            {
                "type": "plotly_figure",
                "id": id,
                "fig": fig_json,
                "html": fig_html
            })
    except Exception as e:
        # Print the stack trace
        import traceback
        traceback.print_exc()

        return jsonify({"type": "error", "error": str(e)})


@app.route('/api/v0/get_training_data', methods=['GET'])
def get_training_data():
    df = vn.get_training_data()

    return jsonify(
        {
            "type": "df",
            "id": "training_data",
            "df": df.head(25).to_json(orient='records'),
        })


@app.route('/api/v0/remove_training_data', methods=['POST'])
def remove_training_data():
    # Get id from the JSON body
    id = flask.request.json.get('id')

    if id is None:
        return jsonify({"type": "error", "error": "No id provided"})

    if vn.remove_training_data(id=id):
        return jsonify({"success": True})
    else:
        return jsonify({"type": "error", "error": "Couldn't remove training data"})


@app.route('/api/v0/train', methods=['POST'])
def add_training_data():
    question = flask.request.json.get('question')
    sql = flask.request.json.get('sql')
    ddl = flask.request.json.get('ddl')
    documentation = flask.request.json.get('documentation')

    try:
        id = vn.train(question=question, sql=sql, ddl=ddl, documentation=documentation)

        return jsonify({"id": id})
    except Exception as e:
        print("TRAINING ERROR", e)
        return jsonify({"type": "error", "error": str(e)})


@app.route('/api/v0/generate_followup_questions', methods=['GET'])
@requires_cache(['df', 'question', 'sql'])
def generate_followup_questions(id: str, df, question, sql):
    followup_questions = vn.generate_followup_questions(question=question, sql=sql, df=df)

    cache.set(id=id, field='followup_questions', value=followup_questions)

    return jsonify(
        {
            "type": "question_list",
            "id": id,
            "questions": followup_questions,
            "header": "Here are some followup questions you can ask:"
        })


@app.route('/api/v0/load_question', methods=['GET'])
@requires_cache(['question', 'sql', 'df', 'fig_json', 'followup_questions'])
def load_question(id: str, question, sql, df, fig_json, followup_questions):
    try:
        return jsonify(
            {
                "type": "question_cache",
                "id": id,
                "question": question,
                "sql": sql,
                "df": df.head(10).to_json(orient='records'),
                "fig": fig_json,
                "followup_questions": followup_questions,
            })

    except Exception as e:
        return jsonify({"type": "error", "error": str(e)})


@app.route('/api/v0/get_question_history', methods=['GET'])
def get_question_history():
    return jsonify({"type": "question_history", "questions": cache.get_all(field_list=['question'])})


@app.route('/')
def root():
    return app.send_static_file('index.html')


if __name__ == '__main__':
    app.run(debug=False)
