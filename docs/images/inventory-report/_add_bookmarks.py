"""inventory-report.pdf に目次ブックマーク（PDF Outline）を付与する。

使い方:
  py -3 docs/images/inventory-report/_add_bookmarks.py
"""
from __future__ import annotations

from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parents[3]
PDF = ROOT / "frontend" / "src" / "views" / "manual" / "pdfs" / "inventory-report.pdf"

BOOKMARKS: list[tuple[int, str, str]] = [
    (1, "はじめに", "1はじめに"),
    (2, "1-1 画面の目的", "1-1画面の目的"),
    (2, "1-2 用語", "1-2用語"),
    (1, "画面を開く", "2画面を開く"),
    (1, "画面構成", "3画面構成"),
    (2, "3-1 操作ボタン", "3-1操作ボタン"),
    (1, "期間の選び方", "4期間の選び方"),
    (1, "レポート生成", "5レポート生成"),
    (1, "KPIカードの見方", "6KPIカードの見方"),
    (1, "棚卸差異と大量廃棄", "7棚卸差異と大量廃棄"),
    (2, "7-1 理論在庫 vs 棚卸差異", "7-1理論在庫"),
    (2, "7-2 大量廃棄・保留品・大量不良", "7-2大量廃棄"),
    (1, "保存・読込・削除", "8保存・読込・削除"),
    (2, "8-1 下書き保存", "8-1下書き保存"),
    (2, "8-2 確定保存", "8-2確定保存"),
    (2, "8-3 読込と削除", "8-3読込と削除"),
    (1, "印刷・Excel・PDF・PPT", "9印刷・Excel・PDF・PPT"),
    (1, "用語・算出方法（ヘルプ）", "10用語・算出方法"),
    (1, "メッセージと対処", "11メッセージと対処"),
    (1, "運用上の注意・よくある質問", "12運用上の注意・よくある質問"),
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
        [1, "在庫報告管理 操作説明書", 1],
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
    verify.close()


if __name__ == "__main__":
    main()
