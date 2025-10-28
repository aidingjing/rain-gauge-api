#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
原生验证器模块 - 替代marshmallow
使用Python原生库实现数据验证和序列化功能
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Union, Callable


class ValidationError(Exception):
    """验证错误异常类"""
    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(message)


class ValidationErrors(Exception):
    """多重验证错误异常类"""
    def __init__(self, errors: Dict[str, List[str]]):
        self.errors = errors
        super().__init__(f"验证失败: {errors}")


class FieldValidator:
    """字段验证器基类"""

    def __init__(self, required: bool = False, default: Any = None,
                 allow_none: bool = False, field_name: str = None):
        self.required = required
        self.default = default
        self.allow_none = allow_none
        self.field_name = field_name

    def validate(self, value: Any) -> Any:
        """验证字段值"""
        # 处理None值
        if value is None:
            if self.required and not self.allow_none:
                raise ValidationError(f"{self.field_name or '字段'}是必填的", self.field_name)
            if not self.allow_none:
                raise ValidationError(f"{self.field_name or '字段'}不能为空", self.field_name)
            return None

        # 执行具体验证逻辑
        return self._validate_value(value)

    def _validate_value(self, value: Any) -> Any:
        """子类实现的验证逻辑"""
        raise NotImplementedError

    def apply_default(self, data: Dict[str, Any]) -> Any:
        """应用默认值"""
        if self.field_name in data:
            return data[self.field_name]
        if self.default is not None:
            return self.default
        return None


class StringField(FieldValidator):
    """字符串字段验证器"""

    def __init__(self, min_length: int = None, max_length: int = None,
                 pattern: str = None, **kwargs):
        self.min_length = min_length
        self.max_length = max_length
        self.pattern = pattern
        super().__init__(**kwargs)

    def _validate_value(self, value: Any) -> str:
        if not isinstance(value, str):
            value = str(value)

        length = len(value)

        if self.min_length is not None and length < self.min_length:
            raise ValidationError(
                f"{self.field_name}长度不能少于{self.min_length}个字符",
                self.field_name
            )

        if self.max_length is not None and length > self.max_length:
            raise ValidationError(
                f"{self.field_name}长度不能超过{self.max_length}个字符",
                self.field_name
            )

        if self.pattern and not re.match(self.pattern, value):
            raise ValidationError(
                f"{self.field_name}格式不正确",
                self.field_name
            )

        return value


class IntegerField(FieldValidator):
    """整数字段验证器"""

    def __init__(self, min_value: int = None, max_value: int = None, **kwargs):
        self.min_value = min_value
        self.max_value = max_value
        super().__init__(**kwargs)

    def _validate_value(self, value: Any) -> int:
        try:
            if isinstance(value, bool):
                value = int(value)
            elif not isinstance(value, int):
                value = int(float(value))
        except (ValueError, TypeError):
            raise ValidationError(
                f"{self.field_name}必须是整数",
                self.field_name
            )

        if self.min_value is not None and value < self.min_value:
            raise ValidationError(
                f"{self.field_name}不能小于{self.min_value}",
                self.field_name
            )

        if self.max_value is not None and value > self.max_value:
            raise ValidationError(
                f"{self.field_name}不能大于{self.max_value}",
                self.field_name
            )

        return value


class FloatField(FieldValidator):
    """浮点数字段验证器"""

    def __init__(self, min_value: float = None, max_value: float = None, **kwargs):
        self.min_value = min_value
        self.max_value = max_value
        super().__init__(**kwargs)

    def _validate_value(self, value: Any) -> float:
        try:
            return float(value)
        except (ValueError, TypeError):
            raise ValidationError(
                f"{self.field_name}必须是数字",
                self.field_name
            )

    def _validate_range(self, value: float):
        if self.min_value is not None and value < self.min_value:
            raise ValidationError(
                f"{self.field_name}不能小于{self.min_value}",
                self.field_name
            )

        if self.max_value is not None and value > self.max_value:
            raise ValidationError(
                f"{self.field_name}不能大于{self.max_value}",
                self.field_name
            )

        return value


class DateTimeField(FieldValidator):
    """日期时间字段验证器"""

    def __init__(self, format: str = '%Y-%m-%d %H:%M:%S', **kwargs):
        self.format = format
        super().__init__(**kwargs)

    def _validate_value(self, value: Any) -> datetime:
        if isinstance(value, datetime):
            return value

        if not isinstance(value, str):
            raise ValidationError(
                f"{self.field_name}必须是字符串或datetime对象",
                self.field_name
            )

        try:
            return datetime.strptime(value, self.format)
        except ValueError:
            raise ValidationError(
                f"{self.field_name}格式不正确，应为{self.format}",
                self.field_name
            )


class ChoiceField(FieldValidator):
    """选择字段验证器"""

    def __init__(self, choices: List[Any], **kwargs):
        self.choices = choices
        super().__init__(**kwargs)

    def _validate_value(self, value: Any) -> Any:
        if value not in self.choices:
            raise ValidationError(
                f"{self.field_name}必须是以下值之一: {self.choices}",
                self.field_name
            )
        return value


class ListField(FieldValidator):
    """列表字段验证器"""

    def __init__(self, inner_field: FieldValidator, **kwargs):
        self.inner_field = inner_field
        super().__init__(**kwargs)

    def _validate_value(self, value: Any) -> List[Any]:
        if not isinstance(value, list):
            raise ValidationError(
                f"{self.field_name}必须是列表",
                self.field_name
            )

        validated_list = []
        for i, item in enumerate(value):
            try:
                validated_item = self.inner_field.validate(item)
                validated_list.append(validated_item)
            except ValidationError as e:
                raise ValidationError(
                    f"{self.field_name}[{i}]验证失败: {e.message}",
                    self.field_name
                )

        return validated_list


