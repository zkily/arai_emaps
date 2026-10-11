"""forming-instruction-issue.pdf に目次ブックマーク（PDF Outline）を付与する。

使い方:
  py -3 docs/images/forming-instruction-issue/_add_bookmarks.py
"""
from __future__ import annotations

from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parents[3]
PDF = ROOT / "frontend" / "src" / "views" / "manual" / "pdfs" / "forming-instruction-issue.pdf"

BOOKMARKS: list[tuple[int, str, str]] = [
    (1, "はじめに", "1はじめに"),
    (2, "1-1 画面の目的", "1-1画面の目的"),
    (2, "1-2 用語", "1-2用語"),
    (2, "1-3 運用の流れ", "1-3運用の流れ"),
    (1, "画面を開く", "2画面を開く"),
    (1, "画面構成", "3画面構成"),
    (2, "3-1 操作ボタン", "3-1操作ボタン"),
    (1, "絞り込み・一覧の見方", "4絞り込み・一覧の見方"),
    (1, "指示書発行", "5指示書発行"),
    (2, "5-1 手順", "5-1手順"),
    (2, "5-2 指示書に含まれる主な情報", "5-2指示書に含まれる主な情報"),
    (1, "段取表プレビュー・印刷", "6段取表プレビュー・印刷"),
    (2, "6-1 段取予定プレビュー（ダイアログ）", "6-1段取予定プレビュー"),
    (1, "設備運行時間設定", "7設備運行時間設定"),
    (2, "7-1 手順", "7-1手順"),
    (1, "新聞紙設定", "8新聞紙設定"),
    (1, "メモ（TODO）", "9メモ（TODO）"),
    (1, "日別計画・実績チャート", "10日別計画・実績チャート"),
    (1, "操作権限（製造実行）", "11操作権限（製造実行）"),
    (1, "メッセージと対処", "12メッセージと対処"),
    (1, "運用上の注意・よくある質問", "13運用上の注意・よくある質問"),
    (2, "Q よくある質問", "よくある質問"),
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
        [1, "成型指示書発行管理 操作説明書", 1],
        [1, "目次", (toc_page + 1) if toc_page is not None else 2],
    ]

    for level, title, needle in BOOKMARKS:
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
    print("count", len(verify.get_toc()), "pages", verify.page_count)
    verify.close()


if __name__ == "__main__":
    main()
