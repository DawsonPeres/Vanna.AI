from pydantic.main import BaseModel
from typing import Optional
from fastapi import Body


class ApiRequest(BaseModel):
    """ 创建用户接口数据校验 """
    # default=..., 是指name字段为必填项, 不写default参数也是默认为必填, 这里加上只是为了更清晰
    query: str = Body(default=..., description="查询语句")
    # targetJsonDict: str = Body(default=..., description="目标数据字典")
    # # Optional[str]可选项, default=None可以不填或者是填写None
    # constraintJsonDict: Optional[str] = Body(default=None, description="数值约束字典")
    # compareConstraintJsonDict: Optional[str] = Body(default=None, description="两个字段值比较约束字典")


class ApiResponse(BaseModel):
    """ 创建用户返回数据格式化 """
    code: Optional[int]
    msg: Optional[str]
    data: Optional[object]

    def __init__(self, code: int, msg: str = None, data: object = None):
        super().__init__(code=code, msg=msg, data=data)
        self.code = code
        # self.msg = "程序出错"

    def set_success(self):
        self.code = 200
        self.msg = "运行成功"

    def set_success(self, msg: str = None):
        self.code = 200
        self.msg = msg

    def set_success(self, msg: str = None, data: object = None):
        self.code = 200
        self.msg = msg
        self.data = data

    def set_error(self, msg: str = None):
        self.code = 500
        self.msg = msg

        # class Config:
    #     # 设置orm_mode=True, 可以在view层直接返回model实例, 并且关联的外键数据也可以直接查出来
    #     orm_mode = True