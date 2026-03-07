@echo off
chcp 65001 >nul
title Smart-EMAP 統合管理システム
echo Smart-EMAP システム起動中...
echo.

REM Pythonスクリプトを実行
python start.py

REM 終了コードを保存
set EXIT_CODE=%ERRORLEVEL%

REM エラーが発生した場合、または正常終了した場合でも一時停止
if %EXIT_CODE% NEQ 0 (
    echo.
    echo ========================================
    echo エラーが発生しました（終了コード: %EXIT_CODE%）
    echo ========================================
    echo.
    echo 詳細を確認してください。
    echo.
) else (
    echo.
    echo ========================================
    echo プログラムが正常に終了しました
    echo ========================================
    echo.
)

REM 常に一時停止してウィンドウを保持
pause

