# -*- coding: utf-8 -*-
# pip install gunicorn
# pip install gevent

# from gevent import pywsgi

from urllib.parse import quote_plus as urlquote
import datetime
from common.common_result import ApiResponse
import sys
import yaml

type = sys.getfilesystemencoding()

from dotenv import load_dotenv

load_dotenv()
import pandas as pd
from functools import wraps
from flask import Flask, jsonify, Response, request, redirect, url_for
import flask
import os
from cache import MemoryCache
from vanna_entity.MyVanna import MyVanna

from sqlalchemy import create_engine

from controller.generate_plotly_html import query_for_chart_html

import cx_Oracle

# 获取yaml文件路径
yamlPath = 'config.yml'
config_global = None
cx_oracle_path = ""

try:
    with open(yamlPath, 'rb') as f:
        # yaml文件通过---分节，多个节组合成一个列表
        # data = yaml.safe_load_all(f)
        config_global = yaml.load(f.read(), Loader=yaml.FullLoader)
        # print(result, type(result))
        # print(result['path'], type(result['path']))

        cx_oracle_path = config_global['path']['cx_oracle']
except Exception as e:
    print('config.yml not found')
    print(e)

    # # salf_load_all方法得到的是一个迭代器，需要使用list()方法转换为列表
    # print(list(data))
    # print(data['path']['cx_oracle'])

# 解决问题(cx_Oracle.DatabaseError) DPI-1047: Cannot locate a 64-bit Oracle Client library:
# "E:\Development\oracle\product\11.2.0\client_1\bin\oci.dll is not the correct architecture"
cx_Oracle.init_oracle_client(lib_dir=cx_oracle_path)
# cx_Oracle.init_oracle_client(lib_dir=r"E:\Development\PremiumSoft\Navicat Premium 15\instantclient_11_2")

app = Flask(__name__, static_url_path='')

# 自 然语言查询SQL 生成图表HTML
app.add_url_rule("/api/query_for_chart_html", view_func=query_for_chart_html, methods=['POST'])

# # flask 传参方式
# # 1.'/test1/<question_url>' 加 def route_test(question_url: str):
# # 2. flask.request.args.get('question')
# # 3. flask.request.form.get('question')
# @app.route('/test1/<question_url>', methods=['GET', 'POST'])
# def route_test(question_url: str):
#     question = flask.request.args.get('question')
#     question = flask.request.form.get('question')
#     return f"test:{question},question_url:{question_url}"


# SETUP
cache = MemoryCache()

# from vanna_entity.local import LocalContext_OpenAI
# vn = LocalContext_OpenAI()

# from vanna_entity.remote import VannaDefault
# vn = VannaDefault(model=os.environ['VANNA_MODEL'], api_key=os.environ['VANNA_API_KEY'])


vn = MyVanna(config={'api_key': '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', 'model': 'gpt-3.5-turbo'
                     # , 'path': 'E:\\work-space\\demo-workspace\\github\\fork\\vanna_entity\\chroma.sqlite3'
                     })
# 连接ChatGLM3
# vn = MyVanna(config={'api_key': 'EMPTY', 'model': 'chatglm3-6b', 'base_url': 'http://127.0.0.1:8009/v1/'})

argv = sys.argv
print(argv)

# db_str = 'oracle://iqms:iqms@192.168.110.74:1521/IQORA'
# if len(argv) > 1:
#     arg_key = argv[1]
#     if arg_key == '--dbstr':
#         db_str = argv[2]

db_str = config_global["db_str"]["local"]

# oracle
# engine = create_engine('oracle://iqms:iqms@192.168.110.254:1521/IQORA')
engine = create_engine(db_str)

userName = 'root'
password = 'a@12345'
dbHost = '127.0.0.1'
dbPort = 3306
dbName = 'robot'


# SQLServer
# engine = create_engine('mssql+pymssql://sa:a@12345@Test-Data:1433/SPLMBak', pwd=None)
# engine = create_engine(f'mssql+pymssql://sa:{urlquote(password)}@Test-Data:1433/SPLMBak')
# engine = create_engine(f'mssql+pymssql://sa:sensnow100%@192.168.110.74:1433/ScenePLM')


# engine = create_engine('mssql+pymssql://sa:server2008@sensnow-hfj:1433/SCENEPLM220615')


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
# # training
# # The information schema query may need some tweaking depending on your database. This is a good starting point.
# # vanna原生不支持oracle 这里改造代码 使oracle可以匹配 vanna_entity
# # 具体代码在E:\Development\conda_env\vanna_entity\Lib\site-packages\vanna_entity\base\base.py里
# # table_catalog对应mysql的def; table_schema对应mysql的库名
#
# # 初始化SQLServer语句
# # df_information_schema = vn.run_sql("SELECT * FROM INFORMATION_SCHEMA.COLUMNS")
# df_information_schema = vn.run_sql("SELECT main.OWNER as table_catalog,main.OWNER as table_schema,main.* FROM all_tab_cols main where main.OWNER='IQMS'")
#
# # This will break up the information schema into bite-sized chunks that can be referenced by the LLM
# plan = vn.get_training_plan_generic(df_information_schema)
# print(plan)
#
# # If you like the plan, then uncomment this and run it to train
# vn.train(plan=plan)
#
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

