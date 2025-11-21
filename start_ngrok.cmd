@echo off
cd /d "C:\Users\mmini\Documents\ladder"
cls
echo.
echo ========================================================================
echo                  NGROK - Tunel a Internet
echo ========================================================================
echo.
echo Conectando al puerto 5000...
echo.
echo CUANDO VEAS "Session Status: online":
echo.
echo 1. Busca la linea que dice "Forwarding"
echo 2. Copia la URL que empieza con "https://"
echo 3. Esa es tu URL publica!
echo.
echo ========================================================================
echo.
ngrok.exe http 5000

