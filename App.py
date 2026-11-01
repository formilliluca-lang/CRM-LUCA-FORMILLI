import streamlit as st
import pandas as pd
from datetime import datetime

# Configurazione Pagina
st.set_page_config(page_title="CRM Sinistri Condominiali", layout="wide", page_icon="🏢")

# 1. INIZIALIZZAZIONE STRUTTURA DATI (Memoria Sessione)
if "clienti" not in st.session_state:
    st.session_state.clienti = {}

if "sinistri" not in st.session_state:
    st.session_state.sinistri = []

# Gestione stato temporaneo per compilazione automatica da anagrafica
if "precompila_studio" not in st.session_state:
    st.session_state.precompila_studio = ""
if "precompila_condominio" not in st.session_state:
    st.session_state.precompila_condominio = ""
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "📋 Pratiche Sinistri"

# Funzione per estrarre tutti i condomini già salvati
def get_tutti_condomini():
    condomini_dict = {} # {nome_condominio: nome_studio}
    for studio, dati in st.session_state.clienti.items():
        for c in dati.get("condomini", []):
            condomini_dict[c] = studio
    return condomini_dict

# SIDEBAR PER ACCESSO E FILTRI
st.sidebar.title("🔐 Accesso & Ruolo")
ruolo = st.sidebar.radio("Seleziona Ruolo Utente:", ["Broker (Admin)", "Amministratore"])

admin_selezionato = None
lista_studi = sorted(list(st.session_state.clienti.keys()))

if ruolo == "Amministratore":
    if lista_studi:
        admin_selezionato = st.sidebar.selectbox("Seleziona il tuo Studio:", lista_studi)
    else:
        st.sidebar.warning("Nessuno studio cliente registrato.")

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

# SCHEDE DI NAVIGAZIONE
tab_pratiche, tab_clienti = st.tabs(["📋 Pratiche Sinistri", "👥 Aggiungi / Gestisci Cliente e Condomini"])

# ==========================================
# TAB 1: GESTIONE PRATICHE SINISTRI
# ==========================================
with tab_pratiche:
    with st.expander("➕ **APRI NUOVA PRATICA SINISTRO**", expanded=True if (len(st.session_state.sinistri) == 0 or st.session_state.precompila_condominio != "") else False):
        st.subheader("Registrazione Nuova Pratica")
        
        tutti_condomini = get_tutti_condomini()
        lista_condomini_esistenti = sorted(list(tutti_condomini.keys()))
        
        # Opzioni per il menu a tendina dei condomini
        opzioni_condomini = ["➕ Digita Nuovo Condominio..."] + lista_condomini_esistenti

        # Gestione valori precompilati se proveniamo dal tasto "Apri Pratica" dell'anagrafica
        index_cond_default = 0
        if st.session_state.precompila_condominio in lista_condomini_esistenti:
            index_cond_default = opzioni_condomini.index(st.session_state.precompila_condominio)

        scelta_cond_select = st.selectbox(
            "Seleziona Condominio Esistente (o sceglilo da elenco) *", 
            opzioni_condomini, 
            index=index_cond_default,
            key="select_cond_pratica"
        )

        # Determinazione automatica o manuale di Indirizzo e Studio
        if scelta_cond_select != "➕ Digita Nuovo Condominio...":
            condominio_final_input = scelta_cond_select
            studio_suggerito = tutti_condomini.get(scelta_cond_select, "")
        else:
            condominio_final_input = st.text_input("Digita Indirizzo Nuovo Condominio *", value=st.session_state.precompila_condominio, placeholder="Es. Via Conca d'Oro 289")
            studio_suggerito = st.session_state.precompila_studio

        with st.form("form_nuova_pratica", clear_on_submit=False):
            col_p1, col_p2 = st.columns(2)
            
            with col_p1:
                studio_pratica = st.text_input("Nome Studio / Amministratore *", value=studio_suggerito, placeholder="Es. Studio Rossi")
                condominio_pratica = st.text_input("Indirizzo Condominio Confermato *", value=condominio_final_input)

            with col_p2:
                numero_polizza = st.text_input("Numero Polizza (opzionale)", placeholder="Es. POL-992831")
                data_evento = st.date_input("Data Evento / Segnalazione", datetime.now())

            descrizione_danno = st.text_area("Descrizione del Danno / Note Iniziali *", placeholder="Es. Infiltrazione acqua da colonna di scarico principale")
            file_allegato_iniziale = st.file_uploader("Allegato iniziale (Foto, Perizia, Preventivo, PDF)", type=["pdf", "png", "jpg", "jpeg"])

            btn_salva_pratica = st.form_submit_button("🚨 Salva e Apri Pratica (Stato: DA APRIRE)", use_container_width=True)
            
            if btn_salva_pratica:
                studio_clean = studio_pratica.strip() if studio_pratica else ""
                cond_clean = condominio_pratica.strip() if condominio_pratica else ""

                if studio_clean and cond_clean and descrizione_danno:
                    # Registra lo studio e il condominio in anagrafica se non esistono ancora
                    if studio_clean not in st.session_state.clienti:
                        st.session_state.clienti[studio_clean] = {"telefono": "N/D", "email": "N/D", "condomini": [cond_clean]}
                    elif cond_clean not in st.session_state.clienti[studio_clean]["condomini"]:
                        st.session_state.clienti[studio_clean]["condomini"].append(cond_clean)

                    allegati_list = []
                    if file_allegato_iniziale is not None:
                        allegati_list.append(file_allegato_iniziale.name)

                    nuovo_id = f"SIN-2026-{len(st.session_state.sinistri) + 1:03d}"
                    nuova_pratica = {
                        "id": nuovo_id,
                        "condominio": cond_clean,
                        "amministratore": studio_clean,
                        "polizza": numero_polizza if numero_polizza else "N/D",
                        "danno": descrizione_danno,
                        "stato": "Da aprire",
                        "data": data_evento.strftime("%Y-%m-%d"),
                        "allegati": allegati_list,
                        "messaggi": [{"da": ruolo, "testo": f"Pratica creata: {descrizione_danno}", "ora": datetime.now().strftime("%H:%M")}]
                    }
                    st.session_state.sinistri.insert(0, nuova_pratica)
                    
                    # Reset precompilazione
                    st.session_state.precompila_studio = ""
                    st.session_state.precompila_condominio = ""
                    
                    st.success(f"Pratica {nuovo_id} aperta con successo per {cond_clean} ({studio_clean})!")
                    st.rerun()
                else:
                    st.error("Compila i campi obbligatori: Studio, Condominio e Descrizione Danno.")

    st.divider()
    
    # ELENCO PRATICHE
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

                    st.write("📎 **File e Allegati Pratica:**")
                    if "allegati" in s and s["allegati"]:
                        for f_name in s["allegati"]:
                            st.caption(f"📄 {f_name}")
                    else:
                        st.caption("Nessun allegato presente.")

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
                    st.write("💬 **Messaggi & Documenti**")
                    for msg in s["messaggi"]:
                        st.caption(f"**{msg['da']}** ({msg['ora']}): {msg['testo']}")
                    
                    nuovo_msg = st.text_input("Scrivi messaggio...", key=f"in_{i}")
                    nuovo_file_chat = st.file_uploader("Allega file al messaggio", type=["pdf", "png", "jpg", "jpeg"], key=f"file_chat_{i}")
                    
                    if st.button("Invia Messaggio / File", key=f"btn_{i}"):
                        if nuovo_msg or nuovo_file_chat is not None:
                            testo_completo = nuovo_msg if nuovo_msg else ""
                            if nuovo_file_chat is not None:
                                nome_f = nuovo_file_chat.name
                                if "allegati" not in s:
                                    st.session_state.sinistri[i]["allegati"] = []
                                st.session_state.sinistri[i]["allegati"].append(nome_f)
                                testo_completo += f" [File allegato: {nome_f}]"

                            st.session_state.sinistri[i]["messaggi"].append({
                                "da": "Broker" if ruolo == "Broker (Admin)" else (admin_selezionato if admin_selezionato else "Cliente"),
                                "testo": testo_completo.strip(),
                                "ora": datetime.now().strftime("%H:%M")
                            })
                            st.rerun()

