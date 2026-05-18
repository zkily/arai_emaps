"""Insert mesWeldingActual locale block from mesInspectionActual in locale files."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "frontend/src/locales"
FILES = ["ja.ts", "zh.ts", "en.ts", "vi.ts"]

REPL = [
    ("mesInspectionActual", "mesWeldingActual"),
    ("検査実績収集", "溶接実績収集"),
    ("検査員", "溶接作業者"),
    ("検査製品", "溶接製品"),
    ("検査指示", "溶接指示"),
    ("検査生産", "溶接生産"),
    ("inspection_management", "welding_management"),
    ("KT09", "KT07"),
    ("检查实绩", "焊接实绩"),
    ("检查员", "焊接作业员"),
    ("检查产品", "焊接产品"),
    ("检查指示", "焊接指示"),
    ("检查生产", "焊接生产"),
    ("Inspection — actual collection", "Welding — actual collection"),
    ("Inspector", "Operator"),
    ("inspection product", "welding product"),
    ("Inspection product", "Welding product"),
    ("loadInspectorsFailed", "loadOperatorsFailed"),
    ("thi công kiểm tra", "thi công hàn"),
    ("Kiểm tra", "Hàn"),
    ("kiểm tra", "hàn"),
]

for name in FILES:
    path = ROOT / name
    text = path.read_text(encoding="utf-8")
    if "mesWeldingActual:" in text:
        print(name, "skip")
        continue
    m = re.search(r"  mesInspectionActual: \{.*?\n  \},", text, re.DOTALL)
    if not m:
        print(name, "NOT FOUND")
        continue
    block = m.group(0)
    for a, b in REPL:
        block = block.replace(a, b)
    block = block.replace("mesInspectionActual", "mesWeldingActual")
    insert_at = m.end()
    text = text[:insert_at] + "\n" + block + text[insert_at:]
    path.write_text(text, encoding="utf-8")
    print(name, "ok")