class DictField(FieldValidator):
    """字典字段验证器"""

    def _validate_value(self, value: Any) -> Dict[str, Any]:
        if not isinstance(value, dict):
            raise ValidationError(
                f"{self.field_name}必须是字典",
                self.field_name
            )
        return value


class Schema:
    """模式基类 - 替代marshmallow.Schema"""

    def __init__(self):
        self._fields = {}
        self._setup_fields()

    def _setup_fields(self):
        """设置字段 - 子类实现"""
        pass

    def add_field(self, name: str, field: FieldValidator):
        """添加字段"""
        field.field_name = name
        self._fields[name] = field

    def load(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """验证并加载数据"""
        if not isinstance(data, dict):
            raise ValidationErrors({"_schema": ["输入必须是字典"]})

        errors = {}
        result = {}

        # 处理每个字段
        for field_name, field in self._fields.items():
            try:
                # 获取值，应用默认值
                if field_name in data:
                    value = data[field_name]
                else:
                    value = field.apply_default(data)

                # 验证字段
                validated_value = field.validate(value)
                result[field_name] = validated_value

            except ValidationError as e:
                errors[field_name] = [e.message]
            except Exception as e:
                errors[field_name] = [f"验证错误: {str(e)}"]

        if errors:
            raise ValidationErrors(errors)

        return result

    def dump(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """序列化数据"""
        if not isinstance(data, dict):
            return {}

        result = {}
        for field_name, field in self._fields.items():
            value = data.get(field_name)
            if value is not None:
                # 特殊处理datetime
                if isinstance(field, DateTimeField) and isinstance(value, datetime):
                    result[field_name] = value.strftime(field.format)
                else:
                    result[field_name] = value
            elif field.default is not None:
                result[field_name] = field.default

        return result


def validate_length(min_length: int = None, max_length: int = None):
    """长度验证器工厂函数"""
    def validator(value: str):
        length = len(value)
        if min_length is not None and length < min_length:
            raise ValidationError(f"长度不能少于{min_length}个字符")
        if max_length is not None and length > max_length:
            raise ValidationError(f"长度不能超过{max_length}个字符")
        return value
    return validator


def validate_range(min_value: float = None, max_value: float = None):
    """范围验证器工厂函数"""
    def validator(value):
        if min_value is not None and value < min_value:
            raise ValidationError(f"值不能小于{min_value}")
        if max_value is not None and value > max_value:
            raise ValidationError(f"值不能大于{max_value}")
        return value
    return validator


def validate_one_of(choices: List[Any]):
    """选择验证器工厂函数"""
    def validator(value):
        if value not in choices:
            raise ValidationError(f"值必须是以下之一: {choices}")
        return value
    return validator


# 便捷的验证函数
def validate_string(value: Any, field_name: str = "字段",
                   min_length: int = None, max_length: int = None,
                   required: bool = False) -> Optional[str]:
    """便捷的字符串验证"""
    if value is None:
        if required:
            raise ValidationError(f"{field_name}是必填的", field_name)
        return None

    if not isinstance(value, str):
        value = str(value)

    length = len(value)
    if min_length is not None and length < min_length:
        raise ValidationError(f"{field_name}长度不能少于{min_length}个字符", field_name)
    if max_length is not None and length > max_length:
        raise ValidationError(f"{field_name}长度不能超过{max_length}个字符", field_name)

    return value


def validate_integer(value: Any, field_name: str = "字段",
                    min_value: int = None, max_value: int = None,
                    required: bool = False) -> Optional[int]:
    """便捷的整数验证"""
    if value is None:
        if required:
            raise ValidationError(f"{field_name}是必填的", field_name)
        return None

    try:
        if isinstance(value, bool):
            value = int(value)
        elif not isinstance(value, int):
            value = int(float(value))
    except (ValueError, TypeError):
        raise ValidationError(f"{field_name}必须是整数", field_name)

    if min_value is not None and value < min_value:
        raise ValidationError(f"{field_name}不能小于{min_value}", field_name)
    if max_value is not None and value > max_value:
        raise ValidationError(f"{field_name}不能大于{max_value}", field_name)

    return value


def validate_float(value: Any, field_name: str = "字段",
                  min_value: float = None, max_value: float = None,
                  required: bool = False) -> Optional[float]:
    """便捷的浮点数验证"""
    if value is None:
        if required:
            raise ValidationError(f"{field_name}是必填的", field_name)
        return None

    try:
        value = float(value)
    except (ValueError, TypeError):
        raise ValidationError(f"{field_name}必须是数字", field_name)

    if min_value is not None and value < min_value:
        raise ValidationError(f"{field_name}不能小于{min_value}", field_name)
    if max_value is not None and value > max_value:
        raise ValidationError(f"{field_name}不能大于{max_value}", field_name)

    return value


def validate_datetime(value: Any, field_name: str = "字段",
                     format: str = '%Y-%m-%d %H:%M:%S',
                     required: bool = False) -> Optional[datetime]:
    """便捷的日期时间验证"""
    if value is None:
        if required:
            raise ValidationError(f"{field_name}是必填的", field_name)
        return None

    if isinstance(value, datetime):
        return value

    if not isinstance(value, str):
        raise ValidationError(f"{field_name}必须是字符串或datetime对象", field_name)

    try:
        return datetime.strptime(value, format)
    except ValueError:
        raise ValidationError(f"{field_name}格式不正确，应为{format}", field_name)