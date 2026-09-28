@echo off
setlocal EnableExtensions

title Horizon Portal - Logo Size Patch
color 0B

echo.
echo ==========================================
echo      HORIZON PORTAL - LOGO SIZE PATCH
echo ==========================================
echo.

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
    echo Dossier recherche :
    echo %ROOT%
    echo.
    pause
    exit /b 1
)

echo [OK] CSS trouve :
echo %CSS%
echo.

echo [1/3] Creation du backup...

copy /Y "%CSS%" "%CSS%.logo-backup" >nul

if errorlevel 1 (
    echo [ERREUR] Impossible de creer le backup.
    pause
    exit /b 1
)

echo [OK] Backup cree.
echo.

echo [2/3] Application du patch...

powershell -NoProfile -ExecutionPolicy Bypass -Command "$p=$env:CSS; $c=[IO.File]::ReadAllText($p); $css=@(); $css+=''; $css+='/* HORIZON PORTAL COMPACT LOGO */'; $css+='.topbar .brand { display:flex !important; align-items:center !important; gap:7px !important; height:30px !important; max-height:30px !important; font-size:13px !important; line-height:1 !important; }'; $css+='.topbar .brand-mark { width:22px !important; height:22px !important; min-width:22px !important; min-height:22px !important; max-width:22px !important; max-height:22px !important; padding:0 !important; margin:0 !important; font-size:10px !important; line-height:22px !important; overflow:hidden !important; flex:0 0 22px !important; }'; $css+='.topbar .brand-mark img, .topbar .brand-mark svg, .topbar .brand-mark picture, .topbar .brand img, .topbar .brand svg { width:22px !important; height:22px !important; max-width:22px !important; max-height:22px !important; object-fit:contain !important; display:block !important; }'; $css+='.topbar .brand-logo, .topbar .logo, .topbar .brand-icon { width:22px !important; height:22px !important; max-width:22px !important; max-height:22px !important; object-fit:contain !important; }'; $css+='.topbar { min-height:48px !important; height:48px !important; padding-top:6px !important; padding-bottom:6px !important; }'; $c += [Environment]::NewLine + ($css -join [Environment]::NewLine); [IO.File]::WriteAllText($p,$c,[Text.UTF8Encoding]::new($false))"

if errorlevel 1 (
    echo.
    echo [ERREUR] Le patch a echoue.
    echo Restauration du backup...
    copy /Y "%CSS%.logo-backup" "%CSS%" >nul
    echo [OK] CSS restaure.
    pause
    exit /b 1
)

echo [OK] Patch applique.
echo.

echo [3/3] Termine.
echo.
echo ==========================================
echo             PATCH TERMINE
echo ==========================================
echo.
echo Logo maximum : 22x22 px
echo Header       : 48 px
echo.
echo Backup :
echo %CSS%.logo-backup
echo.
echo Fais CTRL + F5 dans le navigateur.
echo.

pause