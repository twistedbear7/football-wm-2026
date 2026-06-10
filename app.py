"""
WM 2026 – Der unsichtbare Gegner
Interaktive Streamlit-Visualisierung von Reisedistanzen, Quartieren & Reiselinien.

Start:  streamlit run app.py
Daten:  liest die CSVs aus data/ (vorher die Notebooks ausführen).
"""
from pathlib import Path

import pandas as pd
import pydeck as pdk
import streamlit as st

DATA = Path(__file__).parent / "data"

st.set_page_config(page_title="WM 2026 – Der unsichtbare Gegner", page_icon="⚽", layout="wide")


# ---------------------------------------------------------------- Daten laden
@st.cache_data
def _read_csv(path, _mtime):
    # _mtime ist Teil des Cache-Keys -> ändert sich die Datei, wird neu geladen
    df = pd.read_csv(path, encoding="utf-8-sig")
    return df.loc[:, ~df.columns.str.startswith("Unnamed")]  # leere Spalte (End-Komma) weg


def load_csv(name):
    p = DATA / name
    return _read_csv(str(p), p.stat().st_mtime)


try:
    df_dist = load_csv("wm2026_team_reiserouten_distanzen.csv")
    df_quartiere = load_csv("quartiere.csv")
    df_linien = load_csv("wm2026_reiselinien.csv")
except FileNotFoundError as e:
    st.error(f"CSV nicht gefunden: {e.filename}\n\nBitte zuerst das Notebook "
             "`notebooks/wm2026_team_reiserouten.ipynb` ausführen.")
    st.stop()

for df in (df_dist, df_quartiere, df_linien):
    df["Team"] = df["Team"] if "Team" in df.columns else df["Team_Name"]
    df["Team"] = df["Team"].astype(str).str.strip()


# ------------------------------------------------------------ Farbe pro Team
PALETTE = [
    [228, 26, 28], [55, 126, 184], [77, 175, 74], [152, 78, 163], [255, 127, 0],
    [255, 217, 47], [166, 86, 40], [247, 129, 191], [153, 153, 153], [26, 188, 156],
]
teams_all = sorted(df_dist["Team_Name"].unique())
team_color = {t: PALETTE[i % len(PALETTE)] for i, t in enumerate(teams_all)}


# ---------------------------------------------------------------- Sidebar
st.sidebar.title("⚽ WM 2026")
st.sidebar.caption("Reisedistanz & Zeitzonen als heimlicher Mitspieler")
alle = st.sidebar.checkbox("Alle Teams", value=True)
if alle:
    auswahl = teams_all
else:
    auswahl = st.sidebar.multiselect("Teams filtern", teams_all, default=teams_all)
    if not auswahl:
        st.sidebar.warning("Mindestens ein Team wählen.")
        st.stop()

d_dist = df_dist[df_dist["Team_Name"].isin(auswahl)]
d_quart = df_quartiere[df_quartiere["Team"].isin(auswahl)]
d_lin = df_linien[df_linien["Team"].isin(auswahl)].copy()


# ---------------------------------------------------------------- Kopf + KPIs
st.title("Der unsichtbare Gegner 🌍")
k1, k2, k3 = st.columns(3)
k1.metric("Teams", len(d_dist))
k2.metric("Ø Reisedistanz", f"{d_dist['Total_Distance_KM'].mean():,.0f} km".replace(",", "."))
top = d_dist.loc[d_dist["Total_Distance_KM"].idxmax()]
k3.metric("Vielreiser", top["Team_Name"], f"{top['Total_Distance_KM']:,.0f} km".replace(",", "."))

tab_karte, tab_hot, tab_rang, tab_eff = st.tabs(
    ["🗺️ Reiselinien", "📍 Quartiere & Hotspots", "📊 Ranking", "🎯 Effizienz"])