# ==========================================
# TAB 2: AGGIUNGI / GESTISCI CLIENTE E CONDOMINI
# ==========================================
with tab_clienti:
    st.subheader("👤 Registra Nuovo Cliente / Amministratore")
    
    with st.form("form_nuovo_cliente_tab", clear_on_submit=True):
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            nome_cliente = st.text_input("Nome Studio / Amministratore *", placeholder="Es. Studio Tecnico Rossi")
            telefono_cliente = st.text_input("Telefono / Cellulare", placeholder="Es. 06 1234567")
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
                    st.success(f"Cliente '{nome_clean}' inserito con successo!")
                    st.rerun()
                else:
                    st.warning("Questo Studio/Cliente è già presente in anagrafica.")
            else:
                st.error("Inserisci il Nome dello Studio / Amministratore.")

    st.divider()

    # ELENCO E DETTAGLIO CLIENTI CON TASTO APERTURA PRATICA DIRETTA
    st.subheader("🏢 Anagrafica Clienti & Condomini")
    
    if not st.session_state.clienti:
        st.info("Nessun cliente in anagrafica.")
    else:
        for studio, dati in st.session_state.clienti.items():
            with st.expander(f"👤 **{studio}** | 📞 {dati['telefono']} | ✉️ {dati['email']}"):
                st.write(f"**Telefono:** {dati['telefono']} | **Email:** {dati['email']}")
                st.write("🏢 **Condomini Gestiti:**")

                if not dati["condomini"]:
                    st.caption("Nessun condominio ancora collegato a questo studio.")
                else:
                    for idx_c, cond in enumerate(dati["condomini"]):
                        col_cond1, col_cond2 = st.columns([3, 1])
                        with col_cond1:
                            st.markdown(f"📍 **{cond}**")
                        with col_cond2:
                            # Pulsante per aprire direttamente la pratica associata
                            if st.button(f"🚨 Apri Pratica", key=f"btn_apri_{studio}_{idx_c}"):
                                st.session_state.precompila_studio = studio
                                st.session_state.precompila_condominio = cond
                                st.success(f"Condominio '{cond}' selezionato! Vai alla scheda 'Pratiche Sinistri' per completare.")
                                st.rerun()

                st.divider()
                with st.form(f"form_add_cond_{studio}", clear_on_submit=True):
                    nuovo_cond_studio = st.text_input(f"Aggiungi un nuovo condominio a {studio}:", placeholder="Es. Via Properzio 4")
                    btn_add_cond = st.form_submit_button("➕ Aggiungi Condominio")
                    
                    if btn_add_cond and nuovo_cond_studio:
                        cond_add_clean = nuovo_cond_studio.strip()
                        if cond_add_clean not in st.session_state.clienti[studio]["condomini"]:
                            st.session_state.clienti[studio]["condomini"].append(cond_add_clean)
                            st.success(f"Condominio '{cond_add_clean}' aggiunto a {studio}!")
                            st.rerun()
