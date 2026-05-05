"""
Script de compression du fichier GeoJSON.
Lance automatiquement par mettre_a_jour_donnees.bat
"""

import gzip
import shutil
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent
source   = BASE_DIR / "data" / "solar_facettes_pv_clean.geojson"
dest     = BASE_DIR / "data" / "solar_facettes_pv_clean.geojson.gz"

if not source.exists():
    print(f"[ERREUR] Fichier introuvable : {source}")
    sys.exit(1)

print(f"Compression de {source.name} ...")

with source.open("rb") as f_in, gzip.open(dest, "wb") as f_out:
    shutil.copyfileobj(f_in, f_out)

taille_avant = source.stat().st_size / (1024 * 1024)
taille_apres = dest.stat().st_size   / (1024 * 1024)

print(f"Avant  : {taille_avant:.1f} MB")
print(f"Apres  : {taille_apres:.1f} MB")
print(f"Fichier cree : {dest.name}")