# ---------------------------------------------------------------- Tab: Reiselinien
with tab_karte:
    st.subheader("Reisewege vom Quartier zu den Spielorten")
    d_lin["from"] = d_lin[["Quartier_Lon", "Quartier_Lat"]].values.tolist()
    d_lin["to"] = d_lin[["Spielort_Lon", "Spielort_Lat"]].values.tolist()
    d_lin["color"] = d_lin["Team"].map(team_color)

    arc = pdk.Layer(
        "ArcLayer", d_lin,
        get_source_position="from", get_target_position="to",
        get_source_color="color", get_target_color="color",
        get_width=2, pickable=True, auto_highlight=True,
    )
    punkte = pdk.Layer(
        "ScatterplotLayer", d_lin,
        get_position="to", get_fill_color=[40, 40, 40], get_radius=25000, pickable=False,
    )
    st.pydeck_chart(pdk.Deck(
        layers=[arc, punkte],
        initial_view_state=pdk.ViewState(latitude=38, longitude=-100, zoom=2.6, pitch=35),
        tooltip={"text": "{Team}\n{BaseCamp_City} → {Spielort}\n{Distanz_KM} km ({Spiel_Datum})"},
        map_style=None,
    ))
    st.caption("Jeder Bogen = eine Hin-/Rückreise Quartier ↔ Spielort. Farbe = Team.")


# ---------------------------------------------------------------- Tab: Hotspots
with tab_hot:
    st.subheader("Wo sitzen die Teams? – Quartiere & Hot Spots")
    hot = (d_quart.groupby(["BaseCamp_City", "Latitude", "Longitude"])
           .agg(Anzahl=("Team", "size"), Teams=("Team", lambda s: ", ".join(sorted(s))))
           .reset_index())

    layer = pdk.Layer(
        "ScatterplotLayer", hot,
        get_position=["Longitude", "Latitude"],
        get_radius="Anzahl * 35000", get_fill_color=[255, 80, 80, 160],
        pickable=True, stroked=True, get_line_color=[120, 0, 0],
    )
    st.pydeck_chart(pdk.Deck(
        layers=[layer],
        initial_view_state=pdk.ViewState(latitude=38, longitude=-100, zoom=2.6),
        tooltip={"text": "{BaseCamp_City}\n{Anzahl} Team(s): {Teams}"},
        map_style=None,
    ))
    st.caption("Punktgröße = Anzahl Teams am selben Standort.")
    st.dataframe(hot[hot["Anzahl"] > 1].sort_values("Anzahl", ascending=False)
                 [["BaseCamp_City", "Anzahl", "Teams"]], hide_index=True, width="stretch")


# ---------------------------------------------------------------- Tab: Ranking
with tab_rang:
    st.subheader("Reisedistanz im Vergleich")
    rang = d_dist.sort_values("Total_Distance_KM", ascending=True)  # größter Balken oben bei horizontal
    st.bar_chart(rang.set_index("Team_Name")[["Total_Distance_KM", "Chain_Distance_KM"]],
                 horizontal=True, stack=False, height=max(400, len(rang) * 34))
    st.caption("Total_Distance_KM = Sternmodell (mit Quartier) · Chain_Distance_KM = naive Stadion-Kette.")
    st.dataframe(rang.sort_values("Total_Distance_KM", ascending=False),
                 hide_index=True, width="stretch")


# ---------------------------------------------------------------- Tab: Effizienz
with tab_eff:
    st.subheader("Glück vs. Planung – wie clever ist die Quartierwahl?")
    e1, e2 = st.columns(2)
    worst = d_dist.loc[d_dist["Vermeidbar_KM"].idxmax()]
    e1.metric("Meiste vermeidbare km", worst["Team_Name"],
              f"{worst['Vermeidbar_KM']:,.0f} km".replace(",", "."))
    e2.metric("Ø Effizienz", f"{d_dist['Effizienz_Prozent'].mean():.0f} %")

    eff = d_dist.sort_values("Total_Distance_KM", ascending=True)  # größter Balken oben
    st.bar_chart(eff.set_index("Team_Name")[["Optimal_KM", "Vermeidbar_KM"]],
                 horizontal=True, stack=True, height=max(400, len(eff) * 34),
                 color=["#4C9F70", "#E4572E"])
    st.caption("Pro Team gestapelt: **Optimal_KM** (grün, unvermeidbar – von der Auslosung diktiert) "
               "+ **Vermeidbar_KM** (rot, Planungs-Anteil durch die Quartierwahl). Summe = Gesamtdistanz.")

    tabelle = d_dist.sort_values("Vermeidbar_KM", ascending=False)[
        ["Team_Name", "BaseCamp_City", "Total_Distance_KM", "Optimal_KM",
         "Vermeidbar_KM", "Effizienz_Prozent", "Bestes_Quartier"]]
    st.dataframe(tabelle, hide_index=True, width="stretch")
