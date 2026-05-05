@echo off
title Mise a jour des donnees PV Ixelles
color 1F
echo.
echo ============================================================
echo   OUTIL PV IXELLES - Mise a jour des donnees
echo   Commune d'Ixelles - Service Climat
echo ============================================================
echo.

:: ── Verification que le fichier geojson existe ──
if not exist "%~dp0data\solar_facettes_pv_clean.geojson" (
    echo.
    echo [ERREUR] Le fichier solar_facettes_pv_clean.geojson
    echo          est introuvable dans le dossier data\
    echo.
    echo Etapes a suivre :
    echo  1. Exporter la couche depuis QGIS au format GeoJSON
    echo  2. Nommer le fichier : solar_facettes_pv_clean.geojson
    echo  3. Le placer dans le dossier data\
    echo  4. Relancer ce script
    echo.
    pause
    exit /b 1
)

echo [1/2] Compression du fichier GeoJSON...
echo       (cela peut prendre quelques secondes)
echo.

:: ── Compression avec Python ──
python "%~dp0compresser_geojson.py"

if %errorlevel% neq 0 (
    echo.
    echo [ERREUR] La compression a echoue.
    echo          Verifiez que Python est installe et relancez.
    echo.
    pause
    exit /b 1
)

echo.
echo [2/2] Compression terminee avec succes !
echo.
echo ============================================================
echo   ETAPE SUIVANTE : Mettre a jour le fichier sur GitHub
echo ============================================================
echo.
echo  1. Ouvrir : https://github.com/chancel-15/outil-pv-ixelles
echo  2. Aller dans le dossier : data/
echo  3. Supprimer l'ancien fichier .geojson.gz
echo  4. Uploader le nouveau fichier depuis : %~dp0data\
echo  5. Attendre 2-3 minutes que l'application se mette a jour
echo.
echo  Application : https://outil-pv-ixelles.streamlit.app
echo.
echo ============================================================
echo.

:: ── Ouvrir automatiquement GitHub dans le navigateur ──
set /p OPEN="Voulez-vous ouvrir GitHub maintenant ? (O/N) : "
if /i "%OPEN%"=="O" (
    start https://github.com/chancel-15/outil-pv-ixelles/tree/main/data
)

echo.
echo Termine ! Appuyez sur une touche pour fermer.
pause > nul
