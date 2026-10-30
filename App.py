import streamlit as st
import pandas as pd
from datetime import datetime

# Configurazione Pagina
st.set_page_config(page_title="CRM Sinistri Condominiali", layout="wide", page_icon="🏢")

# 1. Inizializzazione Liste Vuote (Partenza da Zero)
if "amministratori" not in st.session_state:
    st.session_state.amministratori = []

if "sinistri" not in st.session_state:
    st.session_state.sinistri = []

# Sidebar per Accesso e Filtri
st.sidebar.title("🔐 Accesso & Filtri")
ruolo = st.sidebar.radio("Seleziona Ruolo Utente:", ["Broker (Admin)", "Amministratore"])

admin_selezionato = None
if ruolo == "Amministratore":
    if len(st.session_state.amministratori) > 0:
        admin_selezionato = st.sidebar.selectbox("Seleziona il tuo Studio:", st.session_state.amministratori)
    else:
        st.sidebar.warning("Nessun amministratore presente. Registrane uno dal modulo pratiche.")

st.title("🏢 Gestione Sinistri Condominiali")

# Calcolo KPI
da_aprire = sum(1 for s in st.session_state.sinistri if s["stato"] == "Da aprire")
in_lavorazione = sum(1 for s in st.session_state.sinistri if s["stato"] == "In lavorazione")
liquidate = sum(1 for s in st.session_state.sinistri if s["stato"] == "Liquidata")

col1, col2, col3 = st.columns(3)
col1.metric("🔴 DA APRIRE", da_aprire)
col2.metric("🟠 IN LAVORAZIONE", in_lavorazione)
col3.metric("🟢 LIQUIDATE", liquidate)

st.divider()

# --- FORM DI INSERIMENTO NUOVA PRATICA ---
with st.expander("➕ **INSERISCI NUOVA SEGNALAZIONE / PRATICA**", expanded=True if len(st.session_state.sinistri) == 0 else False):
    st.subheader("Registra un nuovo sinistro o studio")
    
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        nuovo_condominio = st.text_input("Indirizzo Condominio *", placeholder="Es. Via Nomentana 120")
        
        # Gestione dinamica tendina
        opzioni_admin = st.session_state.amministratori + ["➕ Aggiungi Nuovo Studio / Amministratore..."]
        scelta_admin = st.selectbox("Amministratore di Riferimento *", opzioni_admin, index=len(opzioni_admin)-1 if len(st.session_state.amministratori) == 0 else 0)
        
        if scelta_admin == "➕ Aggiungi Nuovo Studio / Amministratore...":
            nuovo_admin_nome = st.text_input("Nome Nuovo Studio / Amministratore *", placeholder="Es. Studio Rossi")
        else:
            nuovo_admin_nome = scelta_admin

    with col_f2:
        nuova_polizza = st.text_input("Numero Polizza (opzionale)", placeholder="Es. POL-883920")
        data_evento = st.date_input("Data Evento / Segnalazione", datetime.now())
    
    descrizione_danno = st.text_area("Descrizione del Danno / Note Iniziali *", placeholder="Es. Rottura tubazione acqua calda bagno int. 4")
    
    if st.button("🚨 Salva e Invia Segnalazione (Stato: DA APRIRE)", use_container_width=True):
        admin_finale = nuovo_admin_nome.strip() if nuovo_admin_nome else ""
        
        if nuovo_condominio and descrizione_danno and admin_finale:
            # Aggiunge lo studio alla lista globale se non è presente
            if admin_finale not in st.session_state.amministratori:
                st.session_state.amministratori.append(admin_finale)
            
            nuovo_id = f"SIN-2026-{len(st.session_state.sinistri) + 1:03d}"
            nuova_pratica = {
                "id": nuovo_id,
                "condominio": nuovo_condominio,
                "amministratore": admin_finale,
                "polizza": nuova_polizza if nuova_polizza else "N/D",
                "danno": descrizione_danno,
                "stato": "Da aprire",
                "data": data_evento.strftime("%Y-%m-%d"),
                "messaggi": [{"da": ruolo, "testo": f"Pratica inserita: {descrizione_danno}", "ora": datetime.now().strftime("%H:%M")}]
            }
            st.session_state.sinistri.insert(0, nuova_pratica)
            st.success(f"Pratica {nuovo_id} creata con successo per {admin_finale}!")
            st.rerun()
        else:
            st.error("Compila i campi obbligatori: Indirizzo, Amministratore e Descrizione Danno.")

st.divider()

# --- LISTA PRATICHE ---
st.subheader("📋 Schede Pratiche Sinistri")

if len(st.session_state.sinistri) == 0:
    st.info("Nessuna pratica presente. Usa il modulo qui sopra per inserire la prima segnalazione.")
else:
    for i, s in enumerate(st.session_state.sinistri):
        # Filtro per Amministratore
        if ruolo == "Amministratore" and admin_selezionato and s["amministratore"] != admin_selezionato:
            continue

        badge = "🔴" if s["stato"] == "Da aprire" else ("🟠" if s["stato"] == "In lavorazione" else "🟢")
        
        with st.expander(f"{badge} **{s['id']}** | {s['condominio']} ({s['amministratore']}) — Status: **{s['stato'].upper()}**"):
            col_info, col_chat = st.columns([1, 1])
            
            with col_info:
                st.write(f"**Amministratore:** {s['amministratore']}")
                st.write(f"**Polizza N°:** {s['polizza']}")
                st.write(f"**Data Segnalazione:** {s['data']}")
                st.write(f"**Descrizione Danno:** {s['danno']}")
                
                if ruolo == "Broker (Admin)":
                    st.divider()
                    st.write("⚙️ **Gestione Broker**")
                    nuovo_stato = st.selectbox("Modifica Stato Pratica:", ["Da aprire", "In lavorazione", "Liquidata"], 
                                               index=["Da aprire", "In lavorazione", "Liquidata"].index(s["stato"]),
                                               key=f"status_{i}")
                    if nuovo_stato != s["stato"]:
                        st.session_state.sinistri[i]["stato"] = nuovo_stato
                        st.success(f"Stato aggiornato a: {nuovo_stato}")
                        st.rerun()
                    
                    if st.button("🗑️ Elimina Pratica", key=f"del_{i}"):
                        st.session_state.sinistri.pop(i)
                        st.rerun()

            with col_chat:
                st.write("💬 **Messaggi & Aggiornamenti**")
                for msg in s["messaggi"]:
                    st.caption(f"**{msg['da']}** ({msg['ora']}): {msg['testo']}")
                
                nuovo_testo = st.text_input("Scrivi un messaggio...", key=f"input_{i}")
                if st.button("Invia Messaggio", key=f"btn_{i}"):
                    if nuovo_testo:
                        st.session_state.sinistri[i]["messaggi"].append({
                            "da": "Broker" if ruolo == "Broker (Admin)" else (admin_selezionato if admin_selezionato else "Amministratore"),
                            "testo": nuovo_testo,
                            "ora": datetime.now().strftime("%H:%M")
                        })
                        st.rerun()