# 自己添加的方法,初始化数据库训练
@app.route('/api/init_training_db', methods=['GET', 'POST'])
def init_training_db():
    # db_type 数据库类型,0:oracle,1:mssql,2:mssql
    db_type = flask.request.args.get('db_type')

    # -------------------------------核心库初始化训练-------------------------------
    # training
    # The information schema query may need some tweaking depending on your database. This is a good starting point.
    # vanna原生不支持oracle 这里改造代码 使oracle可以匹配 vanna_entity
    # 具体代码在E:\Development\conda_env\vanna_entity\Lib\site-packages\vanna_entity\base\base.py里
    # table_catalog对应mysql的def; table_schema对应mysql的库名
    df_information_schema = None
    if db_type == '0':
        df_information_schema = vn.run_sql("SELECT main.OWNER as table_catalog,main.OWNER as table_schema,main.* FROM all_tab_cols main where main.OWNER='IQMS'")
        vn.static_documentation = "This is a Oracle database"
    elif db_type == '1' or db_type == '2':
        vn.static_documentation = "This is a MySQL database"
        if db_type == '2':
            vn.static_documentation = "This is a MsSQL database"
        df_information_schema = vn.run_sql("SELECT * FROM INFORMATION_SCHEMA.COLUMNS")

    # 初始化SQLServer语句
    # df_information_schema = vn.run_sql("SELECT * FROM INFORMATION_SCHEMA.COLUMNS")
    # df_information_schema = vn.run_sql("SELECT main.OWNER as table_catalog,main.OWNER as table_schema,main.* FROM all_tab_cols main where main.OWNER='IQMS'")

    # This will break up the information schema into bite-sized chunks that can be referenced by the LLM
    plan = vn.get_training_plan_generic(df_information_schema)
    print(plan)

    # If you like the plan, then uncomment this and run it to train
    vn.train(plan=plan)

    # -------------------------------核心库初始化训练-------------------------------
    return jsonify({
        "code": 200,
        "msg": "初始化数据库训练成功"
    })


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
            # "df": df.head(25).to_json(orient='records'),
            "df": df.to_json(orient='records'),
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


@app.route('/api/add_training', methods=['POST'])
def add_training_data_custom():
    """
    向系统添加自定义的训练数据。

    接收POST请求，请求体中包含训练数据的四个关键部分：问题（question）、
    结构化查询语言（SQL）、数据定义语言（DDL）和文档说明（documentation）。

    参数:
    - question: 训练数据中的问题部分，字符串类型。
    - sql: 对应于问题的结构化查询语言，字符串类型。
    - ddl: 数据定义语言，用于定义数据结构，字符串类型。
    - documentation: 对训练数据的文档说明，字符串类型。

    返回值:
    - 如果训练数据添加成功，返回一个包含训练数据唯一标识符（id）的JSON对象。
    - 如果添加过程中出现错误，返回一个包含错误信息的JSON对象。
    """
    api_response = ApiResponse(500, "请求出错")

    input_json = flask.request.get_json()
    print(f'{datetime.datetime.now()}--add_training_data_input_json:{input_json}')
    if input_json is None or len(input_json) <= 0:
        api_response.set_error("请输入参数")
        return api_response.json()

    # 从请求体中获取训练数据的四个部分
    question = input_json['question'] if 'question' in input_json else None
    sql = input_json['sql'] if 'sql' in input_json else None
    ddl = input_json['ddl'] if 'ddl' in input_json else None
    documentation = input_json['documentation'] if 'documentation' in input_json else None

    if question and not sql:
        api_response.set_error("输入了question必须有对应的sql语句")
        return api_response.json()

    if documentation is None and sql is None and ddl is None:
        api_response.set_error("请至少输入要训练的sql或documentation或ddl中的一个")
        return api_response.json()

    # 从请求体中获取训练数据的四个部分
    # question = flask.request.json.get('question')
    # sql = flask.request.json.get('sql')
    # ddl = flask.request.json.get('ddl')
    # documentation = flask.request.json.get('documentation')

    try:

        # collection_query = vn.sql_collection.query(query_texts=[question], n_results=50)
        # print(collection_query)
        # return

        training_data_single = vn.get_single_training_data_custom(question=question, sql=sql, ddl=ddl, documentation=documentation)

        single_ids = training_data_single["ids"]
        if len(single_ids) > 0:
            api_response.set_success(f"已存在id为{single_ids}的训练数据")
            return api_response.json()

        # 尝试使用提供的训练数据进行训练，并获取训练的唯一标识符
        id = vn.train(question=question, sql=sql, ddl=ddl, documentation=documentation)

        data = {"id": id}
        api_response.set_success("添加训练数据成功", data)
        # return api_response.json()
        # 返回训练的唯一标识符
        # return jsonify({"id": id})
    except Exception as e:
        # 如果训练过程中出现异常，打印错误信息，并返回错误信息
        print("TRAINING ERROR", e)
        api_response.set_error(f"添加训练数据失败,{e.__str__()}")
        # return jsonify({"type": "error", "error": str(e)})
    return api_response.json()


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
    """
    处理应用的根路由请求，返回静态文件index.html。

    参数:
    无

    返回值:
    返回服务器上的静态文件index.html。
    """
    return app.send_static_file('index.html')  # 发送静态文件作为响应


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5001)

# if __name__ == '__main__':
#     server = pywsgi.WSGIServer(('127.0.0.1', 5001), app)
#     server.serve_forever()
