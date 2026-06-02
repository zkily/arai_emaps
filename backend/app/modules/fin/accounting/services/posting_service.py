"""会計コア: 仕訳転記・試算表。

汎用 CRUD では表現しきれない会計固有ロジック（借貸バランス検証、転記、集計）を担う。
fin_codegen の再生成対象外（手書き）。
"""
from __future__ import annotations

from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.fin.accounting import models as acc


async def post_journal(db: AsyncSession, entry_id: int, *, posted_by: str | None = None) -> acc.JournalEntry:
    """仕訳を転記（draft -> posted）。借方合計と貸方合計の一致を検証する。"""
    entry = await db.get(acc.JournalEntry, entry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="仕訳が見つかりません")
    if entry.status == "posted":
        raise HTTPException(status_code=400, detail="既に転記済みです")

    lines = (await db.execute(
        select(acc.JournalLine).where(acc.JournalLine.entry_id == entry_id)
    )).scalars().all()
    debit = sum((Decimal(str(line.debit or 0)) for line in lines), Decimal("0"))
    credit = sum((Decimal(str(line.credit or 0)) for line in lines), Decimal("0"))
    if debit != credit:
        raise HTTPException(
            status_code=400,
            detail=f"借方({debit})と貸方({credit})が一致しません",
        )

    entry.total_debit = debit
    entry.total_credit = credit
    entry.status = "posted"
    if posted_by:
        entry.updated_by = posted_by
    await db.commit()
    await db.refresh(entry)
    return entry


async def trial_balance(db: AsyncSession, *, period_ym: str | None = None) -> list[dict]:
    """試算表（科目別の借方・貸方合計と残高）。posted の仕訳のみ集計する。"""
    stmt = (
        select(
            acc.JournalLine.account_code,
            acc.JournalLine.account_name,
            func.coalesce(func.sum(acc.JournalLine.debit), 0).label("debit"),
            func.coalesce(func.sum(acc.JournalLine.credit), 0).label("credit"),
        )
        .join(acc.JournalEntry, acc.JournalEntry.id == acc.JournalLine.entry_id)
        .where(acc.JournalEntry.status == "posted")
        .group_by(acc.JournalLine.account_code, acc.JournalLine.account_name)
        .order_by(acc.JournalLine.account_code)
    )
    if period_ym:
        stmt = stmt.where(acc.JournalEntry.period_ym == period_ym)

    rows = (await db.execute(stmt)).all()
    result = []
    for code, name, debit, credit in rows:
        d = Decimal(str(debit or 0))
        c = Decimal(str(credit or 0))
        result.append({
            "account_code": code,
            "account_name": name,
            "debit": float(d),
            "credit": float(c),
            "balance": float(d - c),
        })
    return result
