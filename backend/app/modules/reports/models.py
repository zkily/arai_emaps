"""レポート配信モデル（報告定義・スケジュール・送信履歴）"""
from sqlalchemy import BigInteger, Boolean, Column, DateTime, Integer, JSON, String, Text, Time
from sqlalchemy.sql import func

from app.core.database import Base


class ReportDefinition(Base):
    """レポート定義テーブルモデル"""
    __tablename__ = "report_definitions"

    id = Column(Integer, primary_key=True, index=True, comment="ID")
    report_code = Column(String(50), unique=True, nullable=False, index=True, comment="レポートコード")
    report_name = Column(String(100), nullable=False, comment="レポート名")
    category = Column(String(20), nullable=False, default="MES", comment="MES|ERP|APS")
    default_format = Column(String(10), nullable=False, default="xlsx", comment="xlsx|pdf|both")
    parameter_schema = Column(JSON, nullable=True, comment="パラメータスキーマ")
    event_code = Column(String(50), nullable=False, comment="紐づく通知イベントコード")
    description = Column(String(500), nullable=True, comment="説明")
    is_active = Column(Boolean, default=True, nullable=False, comment="有効フラグ")
    created_at = Column(DateTime, server_default=func.now(), comment="作成日時")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新日時")

    def __repr__(self):
        return f"<ReportDefinition(id={self.id}, code='{self.report_code}')>"


class ReportSchedule(Base):
    """レポートスケジュールテーブルモデル"""
    __tablename__ = "report_schedules"

    id = Column(Integer, primary_key=True, index=True, comment="ID")
    report_code = Column(String(50), nullable=False, index=True, comment="レポートコード")
    schedule_type = Column(String(20), nullable=False, default="daily", comment="daily|weekly|monthly")
    schedule_time = Column(Time, nullable=False, default="08:00:00", comment="実行時刻（JST）")
    schedule_config = Column(JSON, nullable=True, comment="曜日・実行日などの詳細")
    parameters = Column(JSON, nullable=True, comment="既定パラメータ")
    format = Column(String(10), nullable=True, comment="出力形式の上書き")
    is_active = Column(Boolean, default=True, nullable=False, comment="有効フラグ")
    last_run_at = Column(DateTime, nullable=True, comment="最終実行日時")
    next_run_at = Column(DateTime, nullable=True, comment="次回実行予定")
    created_by = Column(Integer, nullable=True, comment="作成者 users.id")
    created_at = Column(DateTime, server_default=func.now(), comment="作成日時")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新日時")

    def __repr__(self):
        return f"<ReportSchedule(id={self.id}, code='{self.report_code}', type='{self.schedule_type}')>"


class ReportSendLog(Base):
    """レポート送信履歴テーブルモデル"""
    __tablename__ = "report_send_logs"

    id = Column(BigInteger, primary_key=True, index=True, comment="ID")
    report_code = Column(String(50), nullable=False, index=True, comment="レポートコード")
    trigger_type = Column(String(20), nullable=False, default="manual", comment="manual|scheduled")
    reference_key = Column(String(150), nullable=False, index=True, comment="参照キー（重複送信防止）")
    parameters = Column(JSON, nullable=True, comment="実行パラメータのスナップショット")
    file_name = Column(String(255), nullable=True, comment="添付ファイル名")
    file_size = Column(Integer, nullable=True, comment="添付ファイルサイズ（byte）")
    recipient_count = Column(Integer, nullable=False, default=0, comment="送信対象件数")
    success_count = Column(Integer, nullable=False, default=0, comment="送信成功件数")
    status = Column(String(20), nullable=False, comment="success|partial|failed")
    message = Column(String(500), nullable=True, comment="結果メッセージ")
    error_message = Column(Text, nullable=True, comment="エラー内容")
    triggered_by = Column(Integer, nullable=True, comment="実行者 users.id（手動時）")
    created_at = Column(DateTime, server_default=func.now(), comment="作成日時")

    def __repr__(self):
        return f"<ReportSendLog(id={self.id}, code='{self.report_code}', status='{self.status}')>"
