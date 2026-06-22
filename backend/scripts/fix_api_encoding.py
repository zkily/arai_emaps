"""Restore Japanese text in production_schedule/api.py from release/1.0.2 reference."""
from __future__ import annotations

import difflib
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAIN_PATH = ROOT / "backend/app/modules/production_schedule/api.py"
RELEASE_REF = "release/1.0.2:backend/app/modules/production_schedule/api.py"

JP_RE = re.compile(r"[\u3040-\u30ff\u4e00-\u9fff]")
Q_RE = re.compile(r"\?+")
LIT_RE = re.compile(r'("""[\s\S]*?"""|f?"[^"\n]*"|f?\'[^\n\']*\')')


def string_skeleton(text: str) -> str:
    return JP_RE.sub("\x00", text).replace("?", "\x00")


def load_release() -> str:
    data = subprocess.check_output(["git", "show", RELEASE_REF], cwd=ROOT)
    return data.decode("utf-8")


def fuzzy_line_fix(main: str, release: str, threshold: float) -> tuple[str, int]:
    rel_lines = [line for line in release.splitlines() if JP_RE.search(line) and "?" not in line]
    rel_sk = [(string_skeleton(line), line) for line in rel_lines]
    fixed = 0
    out: list[str] = []
    for line in main.splitlines():
        if not Q_RE.search(line):
            out.append(line)
            continue
        key = string_skeleton(line)
        best = None
        score = 0.0
        for rel_key, rel_line in rel_sk:
            ratio = difflib.SequenceMatcher(None, key, rel_key).ratio()
            if ratio > score:
                score = ratio
                best = rel_line
        if best and score >= threshold:
            indent = line[: len(line) - len(line.lstrip())]
            body = best.lstrip()
            out.append(indent + body)
            fixed += 1
        else:
            out.append(line)
    text = "\n".join(out)
    if main.endswith("\n"):
        text += "\n"
    return text, fixed


def literal_fix(main: str, release: str) -> tuple[str, int]:
    str_map: dict[str, str] = {}
    for match in LIT_RE.finditer(release):
        literal = match.group(1)
        if not JP_RE.search(literal) or "?" in literal:
            continue
        key = string_skeleton(literal)
        if "\x00" in key:
            str_map[key] = literal

    fixed = 0

    def repl(match: re.Match[str]) -> str:
        nonlocal fixed
        literal = match.group(1)
        if "?" not in literal:
            return literal
        key = string_skeleton(literal)
        if key in str_map:
            fixed += 1
            return str_map[key]
        return literal

    return LIT_RE.sub(repl, main), fixed


