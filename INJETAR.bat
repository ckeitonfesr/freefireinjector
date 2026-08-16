@echo off
:: ═══════════════════════════════════════════════════════════════
::  FreeFire Injector — Script de execucao Windows
::  Clique duplo neste arquivo para rodar
:: ═══════════════════════════════════════════════════════════════
title FreeFire Injector - Filza IPA Modifier

echo.
echo  ============================================
echo   FreeFire Injector ^| Filza IPA Modifier
echo  ============================================
echo.

:: Tenta encontrar o Python real (nao o stub da Microsoft Store)
set "PYTHON="

:: 1. Tenta python3.exe na pasta local do usuario
if exist "%LOCALAPPDATA%\Python\bin\python3.exe" (
    set "PYTHON=%LOCALAPPDATA%\Python\bin\python3.exe"
    goto :found
)

:: 2. Tenta Python na pasta Programs
for /d %%G in ("%LOCALAPPDATA%\Programs\Python\Python*") do (
    if exist "%%G\python.exe" (
        set "PYTHON=%%G\python.exe"
        goto :found
    )
)

:: 3. Tenta py launcher
where py >nul 2>&1
if %errorlevel% == 0 (
    set "PYTHON=py"
    goto :found
)

:: 4. Tenta python3
where python3 >nul 2>&1
if %errorlevel% == 0 (
    set "PYTHON=python3"
    goto :found
)

echo [ERRO] Python nao encontrado!
echo.
echo  Instale o Python em: https://www.python.org/downloads/
echo  Marque "Add python.exe to PATH" na instalacao.
echo.
pause
exit /b 1

:found
echo  Python encontrado: %PYTHON%
echo.

:: Vai para a pasta do script
cd /d "%~dp0"

:: Checa se o argumento e --check
if "%1"=="--check" (
    echo  [Modo inspecao] Listando dylibs do binario...
    "%PYTHON%" tools\patch_binary.py --list Extracted\Payload\3105.app\3105
    echo.
    pause
    exit /b 0
)

:: Executa o script principal
"%PYTHON%" run_all.py

echo.
if %errorlevel% == 0 (
    echo  [SUCESSO] IPA modificado criado: Apps_Modified.ipa
) else (
    echo  [ERRO] Verifique as mensagens acima.
)

echo.
pause
