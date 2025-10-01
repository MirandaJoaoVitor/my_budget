@echo off
cd /d %~dp0

:: Ativar o ambiente virtual
call venv\Scripts\activate.bat

:: Rodar o Streamlit
streamlit run src/app.py

:: Manter o prompt aberto em caso de erro
pause
