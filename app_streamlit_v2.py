import geopandas as gpd
import pandas as pd
import streamlit as st
import folium
from pathlib import Path
from streamlit_folium import st_folium


# =========================================================
# CHEMINS DU PROJET
# =========================================================
# Fonctionne aussi bien en local que sur Streamlit Cloud
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"


# =========================================================
# 1. CONFIGURATION GENERALE
# =========================================================
st.set_page_config(
    page_title="Outil PV Ixelles",
    layout="wide"
)

st.title("Suivi et visualisation du potentiel photovoltaïque")
st.caption("Prototype de consultation des facettes solaires à Ixelles")

st.markdown(
    """
    Cet outil permet de consulter les facettes de toiture selon leur potentiel solaire,
    leur adresse, leur statut de rattachement et la présence ou non d'une installation
    photovoltaïque au niveau du bâtiment.
    """
)

# =========================================================
# 2. CHARGEMENT DES DONNEES
# =========================================================
@st.cache_data
def load_data():
    # Accepte aussi bien le .gz compressé que le .geojson brut
    file_gz   = DATA_DIR / "solar_facettes_pv_clean.geojson.gz"
    file_json = DATA_DIR / "solar_facettes_pv_clean.geojson"

    if file_gz.exists():
        gdf = gpd.read_file(file_gz)
    elif file_json.exists():
        gdf = gpd.read_file(file_json)
    else:
        st.error("Fichier de données introuvable. Vérifiez le dossier data/.")
        st.stop()

    gdf["geometry"] = gdf["geometry"].force_2d()
    return gdf

gdf = load_data()

# =========================================================
# 3. NETTOYAGE / PREPARATION
# =========================================================
text_cols = [
    "street_name",
    "street_number",
    "classe_irr",
    "pv_exist",
    "facet_status",
    "capakey",
]

for col in text_cols:
    if col in gdf.columns:
        gdf[col] = gdf[col].fillna("non renseigné").astype(str).str.strip()

if "construction_year" in gdf.columns:
    gdf["construction_year"] = (
        gdf["construction_year"]
        .fillna("non renseigné")
        .astype(str)
        .str.strip()
    )

if "inspire_id" in gdf.columns:
    gdf["inspire_id"] = gdf["inspire_id"].astype(str)

if "pv_exist" in gdf.columns:
    gdf["pv_exist"] = gdf["pv_exist"].replace(
        {
            "oui": "oui",
            "non": "non",
            "NULL": "non renseigné",
            "None": "non renseigné",
        }
    )

if "facet_status" in gdf.columns:
    gdf["facet_status"] = gdf["facet_status"].replace(
        {
            "batiment_pv": "bâtiment avec PV",
            "batiment_sans_pv": "bâtiment sans PV",
            "non_rattache": "non rattaché",
        }
    )

def build_address(row):
    street = row.get("street_name", "non renseigné")
    number = row.get("street_number", "non renseigné")
    if street == "non renseigné" and number == "non renseigné":
        return "adresse non renseignée"
    if number == "non renseigné":
        return f"{street}"
    return f"{street}, {number}"

gdf["adresse_complete"] = gdf.apply(build_address, axis=1)

# =========================================================
# 4. BARRE LATERALE - FILTRES
# =========================================================
st.sidebar.header("Filtres")

street_search = st.sidebar.text_input("Rechercher une rue", "")

streets = sorted(
    [x for x in gdf["street_name"].dropna().unique().tolist() if x != "non renseigné"]
)

if street_search.strip():
    streets_filtered = [s for s in streets if street_search.lower() in s.lower()]
else:
    streets_filtered = streets

street_choice = st.sidebar.selectbox("Rue", ["Toutes"] + streets_filtered)

if street_choice == "Toutes":
    gdf_street = gdf.copy()
else:
    gdf_street = gdf[gdf["street_name"] == street_choice].copy()

numbers = sorted(gdf_street["street_number"].dropna().astype(str).unique().tolist())
number_choice = st.sidebar.selectbox("Numéro", ["Tous"] + numbers)

classes = sorted(gdf["classe_irr"].dropna().astype(str).unique().tolist())
class_choice = st.sidebar.selectbox("Classe d'irradiance", ["Toutes"] + classes)

pv_choices = sorted(gdf["pv_exist"].dropna().astype(str).unique().tolist())
pv_choice = st.sidebar.selectbox("PV existant", ["Tous"] + pv_choices)

status_choices = sorted(gdf["facet_status"].dropna().astype(str).unique().tolist())
status_choice = st.sidebar.selectbox("Statut facette", ["Tous"] + status_choices)

years = sorted(
    [y for y in gdf["construction_year"].unique().tolist() if y != "non renseigné"]
)
year_choice = st.sidebar.selectbox("Année de construction", ["Toutes"] + years)

# =========================================================
# 5. APPLICATION DES FILTRES
# =========================================================
gdf_filtre = gdf.copy()

if street_choice != "Toutes":
    gdf_filtre = gdf_filtre[gdf_filtre["street_name"] == street_choice]

if number_choice != "Tous":
    gdf_filtre = gdf_filtre[gdf_filtre["street_number"].astype(str) == str(number_choice)]

if class_choice != "Toutes":
    gdf_filtre = gdf_filtre[gdf_filtre["classe_irr"] == class_choice]

if pv_choice != "Tous":
    gdf_filtre = gdf_filtre[gdf_filtre["pv_exist"] == pv_choice]

if status_choice != "Tous":
    gdf_filtre = gdf_filtre[gdf_filtre["facet_status"] == status_choice]