def apply_manual_replacements(text: str) -> str:
    replacements = [
        ("03?07", "03〜07"),
        ("03?06", "03〜06"),
        ('detail="対象のメモが見つかりません????????????"', 'detail="対象のメモが見つかりません"'),
        ("# MES ????????????? 03〜07???? DB ???? SQL ?????", "# MES 実績列の参照可否（03〜07 系）を DB から見て SQL 断片を組み立て"),
        (
            '"""Asia/Tokyo?Windows ?? tzdata ??????? UTC+9 ????????? DST ????"""',
            '"""Asia/Tokyo（Windows で tzdata が無い場合は固定 UTC+9 オフセットを使う。DST は考慮しない）"""',
        ),
        (
            '"""cutting_management ??????????????????? SQL ??????????"""',
            '"""cutting_management の既存列名を information_schema から取得（MES 列の有無判定用）"""',
        ),
        (
            '"""?????????????? MES ???????????????????????"""',
            '"""同一切断機で他行の MES 生産が未完了なら 409 を返す"""',
        ),
        ("# ???????? checkpoint ???????????????????", "# 検査系 checkpoint / ロック用の列存在チェック"),
        (
            '"""chamfering_management ??????????????????? SQL ??????????"""',
            '"""chamfering_management の既存列名を information_schema から取得"""',
        ),
        (
            '"""?? API ???????????`**item` ????????? JSON / ??????????????"""',
            '"""検査 API 向け: 不良項目 `**item` 列をパースして JSON / フラット形式に正規化"""',
        ),
        (
            'f"? `{column}` ???????"',
            'f"列 `{column}` が未作成です。"',
        ),
        (
            '"backend/database/migrations/12_inspection_management_mes_client_instance.sql ??????????"',
            '"backend/database/migrations/12_inspection_management_mes_client_instance.sql を実行してください。"',
        ),
        (
            '"backend/database/migrations/52_inspection_mes_client_lock_activity.sql ??????????"',
            '"backend/database/migrations/52_inspection_mes_client_lock_activity.sql を実行してください。"',
        ),
        (
            '"""process_defect_items ?? defect_cd ? defect_name ????"""',
            '"""process_defect_items から defect_cd と defect_name を取得"""',
        ),
        (
            '"""checkpoint ???????????? mes_client_instance_id ??????"""',
            '"""checkpoint 更新時に mes_client_instance_id を必須化"""',
        ),
        (
            '"""dict / JSON ???? MySQL JSON ???????????"""',
            '"""dict / JSON 文字列を MySQL JSON カラム用に正規化"""',
        ),
        (
            '"""ISO 8601 ???? Asia/Tokyo ?????????????????????? MySQL DATETIME ??????"""',
            '"""ISO 8601 文字列を Asia/Tokyo として解釈し、naive な MySQL DATETIME 文字列へ変換"""',
        ),
        (
            '"""??????instruction_plans?1???????????????"',
            '"""指定月の instruction_plans を1件ずつ切断指示へ展開"""',
        ),
        (
            'detail="cutting_management ????????????backend/database/migrations/03〜06_cutting_management_mes_*.sql ??????????"',
            'detail="cutting_management テーブルが存在しません。backend/database/migrations/03〜06_cutting_management_mes_*.sql を実行してください"',
        ),
        (
            "stock_transaction_logs ??????????????????????????????",
            "stock_transaction_logs へ切断実績を登録（同日・同ロットは一旦削除してから再登録）",
        ),
        (
            "# ?????????????????source_file=cutting_management & ?? & ??????????",
            "# 同日削除条件: source_file=cutting_management & 工程 & 管理コード一致",
        ),
        (
            "# ??????????????1???????????????????????????????",
            "# 同一製品・同一設備・同一日の既存行があれば 1 件に集約（数量加算・順序は最小）",
        ),
        (
            "# - ???????????????????????release_cancelled_*?",
            "# - キャンセル済み行は release_cancelled_* フラグで除外",
        ),
        ("mes_production_started_at: Optional[str] = None  # ISO8601?????????", "mes_production_started_at: Optional[str] = None  # ISO8601（生産開始）"),
        ("mes_production_ended_at: Optional[str] = None  # ISO8601?????????", "mes_production_ended_at: Optional[str] = None  # ISO8601（生産終了）"),
        ("mes_net_production_sec: Optional[int] = None  # ????????????", "mes_net_production_sec: Optional[int] = None  # 正味生産時間（秒）"),
        ("mes_paused_accum_sec: Optional[int] = None  # ???????", "mes_paused_accum_sec: Optional[int] = None  # 中断累計（秒）"),
        ("mes_production_is_paused: Optional[int] = None  # 0=???, 1=????????/??? NULL?", "mes_production_is_paused: Optional[int] = None  # 0=稼働中, 1=中断中（未設定は NULL）"),
        ("mes_setup_time_min: Optional[int] = None  # ?????", "mes_setup_time_min: Optional[int] = None  # 段取（分）"),
        ("mes_saw_blade_exchange_min: Optional[int] = None  # ???????", "mes_saw_blade_exchange_min: Optional[int] = None  # のこ刃交換（分）"),
        ("mes_repair_min: Optional[int] = None  # ?????", "mes_repair_min: Optional[int] = None  # 修理（分）"),
        ("mes_operator_user_id: Optional[int] = None  # users.id?0???????", "mes_operator_user_id: Optional[int] = None  # users.id（0 は未設定扱い）"),
        ("mes_scanned_code: Optional[str] = None  # ?????/QR ???????????", "mes_scanned_code: Optional[str] = None  # バーコード/QR 読取値（任意）"),
        ("????1???????????????????????", "指定日の切断実績を一括確定し在庫へ反映"),
        ("mes_production_is_paused: Optional[int] = None  # 0=???, 1=????", "mes_production_is_paused: Optional[int] = None  # 0=稼働中, 1=中断中"),
        ("# ---------- ?????inspection_management??MES?????? ----------", "# ---------- 検査（inspection_management）MES 実績 API ----------"),
        ('detail="data_source ? mes / excel / csv ???????"', 'detail="data_source は mes / excel / csv のいずれかです"'),
        (
            'detail="data_source ????????backend/database/migrations/43_inspection_management_data_source.sql ??????????"',
            'detail="data_source 列が未作成です。backend/database/migrations/43_inspection_management_data_source.sql を実行してください"',
        ),
        ('hide_completed: bool = Query(False, description="????????")', 'hide_completed: bool = Query(False, description="完了分を非表示")'),
        ('None, description="???????: mes / excel / csv"', 'None, description="データソース: mes / excel / csv"'),
        ('"""inspection_management ????????????users ????"""', '"""inspection_management 一覧（検査員 users を JOIN）"""'),
        ('detail="start_date / end_date ?????"', 'detail="start_date / end_date が不正です"'),
        ('_INSPECTION_MES_PRODUCT_NAME_EXCLUDES = ("??", "???")', '_INSPECTION_MES_PRODUCT_NAME_EXCLUDES = ("試作", "サンプル")'),
        ('_INSPECTION_SHIAGE_SECTION_NAME = "???"', '_INSPECTION_SHIAGE_SECTION_NAME = "仕上"'),
        (
            'detail="inspection_inspector_next_assignment ????????????backend/database/migrations/48_inspection_inspector_next_assignment.sql ??????????"',
            'detail="inspection_inspector_next_assignment テーブルが存在しません。backend/database/migrations/48_inspection_inspector_next_assignment.sql を実行してください"',
        ),
        ('return {"success": True, "data": saved, "message": "??????????"}', 'return {"success": True, "data": saved, "message": "検査員割当を保存しました"}'),
        ('start_date: str = Query(..., description="????? YYYY-MM-DD")', 'start_date: str = Query(..., description="開始日 YYYY-MM-DD")'),
        ('end_date: str = Query(..., description="????? YYYY-MM-DD")', 'end_date: str = Query(..., description="終了日 YYYY-MM-DD")'),
        ('mes_inspector_user_id: Optional[int] = Query(None, description="??? users.id")', 'mes_inspector_user_id: Optional[int] = Query(None, description="検査員 users.id")'),
        ('include_incomplete: bool = Query(False, description="????????????")', 'include_incomplete: bool = Query(False, description="未完了セッションを含む")'),
        ('"""??????????inspection_management ????"""', '"""検査能率分析（inspection_management 集計）"""'),
        ('use_company_calendar: bool = Query(True, description="????????????")', 'use_company_calendar: bool = Query(True, description="会社カレンダーで稼働日換算")'),
        ('"""??????????inspection_management ? ??7.6h/? ? ???????????"""', '"""検査生産性（inspection_management × 標準7.6h/日 × カレンダー）"""'),
        ('data_gaps.append(f"????????????? {unassigned_session_count} ?????")', 'data_gaps.append(f"検査員未割当セッションが {unassigned_session_count} 件あります")'),
        ('data_gaps.append(f"??????????????????? {sessions_without_time_count} ?????")', 'data_gaps.append(f"作業時間未入力のセッションが {sessions_without_time_count} 件あります")'),
        ('data_gaps.append("????????????????????????????????????????")', 'data_gaps.append("検査員勤務マスタまたは会社カレンダーが未設定のため、一部指標は参考値です")'),
        ('"""?????????inspection_management ? ??? ? ??? ? ??????"""', '"""検査不良分析（inspection_management × 工程 × 不良 × 検査員）"""'),
        ('mes_operator_user_id: Optional[int] = Query(None, description="????? users.id")', 'mes_operator_user_id: Optional[int] = Query(None, description="作業者 users.id")'),
        ('return {"success": True, "data": {"id": new_id}, "message": "??????"}', 'return {"success": True, "data": {"id": new_id}, "message": "登録しました"}'),
        (
            'detail="manual_registration_note ????????backend/database/migrations/47_inspection_management_manual_registration_note.sql ??????????"',
            'detail="manual_registration_note 列が未作成です。backend/database/migrations/47_inspection_management_manual_registration_note.sql を実行してください"',
        ),
        ('detail="mes_client_instance_id ?????"', 'detail="mes_client_instance_id が未設定です"'),
        ("# ---------- ?????welding_management??MES?????? ----------", "# ---------- 溶接（welding_management）MES 実績 API ----------"),
        (
            'detail="? `welding_machine` ???????backend/database/migrations/14_welding_management_welding_machine.sql ??????????"',
            'detail="列 `welding_machine` が未作成です。backend/database/migrations/14_welding_management_welding_machine.sql を実行してください"',
        ),
        (
            'detail="manual_registration_note ????????backend/database/migrations/57_welding_management_manual_registration_note.sql ??????????"',
            'detail="manual_registration_note 列が未作成です。backend/database/migrations/57_welding_management_manual_registration_note.sql を実行してください"',
        ),
        ('"""??????????welding_management ????"""', '"""溶接能率分析（welding_management 集計）"""'),
        ('data_gaps.append(f"??????????????? {unassigned_session_count} ?????")', 'data_gaps.append(f"作業者未割当セッションが {unassigned_session_count} 件あります")'),
        ('detail="product_cd ?????????"', 'detail="product_cd が未指定です"'),
        ('detail="inspector_user_id ?????"', 'detail="inspector_user_id が未設定です"'),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    return text


def ascii_skeleton(text: str) -> str:
    return JP_RE.sub("", text).replace("?", "")


def safe_line_fix(main: str, release: str) -> tuple[str, int]:
    """Replace lines only when ASCII structure matches exactly (preserves indentation)."""
    rel_map: dict[str, list[str]] = {}
    for line in release.splitlines():
        if not JP_RE.search(line) or "?" in line:
            continue
        key = ascii_skeleton(line)
        if key.strip():
            rel_map.setdefault(key, []).append(line)

    fixed = 0
    out: list[str] = []
    for line in main.splitlines():
        if not Q_RE.search(line):
            out.append(line)
            continue
        key = ascii_skeleton(line)
        cands = rel_map.get(key, [])
        if len(cands) == 1:
            indent = line[: len(line) - len(line.lstrip())]
            body = cands[0].lstrip()
            out.append(indent + body)
            fixed += 1
        else:
            out.append(line)

    text = "\n".join(out)
    if main.endswith("\n"):
        text += "\n"
    return text, fixed


def main() -> None:
    release = load_release()
    main_text = MAIN_PATH.read_text(encoding="utf-8")
    before = main_text.count("???")

    main_text, safe_fixes = safe_line_fix(main_text, release)
    main_text, fuzzy_fixes = fuzzy_line_fix(main_text, release, 0.85)
    main_text, lit_fixes = literal_fix(main_text, release)
    main_text = apply_manual_replacements(main_text)

    # 用户可见占位符（release 分支无对应新增代码）
    placeholder_fixes = [
        ('"inspector_name": "??"', '"inspector_name": "合計"'),
        ('finalized["inspector_name"] = "??"', 'finalized["inspector_name"] = "合計"'),
        ('inspector_name="??"', 'inspector_name="応援"'),
        ('inspector_name = "?"', 'inspector_name = "未割当"'),
        ('operator_name = "?"', 'operator_name = "未割当"'),
        ('else "?")', 'else "—")'),
        ('or "?"', 'or "—"'),
        ('return "?"', 'return "不明"'),
        ("production_day: Optional[str] = None  # YYYY-MM-DD ? start_date/end_date", "production_day: Optional[str] = None  # YYYY-MM-DD（未指定時は start_date/end_date から導出）"),
        ("production_order: Optional[int] = None  # ? priority_order", "production_order: Optional[int] = None  # ← priority_order"),
        ("# process_type='cutting' ? source_id = cutting_management.id", "# process_type='cutting' の source_id = cutting_management.id"),
        ('detail="???????????????????"', 'detail="生産完了済みのため切断機を変更できません"'),
        ('detail="?????????????????"', 'detail="生産中のため切断機を変更できません"'),
    ]
    for old, new in placeholder_fixes:
        main_text = main_text.replace(old, new)

    after = main_text.count("???")
    print(f"before={before} safe={safe_fixes} fuzzy={fuzzy_fixes} literal={lit_fixes} after={after}")
    if after:
        shown = 0
        for idx, line in enumerate(main_text.splitlines(), 1):
            if "???" in line:
                print(f"  L{idx}: {line[:140]}")
                shown += 1
                if shown >= 25:
                    break

    MAIN_PATH.write_text(main_text, encoding="utf-8")
    print(f"Wrote {MAIN_PATH}")


if __name__ == "__main__":
    main()
