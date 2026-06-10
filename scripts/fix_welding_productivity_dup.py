# -*- coding: utf-8 -*-
from pathlib import Path

p = Path(__file__).resolve().parents[1] / "backend/app/modules/production_schedule/api.py"
text = p.read_text(encoding="utf-8")
marker = '@router.get("/plan/welding-management/productivity-analysis")'
parts = text.split(marker)
print("parts", len(parts))
if len(parts) <= 2:
    print("no duplicates")
else:
    last_block = parts[-1]
    end_idx = last_block.find("\n\n@router.")
    if end_idx != -1:
        last_block = last_block[:end_idx]
    new_text = parts[0] + marker + last_block
    p.write_text(new_text, encoding="utf-8")
    print("removed", len(parts) - 2, "duplicate blocks")
