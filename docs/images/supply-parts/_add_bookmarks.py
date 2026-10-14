"""supply-parts.pdf に目次ブックマーク（PDF Outline）を付与する。"""
from __future__ import annotations

from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parents[3]
PDF = ROOT / "frontend" / "src" / "views" / "manual" / "pdfs" / "supply-parts.pdf"

BOOKMARKS: list[tuple[int, str, str]] = [
    (1, "はじめに", "1はじめに"),
    (2, "1-1 画面の目的", "1-1画面の目的"),
    (2, "1-2 台帳の考え方", "1-2台帳の考え方"),
    (2, "1-3 用語", "1-3用語"),
    (1, "画面を開く", "2画面を開く"),
    (1, "画面構成", "3画面構成"),
    (2, "3-1 操作ボタン", "3-1操作ボタン"),
    (1, "在庫一覧の見方", "4在庫一覧の見方"),
    (2, "4-1 集計カード", "4-1集計カード"),
    (2, "4-2 条件バー", "4-2条件バー"),
    (2, "4-3 列の見方", "4-3列の見方"),
    (1, "出荷管理", "5出荷管理"),
    (2, "5-1 集計", "5-1集計"),
    (2, "5-2 当月出荷予定", "5-2当月出荷予定"),
    (2, "5-3 当月実出荷", "5-3当月実出荷"),
    (1, "量産品から振替", "6量産品から振替"),
    (2, "6-1 振替で行うこと", "6-1振替で行うこと"),
    (1, "手動登録", "7手動登録"),
    (1, "補給品詳細（編集・入出庫）", "8補給品詳細"),
    (2, "8-1 開き方", "8-1開き方"),
    (2, "8-2 保管・品質", "8-2保管・品質"),
    (2, "8-3 入出庫", "8-3入出庫"),
    (2, "8-4 その他のブロック", "8-4その他のブロック"),
    (1, "保管場所管理", "9保管場所管理"),
    (2, "9-1 追加・編集", "9-1追加・編集"),
    (2, "9-2 入れ替え", "9-2入れ替え"),
    (2, "9-3 一覧の操作", "9-3一覧の操作"),
    (1, "削除", "10削除"),
    (1, "Excel・棚卸表・棚番票", "11Excel・棚卸表・棚番票"),
    (1, "操作権限", "12操作権限"),
    (1, "メッセージと対処", "13メッセージと対処"),
    (1, "運用上の注意・よくある質問", "14運用上の注意・よくある質問"),
    (1, "文書情報", "文書情報"),
    (1, "改訂履歴", "改訂履歴"),
]


def find_page(doc: pymupdf.Document, needle: str, start: int = 0) -> int | None:
    needle_n = needle.replace(" ", "").replace("\u3000", "").replace("\n", "")
    for i in range(start, doc.page_count):
        text = (
            doc[i]
            .get_text("text")
            .replace(" ", "")
            .replace("\u3000", "")
            .replace("\n", "")
        )
        if needle_n in text:
            return i
    return None


def main() -> None:
    doc = pymupdf.open(PDF)
    toc_page = find_page(doc, "目次")
    body_start = (toc_page + 1) if toc_page is not None else 0
    toc: list[list] = [
        [1, "補給品管理 操作説明書", 1],
        [1, "目次", (toc_page + 1) if toc_page is not None else 2],
    ]
    for level, title, needle in BOOKMARKS:
        page = find_page(doc, needle, start=body_start)
        if page is None:
            print(f"WARN not found: {title!r}")
            continue
        toc.append([level, title, page + 1])
        print(f"L{level} p{page + 1} {title}")
    doc.set_toc(toc)
    doc.saveIncr()
    doc.close()
    verify = pymupdf.open(PDF)
    print("count", len(verify.get_toc()), "pages", verify.page_count)
    for e in verify.get_toc()[:8]:
        print(e)
    verify.close()


if __name__ == "__main__":
    main()
