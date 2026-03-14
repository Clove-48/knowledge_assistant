# tool_integration.py
# 工具集成模块

import json
import math
from typing import Dict, Any, Optional, List
from datetime import datetime
import requests


class ToolIntegration:
    """工具集成模块"""

    def __init__(self):
        """初始化工具集成"""
        self.tools = {
            "calculator": {
                "name": "计算器",
                "description": "执行数学计算",
                "function": self.calculate,
                "parameters": {
                    "expression": "数学表达式，如 '2 + 3 * 4' 或 'sqrt(16)'"
                }
            },
            "time": {
                "name": "时间查询",
                "description": "获取当前日期和时间",
                "function": self.get_current_time,
                "parameters": {}
            },
            "unit_converter": {
                "name": "单位转换",
                "description": "常用单位转换",
                "function": self.convert_units,
                "parameters": {
                    "value": "数值",
                    "from_unit": "原单位",
                    "to_unit": "目标单位"
                }
            }
        }

        # 单位转换表
        self.unit_conversions = {
            "length": {
                "meter": 1.0,
                "kilometer": 1000.0,
                "centimeter": 0.01,
                "millimeter": 0.001,
                "inch": 0.0254,
                "foot": 0.3048,
                "yard": 0.9144,
                "mile": 1609.34
            },
            "weight": {
                "kilogram": 1.0,
                "gram": 0.001,
                "milligram": 0.000001,
                "pound": 0.453592,
                "ounce": 0.0283495
            },
            "temperature": {
                "celsius": "C",
                "fahrenheit": "F",
                "kelvin": "K"
            }
        }

    def list_tools(self) -> List[Dict[str, Any]]:
        """
        列出所有可用工具

        返回:
            工具列表
        """
        tool_list = []
        for tool_id, tool_info in self.tools.items():
            tool_list.append({
                "id": tool_id,
                "name": tool_info["name"],
                "description": tool_info["description"],
                "parameters": tool_info.get("parameters", {})
            })

        return tool_list

    def execute_tool(self, tool_id: str, **kwargs) -> Dict[str, Any]:
        """
        执行工具

        参数:
            tool_id: 工具ID
            **kwargs: 工具参数

        返回:
            执行结果
        """
        if tool_id not in self.tools:
            return {
                "success": False,
                "error": f"未知工具: {tool_id}",
                "available_tools": list(self.tools.keys())
            }

        tool = self.tools[tool_id]

        try:
            result = tool["function"](**kwargs)

            return {
                "success": True,
                "tool": tool["name"],
                "result": result,
                "parameters": kwargs
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "tool": tool["name"]
            }

    def calculate(self, expression: str) -> Dict[str, Any]:
        """
        计算数学表达式

        参数:
            expression: 数学表达式

        返回:
            计算结果
        """
        # 安全评估表达式
        safe_globals = {
            "__builtins__": {},
            "math": math,
            "sqrt": math.sqrt,
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "log": math.log,
            "log10": math.log10,
            "exp": math.exp,
            "pi": math.pi,
            "e": math.e
        }

        # 移除危险字符
        expression = expression.replace("__", "").replace("import", "").replace("eval", "")
        # 将中文括号替换为英文括号
        expression = expression.replace('（', '(').replace('）', ')')

        try:
            # 使用eval计算，但限制在安全环境
            result = eval(expression, {"__builtins__": {}}, safe_globals)

            return {
                "expression": expression,
                "result": result,
                "formatted": f"{expression} = {result}"
            }

        except Exception as e:
            return {
                "expression": expression,
                "error": f"计算错误: {str(e)}",
                "suggestion": "请检查表达式格式，支持 +, -, *, /, **, sqrt(), sin(), cos() 等"
            }

    def get_current_time(self) -> Dict[str, Any]:
        """
        获取当前时间

        返回:
            时间信息
        """
        now = datetime.now()

        return {
            "datetime": now.isoformat(),
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "weekday": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][now.weekday()],
            "formatted": f"当前时间: {now.strftime('%Y年%m月%d日 %H:%M:%S')} {['周一', '周二', '周三', '周四', '周五', '周六', '周日'][now.weekday()]}"
        }

    def convert_units(self, value: float, from_unit: str, to_unit: str) -> Dict[str, Any]:
        """
        单位转换

        参数:
            value: 数值
            from_unit: 原单位
            to_unit: 目标单位

        返回:
            转换结果
        """
        # 标准化单位名称
        from_unit = from_unit.lower()
        to_unit = to_unit.lower()

        # 温度转换
        if from_unit in self.unit_conversions["temperature"] and to_unit in self.unit_conversions["temperature"]:
            return self._convert_temperature(value, from_unit, to_unit)

        # 查找单位类型
        unit_type = None
        for category, units in self.unit_conversions.items():
            if category != "temperature" and from_unit in units and to_unit in units:
                unit_type = category
                break

        if not unit_type:
            available_units = []
            for category, units in self.unit_conversions.items():
                if category != "temperature":
                    available_units.extend(units.keys())

            return {
                "error": f"不支持的单位转换: {from_unit} -> {to_unit}",
                "available_units": list(set(available_units))
            }

        # 执行转换
        factor_from = self.unit_conversions[unit_type][from_unit]
        factor_to = self.unit_conversions[unit_type][to_unit]

        # 转换到基准单位，再转换到目标单位
        base_value = value * factor_from
        result = base_value / factor_to

        return {
            "value": value,
            "from_unit": from_unit,
            "to_unit": to_unit,
            "result": result,
            "formatted": f"{value} {from_unit} = {result:.4f} {to_unit}"
        }

    def _convert_temperature(self, value: float, from_unit: str, to_unit: str) -> Dict[str, Any]:
        """温度转换"""
        # 先转换到摄氏度
        if from_unit == "celsius":
            celsius = value
        elif from_unit == "fahrenheit":
            celsius = (value - 32) * 5 / 9
        elif from_unit == "kelvin":
            celsius = value - 273.15
        else:
            return {"error": f"未知温度单位: {from_unit}"}

        # 从摄氏度转换到目标单位
        if to_unit == "celsius":
            result = celsius
        elif to_unit == "fahrenheit":
            result = celsius * 9 / 5 + 32
        elif to_unit == "kelvin":
            result = celsius + 273.15
        else:
            return {"error": f"未知温度单位: {to_unit}"}

        return {
            "value": value,
            "from_unit": from_unit,
            "to_unit": to_unit,
            "result": result,
            "formatted": f"{value}°{from_unit[0].upper()} = {result:.2f}°{to_unit[0].upper()}"
        }

    def auto_detect_tool(self, query: str) -> Optional[Dict[str, Any]]:
        """
        自动检测查询是否应使用工具

        参数:
            query: 用户查询

        返回:
            工具调用建议，或None
        """
        query_lower = query.lower()

        # 检测计算请求
        calc_keywords = ["计算", "算一下", "等于多少", "+", "-", "*", "/", "sqrt", "sin", "cos", "tan"]
        if any(keyword in query_lower for keyword in calc_keywords):
            # 提取数学表达式
            import re
            # 匹配更复杂的数学表达式，包括括号和运算符
            # 尝试提取整个表达式，而不仅仅是第一个匹配
            # 移除查询中的非数学字符
            # 保留数字、运算符、括号（包括中文括号）和函数
            # 在字符类中，'-'放在最后避免被解释为范围
            cleaned_query = re.sub(r'[^0-9+*/().^√πe\s（）-]', '', query)
            # 移除多余的空格
            cleaned_query = re.sub(r'\s+', '', cleaned_query)
            # 将中文括号替换为英文括号
            cleaned_query = cleaned_query.replace('（', '(').replace('）', ')')
            
            # 确保表达式包含运算符
            if any(op in cleaned_query for op in ['+', '-', '*', '/', '^', '√']):
                return {
                    "tool_id": "calculator",
                    "parameters": {"expression": cleaned_query},
                    "confidence": 0.8
                }

        # 检测时间请求
        time_keywords = ["现在几点", "当前时间", "今天日期", "星期几", "什么时间"]
        if any(keyword in query_lower for keyword in time_keywords):
            return {
                "tool_id": "time",
                "parameters": {},
                "confidence": 0.9
            }

        # 检测单位转换
        convert_keywords = ["转换", "换算", "等于多少", "转成"]
        unit_keywords = ["米", "千米", "厘米", "公斤", "克", "磅", "摄氏度", "华氏度"]

        if any(keyword in query_lower for keyword in convert_keywords):
            if any(unit in query_lower for unit in unit_keywords):
                # 这里可以更复杂地解析单位和数值
                return {
                    "tool_id": "unit_converter",
                    "parameters": {},
                    "confidence": 0.7
                }

        return None


