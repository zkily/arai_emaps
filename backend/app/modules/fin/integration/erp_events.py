"""ERP -> FIN 仕訳連携。

ERP（販売・購買・外注・在庫・原価）や給与・経費の業務イベントを fin_journal_source
として受け取り、月次でまとめて fin_journal_entry（仕訳）へ起票する。

このファイルは手書きの中核ロジックであり、fin_codegen の再生成対象外。
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.fin.accounting import models as acc
from app.modules.fin.master import models as mst

# event_type -> (借方科目名, 貸方科目名)。科目名は fin_account.name を参照して code 解決する。
JOURNAL_TEMPLATES: dict[str, tuple[str, str]] = {
    "SALES_POSTED": ("売掛金", "売上高"),
    "INVOICE_ISSUED": ("売掛金", "売上高"),
    "PURCHASE_RECEIVED": ("仕入高", "買掛金"),
    "OUTSOURCING_RECEIVED": ("外注加工費", "買掛金"),
    "INVENTORY_ADJUST": ("棚卸資産", "棚卸差額"),
    "COSTING_CLOSE": ("製品", "仕掛品"),
    "DEPRECIATION": ("減価償却費", "減価償却累計額"),
    "PAYROLL_POSTED": ("給与手当", "未払費用"),
    "EXPENSE_APPROVED": ("旅費交通費", "未払金"),
}


async def record_event(
    db: AsyncSession,
    *,
    source_type: str,
    source_ref: str,
    amount: Decimal | float,
    event_date: Optional[date] = None,
    source_module: str = "erp",
    payload_json: Optional[str] = None,
    created_by: Optional[str] = None,
) -> acc.JournalSource:
    """業務イベントを仕訳ソース（status=pending）として記録する。"""
    src = acc.JournalSource(
        source_type=source_type,
        source_module=source_module,
        source_ref=source_ref,
        event_date=event_date,
        amount=amount,
        payload_json=payload_json,
        status="pending",
        created_by=created_by,
        updated_by=created_by,
    )
    db.add(src)
    await db.commit()
    await db.refresh(src)
    return src


async def _resolve_account(db: AsyncSession, name: str) -> tuple[Optional[str], str]:
    """科目名から (code, name) を解決。未登録なら code=None。"""
    row = (await db.execute(select(mst.Account).where(mst.Account.name == name))).scalars().first()
    return (row.code if row else None), name


async def generate_journals(
    db: AsyncSession, *, period_ym: str, created_by: Optional[str] = None
) -> dict:
    """指定年月の pending ソースを仕訳（下書き）へ一括変換する。

    返り値: {generated: 件数, skipped: 件数}
    """
    q = select(acc.JournalSource).where(acc.JournalSource.status == "pending")
    sources = (await db.execute(q)).scalars().all()
    generated = 0
    skipped = 0
    for src in sources:
        ev_ym = src.event_date.strftime("%Y-%m") if src.event_date else period_ym
        if ev_ym != period_ym:
            continue
        template = JOURNAL_TEMPLATES.get(src.source_type)
        if not template:
            skipped += 1
            continue
        debit_name, credit_name = template
        d_code, d_name = await _resolve_account(db, debit_name)
        c_code, c_name = await _resolve_account(db, credit_name)
        amount = Decimal(str(src.amount or 0))

        entry = acc.JournalEntry(
            entry_date=src.event_date or date.today(),
            period_ym=period_ym,
            entry_type=src.source_module or "manual",
            description=f"{src.source_type} {src.source_ref or ''}".strip(),
            total_debit=amount,
            total_credit=amount,
            status="draft",
            source_id=src.id,
            created_by=created_by,
            updated_by=created_by,
        )
        db.add(entry)
        await db.flush()
        db.add(acc.JournalLine(
            entry_id=entry.id, line_no=1, account_code=d_code, account_name=d_name,
            debit=amount, credit=Decimal("0"), created_by=created_by, updated_by=created_by,
        ))
        db.add(acc.JournalLine(
            entry_id=entry.id, line_no=2, account_code=c_code, account_name=c_name,
            debit=Decimal("0"), credit=amount, created_by=created_by, updated_by=created_by,
        ))
        src.status = "generated"
        src.journal_entry_id = entry.id
        generated += 1

    await db.commit()
    return {"generated": generated, "skipped": skipped}
