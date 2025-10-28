from marshmallow import Schema, fields, validate, validates, ValidationError
from datetime import datetime

class ExceptionDataSchema(Schema):
    """异常数据序列化模式"""
    stcd = fields.String(required=True, validate=validate.Length(min=1, max=50))
    stnm = fields.String(required=True, validate=validate.Length(min=1, max=100))
    aid = fields.String(required=False)
    val = fields.Float(required=True)
    tm = fields.DateTime(required=True, format='%Y-%m-%d %H:%M:%S')
    insert_tm = fields.DateTime(required=False, format='%Y-%m-%d %H:%M:%S')

class PaginationSchema(Schema):
    """分页参数模式"""
    page = fields.Integer(required=False, load_default=1, validate=validate.Range(min=1))
    page_size = fields.Integer(
        required=False,
        load_default=20,
        validate=validate.Range(min=1, max=100)
    )
    # 政区代码 - 支持新旧参数名
    adcd = fields.String(required=False, validate=validate.Length(max=20))
    aid = fields.String(required=False, validate=validate.Length(max=20))

    # 测站编码
    stcd = fields.String(required=False, validate=validate.Length(max=50))

    # 时间范围 - 支持新旧参数名
    bt = fields.DateTime(
        required=False,
        format='%Y-%m-%d %H:%M:%S',
        allow_none=True
    )
    et = fields.DateTime(
        required=False,
        format='%Y-%m-%d %H:%M:%S',
        allow_none=True
    )
    start_time = fields.DateTime(
        required=False,
        format='%Y-%m-%d %H:%M:%S',
        allow_none=True
    )
    end_time = fields.DateTime(
        required=False,
        format='%Y-%m-%d %H:%M:%S',
        allow_none=True
    )

    # 新增参数
    name = fields.String(required=False, validate=validate.Length(max=100))
    status = fields.Integer(required=False, validate=validate.OneOf([0, 1, 2]), missing=0)
    export = fields.String(required=False, validate=validate.OneOf(['excel']), allow_none=True)

    # 时间验证将在路由逻辑中处理，以避免参数名冲突

class UpdateRemarkSchema(Schema):
    """更新异常原因模式"""
    stcd = fields.String(required=True, validate=validate.Length(min=1, max=50))
    rem = fields.String(required=True, validate=validate.Length(min=1, max=500))
    tm = fields.DateTime(
        required=True,
        format='%Y-%m-%d %H:%M:%S'
    )
    name = fields.String(required=True, validate=validate.Length(min=1, max=100))
    status = fields.Integer(required=True, validate=validate.Range(min=0, max=10))

class FarmSchema(Schema):
    """团场信息模式"""
    aid = fields.String(required=True)
    pending_count = fields.Integer(required=True)

class ResponseSchema(Schema):
    """通用响应模式"""
    code = fields.Integer(required=True)
    message = fields.String(required=True)
    data = fields.Dict(required=False)
    error = fields.String(required=False)

class ExceptionDataItemSchema(Schema):
    """异常数据项模式"""
    stcd = fields.String(required=True)
    stnm = fields.String(required=True)
    aid = fields.String(required=True)
    val = fields.Float(required=True)
    rem = fields.String(required=False, allow_none=True)
    tm = fields.DateTime(required=False, allow_none=True)
    insert_tm = fields.DateTime(required=False, allow_none=True)
    re_name = fields.String(required=False, allow_none=True)
    status = fields.Integer(required=False, allow_none=True)
    re_time = fields.DateTime(required=False, allow_none=True)
    lgtd = fields.Float(required=False, allow_none=True)
    lttd = fields.Float(required=False, allow_none=True)
    xian = fields.String(required=False, allow_none=True)  # 县名称
    shi = fields.String(required=False, allow_none=True)  # 市名称

class ExceptionListDataSchema(Schema):
    """异常列表数据模式"""
    total = fields.Integer(required=True)
    page = fields.Integer(required=True)
    page_size = fields.Integer(required=True)
    pages = fields.Integer(required=True)
    items = fields.List(fields.Nested(ExceptionDataItemSchema()), required=True)

class ExceptionListResponseSchema(ResponseSchema):
    """异常列表响应模式"""
    data = fields.Nested(ExceptionListDataSchema(), required=True)

class UpdateResponseSchema(ResponseSchema):
    """更新操作响应模式"""
    data = fields.Dict(required=True)

class FarmListResponseSchema(ResponseSchema):
    """团场列表响应模式"""
    data = fields.List(fields.Nested(FarmSchema()), required=True)