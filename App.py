import streamlit as st
import pandas as pd
from datetime import datetime

# Configurazione Pagina
st.set_page_config(page_title="CRM Sinistri Condominiali", layout="wide", page_icon="🏢")

# 1. INIZIALIZZAZIONE STRUTTURA DATI (Memoria Sessione)
if "clienti" not in st.session_state:
    # Struttura: {"Studio Rossi": {"telefono": "06...", "email": "info@...", "condomini": ["Via Conca d'Oro 289", "Via Properzio 4"]}}
    st.session_state.clienti = {}

if "sinistri" not in st.session_state:
    st.session_state.sinistri = []

# SIDEBAR PER ACCESSO E FILTRI
st.sidebar.title("🔐 Accesso & Ruolo")
ruolo = st.sidebar.radio("Seleziona Ruolo Utente:", ["Broker (Admin)", "Amministratore"])

admin_selezionato = None
lista_studi = list(st.session_state.clienti.keys())

if ruolo == "Amministratore":
    if lista_studi:
        admin_selezionato = st.sidebar.selectbox("Seleziona il tuo Studio:", lista_studi)
    else:
        st.sidebar.warning("Nessuno studio cliente registrato. Registralo dalla sezione Broker.")

st.title("🏢 CRM Sinistri & Anagrafica Condomini")

# KPI IN ALTO
da_aprire = sum(1 for s in st.session_state.sinistri if s["stato"] == "Da aprire")
in_lavorazione = sum(1 for s in st.session_state.sinistri if s["stato"] == "In lavorazione")
liquidate = sum(1 for s in st.session_state.sinistri if s["stato"] == "Liquidata")

col1, col2, col3 = st.columns(3)
col1.metric("🔴 DA APRIRE", da_aprire)
col2.metric("🟠 IN LAVORAZIONE", in_lavorazione)
col3.metric("🟢 LIQUIDATE", liquidate)

st.divider()

# TAB NAVIGATION PER SEPARARE LE FUNZIONI
tab_pratiche, tab_clienti = st.tabs(["📋 Pratiche Sinistri", "👥 Aggiungi / Gestisci Cliente e Condomini"])

# ==========================================
# TAB 1: GESTIONE PRATICHE SINISTRI
# ==========================================
with tab_pratiche:
    with st.expander("➕ **APRI NUOVA PRATICA SINISTRO**", expanded=True if len(st.session_state.sinistri) == 0 else False):
        st.subheader("Registrazione Pratica")
        
        col_p1, col_p2 = st.columns(2)
        
        with col_p1:
            # Selezione Studio Cliente
            if lista_studi:
                scelta_studio = st.selectbox("Seleziona Amministratore / Studio *", lista_studi)
                condomini_dello_studio = st.session_state.clienti[scelta_studio]["condomini"]
            else:
                st.info("Nessuno studio in anagrafica. Inseriscine uno qui sotto o nella scheda 'Aggiungi Cliente'.")
                scelta_studio = st.text_input("Nome Amministratore / Studio *", placeholder="Es. Studio Rossi")
                condomini_dello_studio = []

            # Selezione o Inserimento Condominio
            if condomini_dello_studio:
                opzioni_cond = condomini_dello_studio + ["➕ Altro / Nuovo Indirizzo..."]
                scelta_cond = st.selectbox("Seleziona Condominio *", opzioni_cond)
                if scelta_cond == "➕ Altro / Nuovo Indirizzo...":
                    indirizzo_condominio = st.text_input("Digita Indirizzo Condominio *", placeholder="Es. Via Nomentana 120")
                else:
                    indirizzo_condominio = scelta_cond
            else:
                indirizzo_condominio = st.text_input("Indirizzo Condominio *", placeholder="Es. Via Conca d'Oro 289")

        with col_p2:
            numero_polizza = st.text_input("Numero Polizza (opzionale)", placeholder="Es. POL-992831")
            data_evento = st.date_input("Data Evento / Segnalazione", datetime.now())

        descrizione_danno = st.text_area("Descrizione del Danno / Note Iniziali *", placeholder="Es. Infiltrazione acqua da colonna di scarico principale")
        
        if st.button("🚨 Salva Pratica (Stato: DA APRIRE)", use_container_width=True):
            studio_finale = scelta_studio.strip() if scelta_studio else ""
            cond_finale = indirizzo_condominio.strip() if indirizzo_condominio else ""

            if studio_finale and cond_finale and descrizione_danno:
                # Se lo studio non esiste in anagrafica lo aggiungiamo
                if studio_finale not in st.session_state.clienti:
                    st.session_state.clienti[studio_finale] = {"telefono": "N/D", "email": "N/D", "condomini": [cond_finale]}
                elif cond_finale not in st.session_state.clienti[studio_finale]["condomini"]:
                    st.session_state.clienti[studio_finale]["condomini"].append(cond_finale)

                nuovo_id = f"SIN-2026-{len(st.session_state.sinistri) + 1:03d}"
                nuova_pratica = {
                    "id": nuovo_id,
                    "condominio": cond_finale,
                    "amministratore": studio_finale,
                    "polizza": numero_polizza if numero_polizza else "N/D",
                    "danno": descrizione_danno,
                    "stato": "Da aprire",
                    "data": data_evento.strftime("%Y-%m-%d"),
                    "messaggi": [{"da": ruolo, "testo": f"Pratica inserita: {descrizione_danno}", "ora": datetime.now().strftime("%H:%M")}]
                }
                st.session_state.sinistri.insert(0, nuova_pratica)
                st.success(f"Pratica {nuovo_id} creata con successo per {cond_finale} ({studio_finale})!")
                st.rerun()
            else:
                st.error("Compila i campi obbligatori: Studio, Condominio e Descrizione Danno.")

    st.divider()
    
    # ELENCO PRATICI
    st.subheader("📋 Lista Pratiche")
    if not st.session_state.sinistri:
        st.info("Nessuna pratica presente.")
    else:
        for i, s in enumerate(st.session_state.sinistri):
            if ruolo == "Amministratore" and admin_selezionato and s["amministratore"] != admin_selezionato:
                continue

            badge = "🔴" if s["stato"] == "Da aprire" else ("🟠" if s["stato"] == "In lavorazione" else "🟢")
            with st.expander(f"{badge} **{s['id']}** | {s['condominio']} ({s['amministratore']}) — Status: **{s['stato'].upper()}**"):
                col_i1, col_i2 = st.columns(2)
                with col_i1:
                    st.write(f"**Amministratore:** {s['amministratore']}")
                    st.write(f"**Polizza N°:** {s['polizza']}")
                    st.write(f"**Data:** {s['data']}")
                    st.write(f"**Danno:** {s['danno']}")

                    if ruolo == "Broker (Admin)":
                        st.divider()
                        nuovo_st = st.selectbox("Modifica Stato:", ["Da aprire", "In lavorazione", "Liquidata"],
                                                index=["Da aprire", "In lavorazione", "Liquidata"].index(s["stato"]), key=f"st_{i}")
                        if nuovo_st != s["stato"]:
                            st.session_state.sinistri[i]["stato"] = nuovo_st
                            st.rerun()
                        if st.button("🗑️ Elimina Pratica", key=f"del_{i}"):
                            st.session_state.sinistri.pop(i)
                            st.rerun()

                with col_i2:
                    st.write("💬 **Messaggi & Note**")
                    for msg in s["messaggi"]:
                        st.caption(f"**{msg['da']}** ({msg['ora']}): {msg['testo']}")
                    nuovo_msg = st.text_input("Rispondi...", key=f"in_{i}")
                    if st.button("Invia", key=f"btn_{i}") and nuovo_msg:
                        st.session_state.sinistri[i]["messaggi"].append({
                            "da": "Broker" if ruolo == "Broker (Admin)" else (admin_selezionato if admin_selezionato else "Cliente"),
                            "testo": nuovo_msg,
                            "ora": datetime.now().strftime("%H:%M")
                        })
                        st.rerun()

