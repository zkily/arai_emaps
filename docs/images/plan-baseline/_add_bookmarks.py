"""plan-baseline.pdf に目次ブックマーク（PDF Outline）を付与する。

HTML→Chrome 印刷で作った PDF には Outline が無いため、補給品管理 PDF と同様に
ビューア左の「ドキュメントのアウトライン」で章ジャンプできるようにする。

使い方:
  py -3 docs/images/plan-baseline/_add_bookmarks.py
"""
from __future__ import annotations

from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parents[3]
PDF = ROOT / "frontend" / "src" / "views" / "manual" / "pdfs" / "plan-baseline.pdf"

# (level, title, search_text) — search_text は本文見出し。目次ページは検索対象外。
BOOKMARKS: list[tuple[int, str, str]] = [
    (1, "はじめに", "1はじめに"),
    (2, "1-1 画面の目的", "1-1画面の目的"),
    (2, "1-2 用語", "1-2用語"),
    (2, "1-3 運用の流れ", "1-3運用の流れ"),
    (1, "画面を開く", "2画面を開く"),
    (1, "画面構成", "3画面構成"),
    (1, "ベースライン生成・削除", "4ベースライン生成・削除"),
    (2, "4-1 ロック", "4-1ロック"),
    (2, "4-2 生成手順", "4-2生成手順"),
    (2, "4-3 削除手順", "4-3削除手順"),
    (1, "基準計画の手入力", "5基準計画の手入力"),
    (1, "比較条件", "6比較条件"),
    (1, "サマリー KPI・期間比較", "7サマリーKPI・期間比較"),
    (1, "日次推移・月間ヒートマップ", "8日次推移・月間ヒートマップ"),
    (2, "8-1 日次推移", "8-1日次推移"),
    (2, "8-2 月間ヒートマップ", "8-2月間ヒートマップ"),
    (1, "ベースライン比較一覧", "9ベースライン比較一覧"),
    (2, "9-1 タブ", "9-1タブ"),
    (2, "9-2 列", "9-2列"),
    (2, "9-3 差分閾値（アラート）", "9-3差分閾値（アラート）"),
    (1, "計画を修正", "10計画を修正"),
    (1, "レポート・Excel・印刷", "11レポート・Excel・印刷"),
    (2, "11-1 レポート印刷", "11-1レポート印刷"),
    (2, "11-2 週次配信", "11-2週次配信"),
    (2, "11-3 Excel 出力", "11-3Excel出力"),
    (2, "11-4 印刷", "11-4印刷"),
    (1, "操作権限（生産計画）", "12操作権限（生産計画）"),
    (1, "メッセージと対処", "13メッセージと対処"),
    (1, "運用上の注意・よくある質問", "14運用上の注意・よくある質問"),
    (2, "Q よくある質問", "よくある質問"),
    (1, "文書情報", "文書情報"),
    (1, "改訂履歴", "改訂履歴"),
]


def find_page(doc: pymupdf.Document, needle: str, start: int = 0) -> int | None:
    for i in range(start, doc.page_count):
        text = doc[i].get_text("text").replace(" ", "").replace("\u3000", "")
        if needle.replace(" ", "") in text:
            return i
    return None


def main() -> None:
    doc = pymupdf.open(PDF)
    toc_page = find_page(doc, "目次")
    body_start = (toc_page + 1) if toc_page is not None else 0

    toc: list[list] = [
        [1, "生産計画ベースライン管理 操作説明書", 1],
        [1, "目次", (toc_page + 1) if toc_page is not None else 2],
    ]

    for level, title, needle in BOOKMARKS:
        # 「よくある質問」は目次にも出るので本文側から探す
        page = find_page(doc, needle, start=body_start)
        if page is None:
            page = find_page(doc, needle, start=0)
        if page is None:
            print(f"WARN not found: {title!r} / {needle!r}")
            continue
        toc.append([level, title, page + 1])
        print(f"L{level} p{page + 1} {title}")

    doc.set_toc(toc)
    doc.saveIncr()
    doc.close()

    verify = pymupdf.open(PDF)
    print("--- verify ---")
    for row in verify.get_toc():
        print(row)
    print("count", len(verify.get_toc()))
    verify.close()


if __name__ == "__main__":
    main()
