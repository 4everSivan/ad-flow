"""安装校验器的 Python 3.7 兼容性守卫（维护者资产，不安装到目标项目）。

目标项目可能运行较旧的解释器，而维护者本地与 CI 主矩阵是 3.9+。
这里用 AST 静态检查 ``scripts/adflow_verify.py`` 的语法与标准库下限，
避免安装资产悄悄用上 3.8+ 才有的语法或 API。
"""
import ast
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TOOL = REPO / "scripts/adflow_verify.py"
TARGET = (3, 7)

# 3.8+ 新增的标准库模块：导入即不兼容。
POST_37_MODULES = {
    "importlib.metadata": "3.8",
    "zoneinfo": "3.9",
    "graphlib": "3.9",
    "tomllib": "3.11",
}

# 以模块属性或 from-import 形式使用的 3.8+ API（键为完整限定名）。
POST_37_QUALIFIED = {
    "functools.cache": "3.9",
    "functools.cached_property": "3.8",
    "math.lcm": "3.9",
    "math.prod": "3.8",
    "ast.unparse": "3.9",
    "ast.get_source_segment": "3.8",
    "shlex.join": "3.8",
    "random.randbytes": "3.9",
}

# 只按方法名识别：这些名字足够特定，不会误伤普通业务字段。
POST_37_METHODS = {
    "is_relative_to": "3.9",  # pathlib.Path
    "with_stem": "3.9",       # pathlib.Path
    "hardlink_to": "3.10",    # pathlib.Path
    "removeprefix": "3.9",    # str
    "removesuffix": "3.9",    # str
}

# 以关键字参数形式出现的新增能力。
POST_37_KEYWORDS = {
    "missing_ok": "3.8",    # Path.unlink / Path.readlink
    "dirs_exist_ok": "3.8",  # shutil.copytree / shutil.move
}


def _import_aliases(tree):
    """把 import 绑定映射到完整限定名，识别 ``import math as m`` 这类别名。"""
    aliases = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for name in node.names:
                aliases[name.asname or name.name] = name.name
        elif isinstance(node, ast.ImportFrom) and node.module:
            for name in node.names:
                aliases[name.asname or name.name] = "%s.%s" % (node.module, name.name)
    return aliases


def scan_python37(source):
    """返回 ``[(行号, 说明)]``，说明中标出该 API 的最低 Python 版本。"""
    tree = ast.parse(source)
    aliases = _import_aliases(tree)
    findings = []

    def report(lineno, name, version):
        findings.append((lineno, "%s 需要 Python %s+" % (name, version)))

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for name in node.names:
                if name.name in POST_37_MODULES:
                    report(node.lineno, name.name, POST_37_MODULES[name.name])
        elif isinstance(node, ast.ImportFrom) and node.module:
            for name in node.names:
                qualified = "%s.%s" % (node.module, name.name)
                if qualified in POST_37_MODULES:
                    report(node.lineno, qualified, POST_37_MODULES[qualified])
                elif qualified in POST_37_QUALIFIED:
                    report(node.lineno, qualified, POST_37_QUALIFIED[qualified])
        elif isinstance(node, ast.Attribute):
            if node.attr in POST_37_METHODS:
                report(node.lineno, "." + node.attr, POST_37_METHODS[node.attr])
                continue
            if isinstance(node.value, ast.Name):
                module = aliases.get(node.value.id)
                qualified = "%s.%s" % (module, node.attr) if module else None
                if qualified in POST_37_QUALIFIED:
                    report(node.lineno, qualified, POST_37_QUALIFIED[qualified])
        elif isinstance(node, ast.Name):
            qualified = aliases.get(node.id)
            if qualified in POST_37_QUALIFIED:
                report(node.lineno, qualified, POST_37_QUALIFIED[qualified])
        elif isinstance(node, ast.Call):
            # keyword 节点在 3.9 之前没有 lineno，用所在调用行报告。
            for keyword in node.keywords:
                if keyword.arg in POST_37_KEYWORDS:
                    report(node.lineno, keyword.arg + "=", POST_37_KEYWORDS[keyword.arg])

    return sorted(set(findings))


class Python37CompatibilityTests(unittest.TestCase):
    def setUp(self):
        self.source = TOOL.read_text(encoding="utf-8")

    def test_verifier_parses_as_python37(self):
        try:
            # feature_version 是 3.8+ 的参数；在真正的 3.7 上原生解析即可完成同等约束。
            if sys.version_info >= (3, 8):
                ast.parse(self.source, feature_version=TARGET)
            else:
                ast.parse(self.source)
        except SyntaxError as exc:
            self.fail("scripts/adflow_verify.py 使用了 Python 3.8+ 语法：%s" % exc)

    def test_verifier_avoids_post_37_stdlib(self):
        findings = scan_python37(self.source)
        detail = "\n".join("第 %d 行：%s" % item for item in findings)
        self.assertEqual(findings, [], "安装校验器需保持 Python 3.7+ 兼容：\n" + detail)

    def test_guard_detects_post_37_apis(self):
        sample = "\n".join([
            "import zoneinfo",
            "from functools import cache",
            "from pathlib import Path",
            "Path('a').is_relative_to('b')",
            "'x'.removeprefix('x')",
            "Path('a').unlink(missing_ok=True)",
        ])
        messages = "\n".join(message for _, message in scan_python37(sample))
        for expected in ("zoneinfo", "cache", "is_relative_to", "removeprefix", "missing_ok"):
            self.assertIn(expected, messages)


if __name__ == "__main__":
    unittest.main()
