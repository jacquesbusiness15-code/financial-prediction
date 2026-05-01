import ast
import pathlib

src = pathlib.Path("src/i18n.py").read_text(encoding="utf-8")
tree = ast.parse(src)
keys = set()
for node in ast.walk(tree):
    if isinstance(node, ast.Dict):
        for k in node.keys:
            if isinstance(k, ast.Constant) and isinstance(k.value, str) and "." in k.value:
                keys.add(k.value)

all_src = ""
for p in pathlib.Path(".").rglob("*.py"):
    ps = p.as_posix()
    if ".venv" in ps or "__pycache__" in ps or ps.endswith("src/i18n.py") or ps.endswith("_scan_unused.py"):
        continue
    try:
        all_src += p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        pass
for p in pathlib.Path(".").rglob("*.html"):
    if ".venv" in p.as_posix():
        continue
    try:
        all_src += p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        pass

unused = sorted(k for k in keys if k not in all_src)
print(f"Total keys: {len(keys)}")
print(f"Unused: {len(unused)}")
for k in unused:
    print(k)
