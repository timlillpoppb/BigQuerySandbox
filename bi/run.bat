@echo off
cd /d "%~dp0"
..\\.venv311\Scripts\streamlit run app.py --server.port 8501
