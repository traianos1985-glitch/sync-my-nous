"""Offline, deterministic utility tools exposed through the NOUS command interface."""
from __future__ import annotations

import ast
import hashlib
import json
import math
import operator
import re
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


_MAX_EXPRESSION_LENGTH = 300
_MAX_AST_NODES = 80
_MAX_EXPONENT = 100
_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARY_OPS = {ast.UAdd: operator.pos, ast.USub: operator.neg}
_FUNCTIONS = {
    "abs": abs,
    "min": min,
    "max": max,
    "round": round,
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "log": math.log,
    "log10": math.log10,
}
_CONSTANTS = {"pi": math.pi, "e": math.e}

_UNIT_GROUPS = {
    "length": {
        "m": 1.0, "meter": 1.0, "meters": 1.0, "metre": 1.0, "metres": 1.0,
        "km": 1000.0, "kilometer": 1000.0, "kilometers": 1000.0, "kilometre": 1000.0,
        "cm": 0.01, "mm": 0.001, "mi": 1609.344, "mile": 1609.344, "miles": 1609.344,
        "ft": 0.3048, "foot": 0.3048, "feet": 0.3048, "in": 0.0254, "inch": 0.0254, "inches": 0.0254,
    },
    "mass": {
        "kg": 1.0, "kilogram": 1.0, "kilograms": 1.0, "g": 0.001, "gram": 0.001,
        "grams": 0.001, "mg": 0.000001, "lb": 0.45359237, "lbs": 0.45359237,
        "pound": 0.45359237, "pounds": 0.45359237, "oz": 0.028349523125, "ounce": 0.028349523125,
    },
    "volume": {
        "l": 1.0, "liter": 1.0, "litre": 1.0, "liters": 1.0, "litres": 1.0,
        "ml": 0.001, "milliliter": 0.001, "millilitre": 0.001,
        "m3": 1000.0, "m³": 1000.0, "gal": 3.785411784, "gallon": 3.785411784, "gallons": 3.785411784,
    },
    "speed": {
        "m/s": 1.0, "mps": 1.0, "km/h": 1 / 3.6, "kph": 1 / 3.6,
        "mph": 0.44704, "ft/s": 0.3048,
    },
}


def _finite_number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("numeric_value_required")
    if not math.isfinite(value):
        raise ValueError("non_finite_result")
    return value


