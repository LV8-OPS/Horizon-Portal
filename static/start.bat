@echo off
setlocal EnableExtensions

title Horizon Portal - Header Patch
color 0B

echo.
echo ==========================================
echo      HORIZON PORTAL - HEADER PATCH
echo ==========================================
echo.

REM ============================================================
REM Recherche automatique de Index.css
REM ============================================================

set "ROOT=%~dp0"
set "CSS="

if exist "%ROOT%Index.css" (
    set "CSS=%ROOT%Index.css"
)

if not defined CSS if exist "%ROOT%backend\static\Index.css" (
    set "CSS=%ROOT%backend\static\Index.css"
)

if not defined CSS (
    echo [ERREUR] Index.css introuvable.
    echo.
    echo Dossier du patch :
    echo %ROOT%
    echo.
    echo Le fichier doit se trouver dans :
    echo backend\static\Index.css
    echo.
    pause
    exit /b 1
)

echo [OK] Index.css trouve :
echo %CSS%
echo.

REM ============================================================
REM Backup
REM ============================================================

echo [1/3] Creation de la sauvegarde...

copy /Y "%CSS%" "%CSS%.backup" >nul

if errorlevel 1 (
    echo.
    echo [ERREUR] Impossible de creer le backup.
    pause
    exit /b 1
)

echo [OK] Backup cree :
echo %CSS%.backup
echo.

REM ============================================================
REM Creation du script PowerShell temporaire
REM ============================================================

echo [2/3] Application du patch CSS...

set "PS=%TEMP%\horizon_header_patch.ps1"

> "%PS%" echo $p = '%CSS%'
>>"%PS%" echo $c = [IO.File]::ReadAllText($p)

>>"%PS%" echo $c = [regex]::Replace($c, '(?s)\.topbar\s*\{.*?\}', @'
>>"%PS%" echo .topbar {
>>"%PS%" echo   position: sticky;
>>"%PS%" echo   top: 0;
>>"%PS%" echo   z-index: 20;
>>"%PS%" echo   display: flex;
>>"%PS%" echo   align-items: center;
>>"%PS%" echo   justify-content: space-between;
>>"%PS%" echo   gap: 18px;
>>"%PS%" echo   padding: 9px clamp(18px, 3vw, 42px);
>>"%PS%" echo   min-height: 58px;
>>"%PS%" echo   background: rgba(7, 8, 11, .88);
>>"%PS%" echo   border-bottom: 1px solid var(--line);
>>"%PS%" echo   backdrop-filter: blur(18px);
>>"%PS%" echo }
>>"%PS%" echo '@, 1)

>>"%PS%" echo $c = [regex]::Replace($c, '(?s)\.brand\s*\{.*?\}', @'
>>"%PS%" echo .brand {
>>"%PS%" echo   display: flex;
>>"%PS%" echo   align-items: center;
>>"%PS%" echo   gap: 9px;
>>"%PS%" echo   font-weight: 750;
>>"%PS%" echo   font-size: 14px;
>>"%PS%" echo   letter-spacing: .02em;
>>"%PS%" echo }
>>"%PS%" echo '@, 1)

>>"%PS%" echo $c = [regex]::Replace($c, '(?s)\.brand-mark\s*\{.*?\}', @'
>>"%PS%" echo .brand-mark {
>>"%PS%" echo   width: 28px;
>>"%PS%" echo   height: 28px;
>>"%PS%" echo   display: grid;
>>"%PS%" echo   place-items: center;
>>"%PS%" echo   border: 1px solid rgba(212,175,55,.4);
>>"%PS%" echo   color: var(--gold-soft);
>>"%PS%" echo   background: linear-gradient(145deg,#17140b,#0c0d11);
>>"%PS%" echo   box-shadow: 0 0 18px rgba(212,175,55,.07);
>>"%PS%" echo   font-size: 12px;
>>"%PS%" echo }
>>"%PS%" echo '@, 1)

>>"%PS%" echo $c = [regex]::Replace($c, '(?s)\.shell\s*\{.*?\}', @'
>>"%PS%" echo .shell {
>>"%PS%" echo   width: min(1180px, calc(100% - 32px));
>>"%PS%" echo   margin: 0 auto;
>>"%PS%" echo   padding: 32px 0 70px;
>>"%PS%" echo }
>>"%PS%" echo '@, 1)

>>"%PS%" echo [IO.File]::WriteAllText($p, $c, [Text.UTF8Encoding]::new($false))

powershell -NoProfile -ExecutionPolicy Bypass -File "%PS%"

if errorlevel 1 (
    echo.
    echo [ERREUR] Le patch a echoue.
    echo.
    echo Restauration du backup...
    copy /Y "%CSS%.backup" "%CSS%" >nul
    del "%PS%" >nul 2>&1
    pause
    exit /b 1
)

del "%PS%" >nul 2>&1

echo [OK] CSS modifie.
echo.

REM ============================================================
REM Fin
REM ============================================================

echo [3/3] Patch termine.
echo.
echo ==========================================
echo             PATCH TERMINE
echo ==========================================
echo.
echo Header : 58px
echo Logo   : 28px
echo Contenu : largeur 1180px
echo.
echo Backup :
echo %CSS%.backup
echo.
echo Fais CTRL + F5 dans le navigateur.
echo.

pause