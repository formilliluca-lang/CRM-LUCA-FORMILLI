import streamlit as st
import pandas as pd
from datetime import datetime

# Configurazione Pagina
st.set_page_config(page_title="CRM Sinistri Condominiali", layout="wide", page_icon="🏢")

# Inizializzazione Stato Sessione
if "sinistri" not in st.session_state:
    st.session_state.sinistri = [
        {
            "id": "SIN-2026-001",
            "condominio": "Via Conca d'Oro 289",
            "amministratore": "Studio Rossi",
            "danno": "Infiltrazione acqua da colonna di scarico principale",
            "stato": "Da aprire",
            "data": "2026-10-28",
            "messaggi": [{"da": "Studio Rossi", "testo": "Segnalata perdita al 3° piano.", "ora": "10:15"}],
            "nuovo_msg": True
        },
        {
            "id": "SIN-2026-002",
            "condominio": "Via Properzio 4",
            "amministratore": "Studio Bianchi",
            "danno": "Rottura cristallo portone d'ingresso",
            "stato": "In lavorazione",
            "data": "2026-10-25",
            "messaggi": [{"da": "Broker", "testo": "Perito incaricato per il sopralluogo.", "ora": "15:30"}],
            "nuovo_msg": False
        },
        {
            "id": "SIN-2026-003",
            "condominio": "Via Nomentana 120",
            "amministratore": "Studio Rossi",
            "danno": "Distacco intonaco cornicione balcone",
            "stato": "Liquidata",
            "data": "2026-10-10",
            "messaggi": [{"da": "Broker", "testo": "Atto di liquidazione inviato al condominio.", "ora": "09:00"}],
            "nuovo_msg": False
        }
    ]

# Sidebar per cambio ruolo / login
st.sidebar.title("🔐 Accesso CRM")
ruolo = st.sidebar.radio("Seleziona Ruolo Utente:", ["Broker (Admin)", "Amministratore (Studio Rossi)"])

st.title("🏢 Gestione Sinistri Condominiali")

# Calcolo KPI
da_aprire = sum(1 for s in st.session_state.sinistri if s["stato"] == "Da aprire")
in_lavorazione = sum(1 for s in st.session_state.sinistri if s["stato"] == "In lavorazione")
liquidate = sum(1 for s in st.session_state.sinistri if s["stato"] == "Liquidata")

# Metric Cards
col1, col2, col3 = st.columns(3)
col1.metric("🔴 DA APRIRE", da_aprire)
col2.metric("🟠 IN LAVORAZIONE", in_lavorazione)
col3.metric("🟢 LIQUIDATE", liquidate)

st.divider()

# Tabelle o schede pratiche
st.subheader("📋 Lista Pratiche Sinistri")

for i, s in enumerate(st.session_state.sinistri):
    # Filtro visibilità per Amministratore
    if ruolo == "Amministratore (Studio Rossi)" and s["amministratore"] != "Studio Rossi":
        continue

    # Colore badge
    badge = "🔴" if s["stato"] == "Da aprire" else ("🟠" if s["stato"] == "In lavorazione" else "🟢")
    
    with st.expander(f"{badge} **{s['id']}** | {s['condominio']} — Status: **{s['stato'].upper()}**"):
        col_info, col_chat = st.columns([1, 1])
        
        with col_info:
            st.write(f"**Amministratore:** {s['amministratore']}")
            st.write(f"**Data Segnalazione:** {s['data']}")
            st.write(f"**Descrizione Danno:** {s['danno']}")
            
            # Cambio Stato (solo per Broker)
            if ruolo == "Broker (Admin)":
                nuovo_stato = st.selectbox("Modifica Stato Pratica:", ["Da aprire", "In lavorazione", "Liquidata"], 
                                           index=["Da aprire", "In lavorazione", "Liquidata"].index(s["stato"]),
                                           key=f"status_{i}")
                if nuovo_stato != s["stato"]:
                    st.session_state.sinistri[i]["stato"] = nuovo_stato
                    st.rerun()

        with col_chat:
            st.write("💬 **Messaggi & Aggiornamenti**")
            for msg in s["messaggi"]:
                st.caption(f"**{msg['da']}** ({msg['ora']}): {msg['testo']}")
            
            nuovo_testo = st.text_input("Scrivi un messaggio...", key=f"input_{i}")
            if st.button("Invia Messaggio", key=f"btn_{i}"):
                if nuovo_testo:
                    st.session_state.sinistri[i]["messaggi"].append({
                        "da": "Broker" if ruolo == "Broker (Admin)" else "Studio Rossi",
                        "testo": nuovo_testo,
                        "ora": datetime.now().strftime("%H:%M")
                    })
                    st.rerun()