# ==========================================
# TAB 2: AGGIUNGI / GESTISCI CLIENTE E CONDOMINI
# ==========================================
with tab_clienti:
    st.subheader("👤 Registra Nuovo Cliente / Amministratore")
    
    with st.form("form_nuovo_cliente", clear_on_submit=True):
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            nome_cliente = st.text_input("Nome Studio / Amministratore *", placeholder="Es. Studio Tecnico Rossi")
            telefono_cliente = st.text_input("Telefono / Cellulare", placeholder="Es. 06 1234567 / 339 1234567")
        with col_c2:
            email_cliente = st.text_input("Email / PEC", placeholder="Es. studio@rossiamministrazioni.it")
            primo_condominio = st.text_input("Primo Condominio da associare (opzionale)", placeholder="Es. Via Conca d'Oro 289")

        btn_salva_cli = st.form_submit_button("💾 Salva Scheda Cliente")

        if btn_salva_cli:
            if nome_cliente:
                nome_clean = nome_cliente.strip()
                if nome_clean not in st.session_state.clienti:
                    st.session_state.clienti[nome_clean] = {
                        "telefono": telefono_cliente if telefono_cliente else "N/D",
                        "email": email_cliente if email_cliente else "N/D",
                        "condomini": [primo_condominio.strip()] if primo_condominio else []
                    }
                    st.success(f"Cliente '{nome_clean}' aggiunto all'anagrafica!")
                    st.rerun()
                else:
                    st.warning("Questo Studio/Cliente è già presente in anagrafica.")
            else:
                st.error("Inserisci almeno il Nome dello Studio / Amministratore.")

    st.divider()

    # ELENCO E DETTAGLIO CLIENTI
    st.subheader("🏢 Anagrafica Clienti & Condomini Collegati")
    
    if not st.session_state.clienti:
        st.info("Nessun cliente in anagrafica. Compila il modulo in alto per registrarne uno.")
    else:
        for studio, dati in st.session_state.clienti.items():
            with st.expander(f"👤 **{studio}** | 📞 {dati['telefono']} | ✉️ {dati['email']}"):
                st.write(f"**Telefono:** {dati['telefono']} | **Email:** {dati['email']}")
                st.write("🏢 **Condomini Gestiti:**")

                if not dati["condomini"]:
                    st.caption("Nessun condominio ancora collegato a questo studio.")
                else:
                    for cond in dati["condomini"]:
                        st.markdown(f"- 📍 **{cond}**")

                st.divider()
                # Aggiunta rapida nuovo condominio per questo cliente
                col_add1, col_add2 = st.columns([3, 1])
                with col_add1:
                    nuovo_cond_studio = st.text_input("Aggiungi un nuovo condominio a questo studio:", key=f"add_cond_{studio}", placeholder="Es. Via Properzio 4")
                with col_add2:
                    st.write("") # Spaziatore
                    st.write("")
                    if st.button("➕ Aggiungi", key=f"btn_add_cond_{studio}") and nuovo_cond_studio:
                        if nuovo_cond_studio.strip() not in st.session_state.clienti[studio]["condomini"]:
                            st.session_state.clienti[studio]["condomini"].append(nuovo_cond_studio.strip())
                            st.success(f"Condominio aggiunto a {studio}!")
                            st.rerun()
