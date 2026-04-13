@echo off
echo ========================================================
echo   JOB HUNTER AI - COMMAND CENTER
echo ========================================================
echo.
echo [1] Starting Streamlit Dashboard...
start cmd /k "python -m streamlit run dashboard/streamlit_app.py"

echo [2] Starting Job Application AI Agent...
echo The AI is now scanning for Jobs matching (Sri Lanka / Dubai / Singapore / UK / USA)
echo and Auto-Applying.
echo.
python -u -m app.fast_pipeline --mode auto_safe --top 50 --min-score 50

pause
