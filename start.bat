@echo off
echo ========================================
echo    INICIANDO SISTEMA DE AGENDA WEB
echo ========================================
echo.
echo Iniciando servidor...
echo Acesse: http://127.0.0.1:5000
echo.
echo O servidor será fechado quando esta janela for fechada
echo ========================================

REM Abre o navegador após um delay
timeout /t 2 /nobreak >nul
start "" "http://127.0.0.1:5000"

REM Inicia o servidor (este comando manterá a janela aberta)
python flask_app.py

REM Quando o servidor for parado (Ctrl+C), a janela fechará automaticamente