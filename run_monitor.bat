@echo off
if not exist "E:\wlpc-c1\logs" mkdir "E:\wlpc-c1\logs"
echo Step1 OK >> E:\wlpc-c1\logs\test.log
cd /d E:\wlpc-c1
echo Step2 CD=%CD% >> E:\wlpc-c1\logs\test.log
if exist "E:\wlpc-c1\src\main.py" (echo main.py exists >> E:\wlpc-c1\logs\test.log) else (echo main.py NOT FOUND >> E:\wlpc-c1\logs\test.log)
where python >> E:\wlpc-c1\logs\test.log 2>&1
echo Step3 DONE >> E:\wlpc-c1\logs\test.log
