import json

from flask import Flask, jsonify, Response, request, redirect, url_for
import flask
from vanna_model.vanna_chromadb_openai import VannaChromaDBOpenai
from sqlalchemy import create_engine
from common.common_result import ApiResponse
import datetime


# class GeneratePlotlyHTML:
#     def __init__(self):
#         pass

# 自然语言查询SQL 生成图表HTML
def query_for_chart_html() -> jsonify:
    """
    自然语言查询SQL 生成图表HTML
    从Flask的请求中获取问题参数，并返回一个包含问题和HTML内容的JSON响应。
    参数:
    question: 用户输入的问题
    返回值:
    jsonify: 返回一个JSON响应对象，包含问题（question）和HTML内容（html）。
    """

    api_response = ApiResponse(500, "请求出错")

    # # dump = json.dumps(api_response)
    # # print(dump)
    # json = api_response.json()
    # print(json)
    # return api_response

    try:
        # question = flask.request.form.get('question')  # 从请求的表单数据中获取问题
        # # 数据库链接字符串 ex:'oracle://iqms:iqms@192.168.110.73:1521/IQORA'
        # db_url = flask.request.form.get('db_url')
        # # 数据库描述 ex:"This is a Oracle database"
        # db_desc = flask.request.form.get('db_desc')

        input_json = flask.request.get_json()

        print(f'{datetime.datetime.now()}:{input_json}')

        if input_json is None or len(input_json) <= 0:
            api_response.set_error("请输入参数")
            return jsonify(api_response.json())

        question = input_json['question'] if 'question' in input_json else None
        db_url = input_json['db_url'] if "db_url" in input_json else None
        db_desc = input_json['db_desc'] if "db_desc" in input_json else None
        if question is None or len(question) <= 0:
            api_response.set_error("请输入要查询的问题")
            return jsonify(api_response.json())
        if db_url is None or len(db_url) <= 0:
            api_response.set_error("请输入要链接的数据库链接字符串")
            return jsonify(api_response.json())
        if db_desc is None or len(db_desc) <= 0:
            api_response.set_error("请输入数据库类型描述")
            return jsonify(api_response.json())

        # return jsonify({"code": "test"})

        vn = VannaChromaDBOpenai(config={'api_key': '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', 'model': 'gpt-3.5-turbo'
                                         # , 'path': 'E:\\work-space\\demo-workspace\\github\\fork\\vanna_entity\\chroma.sqlite3'
                                         })
        # vn.test_ref()

        # This gives the package a function that it can use to run the SQL
        vn.run_sql = vn.run_sql
        vn.run_sql_is_set = True

        if db_desc is not None:
            vn.static_documentation = db_desc
        else:
            vn.static_documentation = "This is a Oracle database"

        # engine = None
        if db_url is not None:
            engine = create_engine(db_url)
        else:
            engine = create_engine('oracle://iqms:iqms@192.168.110.254:1521/IQORA')

        # engine = create_engine('oracle://iqms:iqms@192.168.110.73:1521/IQORA')

        # 生成sql
        sql = vn.generate_sql(question=question)
        # 执行sql取数据
        df = vn.run_sql(sql=sql, db=engine)
        code = vn.generate_plotly_code(question=question, sql=sql, df_metadata=f"Running df.dtypes gives:\n {df.dtypes}")
        fig = vn.get_plotly_figure(plotly_code=code, df=df, dark_mode=False)
        fig_html = fig.to_html()

        data = {
            "question": question,
            "html": fig_html
        }
        api_response.set_success("请求成功", data)

    except Exception as e:
        return e.__str__(), 500, {'Content-Type': 'text/plain'}
        api_response.set_error(e.__str__())

    return fig_html, 200, {'Content-Type': 'text/plain'}

    # return jsonify(
    #     api_response.json()
    # )