if year_choice != "Toutes":
    gdf_filtre = gdf_filtre[gdf_filtre["construction_year"] == year_choice]

# =========================================================
# 6. INDICATEURS PRINCIPAUX
# =========================================================
c1, c2, c3, c4 = st.columns(4)

nb_facettes = len(gdf_filtre)
nb_batiments = gdf_filtre["inspire_id"].nunique() if "inspire_id" in gdf_filtre.columns else 0
surface_totale = gdf_filtre["roof_area"].fillna(0).sum() if "roof_area" in gdf_filtre.columns else 0

if "pv_exist" in gdf_filtre.columns:
    nb_facettes_pv = (gdf_filtre["pv_exist"] == "oui").sum()
else:
    nb_facettes_pv = 0

c1.metric("Nombre de facettes", nb_facettes)
c2.metric("Nombre de bâtiments", nb_batiments)
c3.metric("Surface totale des facettes filtrées (m²)", f"{surface_totale:,.1f}")
c4.metric("Facettes avec bâtiment équipé PV", nb_facettes_pv)

# =========================================================
# 7. STATISTIQUES COMPLEMENTAIRES
# =========================================================
st.subheader("Résumé des classes d'irradiance")

if len(gdf_filtre) > 0:
    count_col = "fid" if "fid" in gdf_filtre.columns else gdf_filtre.columns[0]
    stats_classes = (
        gdf_filtre.groupby("classe_irr", dropna=False)
        .agg(
            nb_facettes=(count_col, "count"),
            surface_totale_m2=("roof_area", "sum")
        )
        .reset_index()
        .sort_values("classe_irr")
    )
    st.dataframe(stats_classes, use_container_width=True)
else:
    st.info("Aucune donnée à résumer pour les filtres choisis.")

# =========================================================
# 8. LEGENDE
# =========================================================
st.markdown("### Légende")
legend_cols = st.columns(4)
legend_cols[0].markdown("🟥 **fort**")
legend_cols[1].markdown("🟧 **moyen**")
legend_cols[2].markdown("🟨 **faible**")
legend_cols[3].markdown("⬜ **nul**")

# =========================================================
# 9. COULEURS
# =========================================================
def color_irr(classe):
    if classe == "nul":
        return "gray"
    elif classe == "faible":
        return "yellow"
    elif classe == "moyen":
        return "orange"
    elif classe == "fort":
        return "red"
    else:
        return "black"

# =========================================================
# 10. CARTE
# =========================================================
st.subheader("Carte des facettes filtrées")

if len(gdf_filtre) == 0:
    st.warning("Aucune facette ne correspond aux filtres choisis.")

else:
    # On limite l'affichage global pour éviter les lenteurs
    max_display = 1000

    if street_choice == "Toutes" and number_choice == "Tous":
        st.info(
            f"Vue globale : affichage limité à {max_display} facettes. "
            "Utilise les filtres pour zoomer sur une zone précise."
        )

    bounds = gdf_filtre.total_bounds
    xmin, ymin, xmax, ymax = bounds

    m = folium.Map()
    m.fit_bounds([[ymin, xmin], [ymax, xmax]])

    if len(gdf_filtre) > max_display:
        gdf_map = gdf_filtre.head(max_display).copy()
    else:
        gdf_map = gdf_filtre.copy()

    for _, row in gdf_map.iterrows():
        sim_geo = gpd.GeoSeries([row["geometry"]]).__geo_interface__

        popup_text = f"""
        <b>Adresse :</b> {row.get('adresse_complete', 'non renseigné')}<br>
        <b>Irradiance :</b> {row.get('irr_kwh_m2', 'non renseigné')} kWh/m²<br>
        <b>Classe :</b> {row.get('classe_irr', 'non renseigné')}<br>
        <b>Surface facette :</b> {row.get('roof_area', 'non renseigné')} m²<br>
        <b>PV existant :</b> {row.get('pv_exist', 'non renseigné')}<br>
        <b>Statut facette :</b> {row.get('facet_status', 'non renseigné')}<br>
        <b>Année construction :</b> {row.get('construction_year', 'non renseigné')}<br>
        <b>ID bâtiment :</b> {row.get('inspire_id', 'non renseigné')}<br>
        <b>CAPAKEY :</b> {row.get('capakey', 'non renseigné')}
        """

        folium.GeoJson(
            sim_geo,
            style_function=lambda x, classe=row["classe_irr"]: {
                "fillColor": color_irr(classe),
                "color": color_irr(classe),
                "weight": 0.6,
                "fillOpacity": 0.65,
            },
            popup=folium.Popup(popup_text, max_width=380),
        ).add_to(m)

    st_folium(m, width=1200, height=700)

# =========================================================
# 11. TABLEAU DETAILLE
# =========================================================
st.subheader("Tableau des résultats")

cols_to_show = [
    "adresse_complete",
    "irr_kwh_m2",
    "classe_irr",
    "pv_exist",
    "facet_status",
    "roof_area",
    "construction_year",
    "inspire_id",
    "capakey",
]

cols_to_show = [c for c in cols_to_show if c in gdf_filtre.columns]
st.dataframe(gdf_filtre[cols_to_show], use_container_width=True)

# =========================================================
# 12. TELECHARGEMENT CSV
# =========================================================
st.subheader("Téléchargement")

df_export = gdf_filtre[cols_to_show].copy()
csv = df_export.to_csv(index=False).encode("utf-8-sig")

st.download_button(
    label="Télécharger les résultats filtrés en CSV",
    data=csv,
    file_name="resultats_filtres_pv_ixelles.csv",
    mime="text/csv",
)
