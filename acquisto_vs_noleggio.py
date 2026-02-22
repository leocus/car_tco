import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Configurazione Pagina
st.set_page_config(page_title="Car Cost Comparator", layout="wide", page_icon="🚗")

st.title("Comparatore Costi Auto")
st.markdown("""
Questa app ti aiuta a confrontare il **Costo Totale di Possesso (TCO)** tra:
1. Acquisto (Proprietà)
2. Noleggio a Lungo Termine
3. Noleggio a Breve Termine / Car Sharing
""")

# --- SIDEBAR: PARAMETRI GENERALI ---
st.sidebar.header("⚙️ Parametri Generali")
anni = st.sidebar.slider("Orizzonte temporale (anni)", 1, 10, 4)
km_anno = st.sidebar.number_input("Km percorsi all'anno", value=15000, step=1000)

st.sidebar.markdown("---")
st.sidebar.header("📉 Opzioni Avanzate")
calcolo_residuo = st.sidebar.radio("Calcolo Valore Residuo", ["Automatico (Algoritmo)", "Manuale"])

# Costo opportunità (Facoltativo)
usa_costo_opportunita = st.sidebar.checkbox("Includi Costo Opportunità", help="Considera il rendimento perso investendo i soldi nell'auto invece che in un prodotto finanziario (es. Conto Deposito).")
rendimento_annuo = 0.0
if usa_costo_opportunita:
    rendimento_annuo = st.sidebar.slider("Rendimento annuo netto stimato (%)", 0.0, 15.0, 2.5) / 100

# --- COLONNE INPUT ---
col1, col2, col3 = st.columns(3)

with col1:
    st.header("Proprietà")
    prezzo_auto = st.number_input("Prezzo listino auto (€)", value=35000, step=1000)
    
    if calcolo_residuo == "Manuale":
        valore_residuo = st.number_input("Valore residuo stimato (€)", value=15000)
    else:
        # Algoritmo svalutazione: -25% primo anno, poi -10% annuo + correzione KM
        # Media 15k km/anno. Se fai più km, perdi 1.5% ogni 5k km extra.
        base_svalutazione = [1.0, 0.75, 0.65, 0.55, 0.48, 0.40, 0.33, 0.28, 0.23, 0.18, 0.15]
        perc_residua = base_svalutazione[min(anni, 10)]
        km_extra = max(0, (km_anno - 15000) * anni)
        penale_km = (km_extra / 5000) * 0.015
        valore_residuo = prezzo_auto * (perc_residua - penale_km)
        st.caption(f"Valore residuo stimato: **{valore_residuo:,.0f}€** ({perc_residua*100:.1f}% del listino)")

    spese_fisse = st.number_input("Assicurazione + Bollo (€/anno)", value=1200)
    manutenzione_ord = st.number_input("Manutenzione ordinaria (€/anno)", value=400)
    rischio_imprevisti = st.number_input("Rischio imprevisti/extra (€/anno)", value=300, help="Accantonamento per riparazioni fuori garanzia.")

with col2:
    st.header("Noleggio a lungo termine")
    anticipo_nlt = st.number_input("Anticipo NLT (€)", value=5000, step=500)
    canone_nlt = st.number_input("Canone mensile (€)", value=480, step=10)
    st.info("Include tipicamente: RCA, Kasko, Bollo, Manutenzione e Soccorso stradale.")

with col3:
    st.header("Noleggio a breve termine")
    costo_giorno = st.number_input("Costo medio al giorno (€)", value=65)
    giorni_uso = st.number_input("Giorni di uso all'anno", value=80)
    st.caption("Ideale se non usi l'auto tutti i giorni.")

# --- LOGICA DI CALCOLO ---

# 1. Calcolo Proprietà
costo_acquisto_netto = prezzo_auto - valore_residuo
costi_gestione_tot = (spese_fisse + manutenzione_ord + rischio_imprevisti) * anni
# Semplificazione Costo Opportunità: applicato sull'intero capitale immobilizzato (prezzo auto)
opportunita_tot = 0
if usa_costo_opportunita:
    # Calcolo interessi composti persi sul prezzo dell'auto
    opportunita_tot = prezzo_auto * ((1 + rendimento_annuo)**anni - 1)

tco_proprieta = costo_acquisto_netto + costi_gestione_tot + opportunita_tot

# 2. Calcolo NLT
tco_nlt = anticipo_nlt + (canone_nlt * 12 * anni)

# 3. Calcolo NBT
tco_nbt = (costo_giorno * giorni_uso) * anni

# --- OUTPUT E VISUALIZZAZIONE ---
st.markdown("---")
st.subheader("📊 Confronto Risultati")

data = {
    "Vento di Spesa": ["Costo Totale", "Costo Annuo", "Costo Mensile"],
    "Proprietà": [tco_proprieta, tco_proprieta/anni, tco_proprieta/(anni*12)],
    "NLT": [tco_nlt, tco_nlt/anni, tco_nlt/(anni*12)],
    "Breve Termine": [tco_nbt, tco_nbt/anni, tco_nbt/(anni*12)]
}
df = pd.DataFrame(data)

c1, c2 = st.columns([1, 1.5])

with c1:
    st.dataframe(df.set_index("Vento di Spesa").style.format("{:,.0f} €"))
    
    # Messaggio dinamico
    vincitore = df.columns[df.iloc[0, 1:].astype(float).argmin() + 1]
    st.success(f"💡 L'opzione economicamente più vantaggiosa è: **{vincitore}**")

with c2:
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df.columns[1:], 
        y=df.iloc[0, 1:], 
        marker_color=['#1f77b4', '#ff7f0e', '#2ca02c'],
        text=[f"{v:,.0f}€" for v in df.iloc[0, 1:]],
        textposition='auto',
    ))
    
    fig.update_layout(
        title="Confronto Costo Totale (TCO)", 
        yaxis_title="Euro (€)", 
        height=400,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    st.plotly_chart(fig, use_container_width=True)

# Dettaglio Costi Proprietà
if usa_costo_opportunita or rischio_imprevisti > 0:
    with st.expander("🔍 Dettaglio Costi Proprietà"):
        st.write(f"- Svalutazione auto: {costo_acquisto_netto:,.0f}€")
        st.write(f"- Costi fissi (Bollo/Ass): {spese_fisse*anni:,.0f}€")
        st.write(f"- Manutenzione (Ord + Straord): {(manutenzione_ord + rischio_imprevisti)*anni:,.0f}€")
        if usa_costo_opportunita:
            st.write(f"- Costo opportunità finanziario: {opportunita_tot:,.0f}€")
