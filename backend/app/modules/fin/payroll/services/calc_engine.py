"""給与計算エンジン（スケルトン）。

支給控除項目（fin_pay_item / fin_employee_pay_item）と源泉税表
（fin_withholding_tax_table）をルール表として参照し、給与計算 run の各行を算出する。

注意: 日本の社会保険料率・源泉徴収税額は法令で頻繁に改定される。料率や税額は
必ず fin_withholding_tax_table 等のバージョン付きデータから取得し、本コードに
直接ハードコードしないこと。本関数は計算フレームのみを提供する手書きスケルトン。
fin_codegen の再生成対象外。
"""
from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.fin.payroll import models as pay


async def calculate_run(db: AsyncSession, run_id: int, *, calculated_by: str | None = None) -> dict:
    """指定 run の全行を計算し、ヘッダ合計を更新する。

    現状は固定支給控除（fin_employee_pay_item）の単純合算による骨組み。
    残業・社会保険・源泉税の本計算は、勤怠集計と料率テーブルを接続して拡張する。
    """
    run = await db.get(pay.PayrollRun, run_id)
    if run is None:
        return {"error": "run not found"}

    lines = (await db.execute(
        select(pay.PayrollRunLine).where(pay.PayrollRunLine.run_id == run_id)
    )).scalars().all()

    total_gross = Decimal("0")
    total_deduction = Decimal("0")
    for line in lines:
        items = (await db.execute(
            select(pay.EmployeePayItem).where(pay.EmployeePayItem.employee_id == line.employee_id)
        )).scalars().all()
        gross = Decimal("0")
        deduction = Decimal("0")
        for it in items:
            master = (await db.execute(
                select(pay.PayItem).where(pay.PayItem.code == it.pay_item_code)
            )).scalars().first()
            amount = Decimal(str(it.amount or 0))
            if master and master.item_type == "deduction":
                deduction += amount
            else:
                gross += amount
        line.gross_amount = gross
        line.deduction_amount = deduction
        line.net_amount = gross - deduction
        if calculated_by:
            line.updated_by = calculated_by
        total_gross += gross
        total_deduction += deduction

    run.total_gross = total_gross
    run.total_deduction = total_deduction
    run.total_net = total_gross - total_deduction
    run.status = "calculated"
    if calculated_by:
        run.updated_by = calculated_by
    await db.commit()
    return {
        "run_id": run_id,
        "total_gross": float(total_gross),
        "total_deduction": float(total_deduction),
        "total_net": float(total_gross - total_deduction),
        "lines": len(lines),
    }