def test_tool_integration():
    """测试工具集成"""
    print("测试工具集成")
    print("=" * 60)

    # 创建工具集成
    tools = ToolIntegration()

    # 列出工具
    print("1. 可用工具:")
    tool_list = tools.list_tools()
    for tool in tool_list:
        print(f"  - {tool['name']}: {tool['description']}")

    # 测试计算器
    print("\n2. 测试计算器:")
    result = tools.execute_tool("calculator", expression="2 + 3 * 4")
    if result["success"]:
        print(f"  ✅ {result['result']['formatted']}")
    else:
        print(f"  ❌ {result['error']}")

    # 测试时间
    print("\n3. 测试时间查询:")
    result = tools.execute_tool("time")
    if result["success"]:
        print(f"  ✅ {result['result']['formatted']}")

    # 测试单位转换
    print("\n4. 测试单位转换:")
    result = tools.execute_tool("unit_converter", value=10, from_unit="kilometer", to_unit="meter")
    if result["success"]:
        print(f"  ✅ {result['result']['formatted']}")

    # 测试温度转换
    print("\n5. 测试温度转换:")
    result = tools.execute_tool("unit_converter", value=100, from_unit="celsius", to_unit="fahrenheit")
    if result["success"]:
        print(f"  ✅ {result['result']['formatted']}")

    # 测试自动检测
    print("\n6. 测试工具自动检测:")
    test_queries = [
        "计算一下 2 + 3 * 4 等于多少",
        "现在几点钟",
        "10公里等于多少米"
    ]

    for query in test_queries:
        suggestion = tools.auto_detect_tool(query)
        if suggestion:
            print(f"  '{query}' -> 建议使用: {suggestion['tool_id']} (置信度: {suggestion['confidence']})")
        else:
            print(f"  '{query}' -> 无工具建议")

    print("\n" + "=" * 60)
    print("✅ 工具集成测试完成！")
    print("=" * 60)

    return tools


if __name__ == "__main__":
    test_tool_integration()