def _eval_node(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
        return _finite_number(node.value)
    if isinstance(node, ast.Name):
        if node.id in _CONSTANTS:
            return _CONSTANTS[node.id]
        raise ValueError("unknown_constant")
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPS:
        return _finite_number(_UNARY_OPS[type(node.op)](_eval_node(node.operand)))
    if isinstance(node, ast.BinOp) and type(node.op) in _BIN_OPS:
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > _MAX_EXPONENT:
            raise ValueError("exponent_limit_exceeded")
        return _finite_number(_BIN_OPS[type(node.op)](left, right))
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in _FUNCTIONS:
        if node.keywords:
            raise ValueError("keyword_arguments_not_supported")
        args = [_eval_node(arg) for arg in node.args]
        return _finite_number(_FUNCTIONS[node.func.id](*args))
    raise ValueError("expression_syntax_not_allowed")


def calculate(expression: str) -> dict:
    expression = str(expression).strip()
    if not expression or len(expression) > _MAX_EXPRESSION_LENGTH:
        return {"ok": False, "error": "expression_empty_or_too_long"}
    try:
        tree = ast.parse(expression, mode="eval")
        if sum(1 for _ in ast.walk(tree)) > _MAX_AST_NODES:
            raise ValueError("expression_too_complex")
        result = _eval_node(tree.body)
        return {"ok": True, "expression": expression, "result": result}
    except (ValueError, TypeError, SyntaxError, ArithmeticError, OverflowError) as exc:
        return {"ok": False, "expression": expression, "error": str(exc) or "calculation_failed"}


def _temperature_to_kelvin(value, unit):
    if unit in {"c", "°c", "celsius"}:
        return value + 273.15
    if unit in {"f", "°f", "fahrenheit"}:
        return (value - 32) * 5 / 9 + 273.15
    if unit in {"k", "kelvin"}:
        return value
    raise ValueError("unknown_temperature_unit")


def _kelvin_to_temperature(value, unit):
    if unit in {"c", "°c", "celsius"}:
        return value - 273.15
    if unit in {"f", "°f", "fahrenheit"}:
        return (value - 273.15) * 9 / 5 + 32
    if unit in {"k", "kelvin"}:
        return value
    raise ValueError("unknown_temperature_unit")


def convert_units(value, source_unit, target_unit) -> dict:
    try:
        amount = _finite_number(float(value))
        source = str(source_unit).strip().lower()
        target = str(target_unit).strip().lower()
        if source in {"c", "°c", "celsius", "f", "°f", "fahrenheit", "k", "kelvin"}:
            result = _kelvin_to_temperature(_temperature_to_kelvin(amount, source), target)
            if _temperature_to_kelvin(result, target) < 0:
                raise ValueError("temperature_below_absolute_zero")
            group = "temperature"
        else:
            group = next(
                (name for name, units in _UNIT_GROUPS.items() if source in units and target in units),
                None,
            )
            if group is None:
                raise ValueError("incompatible_or_unknown_units")
            result = amount * _UNIT_GROUPS[group][source] / _UNIT_GROUPS[group][target]
        if not math.isfinite(result):
            raise ValueError("non_finite_result")
        return {
            "ok": True, "value": amount, "from": source_unit, "to": target_unit,
            "result": result, "group": group,
        }
    except (ValueError, TypeError, OverflowError) as exc:
        return {"ok": False, "error": str(exc) or "conversion_failed"}


def parse_conversion(command: str) -> dict:
    match = re.fullmatch(
        r"\s*([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[-+]?\d+)?)\s+(.+?)\s+(?:to|σε|σε\s+)\s+(.+?)\s*",
        str(command), flags=re.IGNORECASE,
    )
    if not match:
        return {"ok": False, "error": "usage: convert 12 km to miles"}
    return convert_units(match.group(1), match.group(2), match.group(3))


def current_time(zone: str = "") -> dict:
    zone = str(zone or "").strip()
    try:
        if zone:
            tz = ZoneInfo(zone)
            now = datetime.now(tz)
            zone_name = zone
        else:
            now = datetime.now().astimezone()
            zone_name = str(now.tzinfo or "local")
        return {
            "ok": True,
            "timezone": zone_name,
            "iso": now.isoformat(timespec="seconds"),
            "date": now.date().isoformat(),
            "time": now.strftime("%H:%M:%S"),
            "utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
    except (ZoneInfoNotFoundError, ValueError, OSError):
        return {"ok": False, "error": "unknown_timezone", "timezone": zone}


def text_stats(text: str) -> dict:
    value = str(text)
    words = re.findall(r"\b[\w’'-]+\b", value, flags=re.UNICODE)
    lines = value.splitlines()
    return {
        "ok": True,
        "characters": len(value),
        "characters_without_whitespace": sum(not ch.isspace() for ch in value),
        "words": len(words),
        "lines": len(lines) if value else 0,
        "paragraphs": len([part for part in re.split(r"\n\s*\n", value.strip()) if part]) if value.strip() else 0,
    }


def validate_json_text(text: str) -> dict:
    try:
        value = json.loads(str(text))
        return {
            "ok": True,
            "valid": True,
            "type": type(value).__name__,
            "top_level_items": len(value) if isinstance(value, (dict, list, str)) else None,
        }
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        return {
            "ok": True,
            "valid": False,
            "error": "invalid_json",
            "line": getattr(exc, "lineno", None),
            "column": getattr(exc, "colno", None),
            "details": str(exc),
        }


def sha256_text(text: str) -> dict:
    value = str(text)
    return {"ok": True, "algorithm": "sha256", "sha256": hashlib.sha256(value.encode("utf-8")).hexdigest(), "characters": len(value)}
