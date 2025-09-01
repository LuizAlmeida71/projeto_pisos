@echo off
set SCRIPT_DIR=%~dp0
cd /d %SCRIPT_DIR%

rem Definir o caminho completo para o executável do Python dentro do ambiente virtual
set PYTHON_EXE="C:\Users\lsaju\anaconda3\envs\pisos\python.exe"

rem Executar o Streamlit usando o Python do ambiente virtual
%PYTHON_EXE% -m streamlit run app.py

pause
