import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import uuid

st.set_page_config(
    page_title="CRM Sinistri & Clienti",
    page_icon="🏢",
    layout="wide"
)

conn = st.connection("gsheets", type=GSheetsConnection)

# Colonne esatte del tuo file CRM_sinistri_database
COLS_CLIENTI = ["nome", "telefono", "email", "condomini"]
COLS_SINISTRI = ["id", "condominio", "amministratore", "polizza", "danno", "stato", "data", "allegati", "messaggi"]

def leggi_dati(foglio: str, colonne: list) -> pd.DataFrame:
    try:
        df = conn.read(worksheet=foglio, ttl="0s")
        # Pulisce eventuali spazi extra nei nomi delle colonne (es. "condominio " -> "condominio")
        df.columns = [c.strip() for c in df.columns]
        if df.empty:
            return pd.DataFrame(columns=colonne)
        df = df.dropna(how="all")
        for col in colonne:
            if col not in df.columns:
                df[col] = ""
        return df[colonne]
    except Exception as e:
        st.error(f"Errore lettura foglio '{foglio}': {e}")
        return pd.DataFrame(columns=colonne)

def salva_dati(foglio: str, df: pd.DataFrame):
    try:
        conn.update(worksheet=foglio, data=df)
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Errore salvataggio su '{foglio}': {e}")
        st.stop()

# Caricamento dati permanenti dal tuo foglio Google
df_clienti = leggi_dati("clienti", COLS_CLIENTI)
df_sinistri = leggi_dati("sinistri", COLS_SINISTRI)

# --- SIDEBAR ---
st.sidebar.title("🏢 CRM Sinistri")
menu = st.sidebar.radio(
    "Menu",
    ["📂 Schede Clienti & Sinistri", "➕ Nuova Scheda Cliente / Studio", "📋 Tutti i Sinistri"]
)

# =========================================================
# 1. CREA NUOVA SCHEDA CLIENTE / AMMINISTRATORE
# =========================================================
if menu == "➕ Nuova Scheda Cliente / Studio":
    st.title("➕ Nuova Scheda Cliente / Amministratore")
    st.caption("I dati vengono salvati nella scheda 'clienti' di CRM_sinistri_database.")
    
    with st.form("form_nuovo_cliente", clear_on_submit=True):
        nome = st.text_input("Nome Amministratore / Studio *")
        telefono = st.text_input("Telefono")
        email = st.text_input("Email")
        condomini = st.text_area("Condomini Gestiti (separati da virgola, es. Via Po 12, Via Leutari 28)")
        
        if st.form_submit_button("💾 Salva Scheda Cliente"):
            if not nome.strip():
                st.error("Inserisci il nome del cliente/amministratore.")
            else:
                nuovo_cliente = pd.DataFrame([{
                    "nome": nome.strip(),
                    "telefono": telefono.strip(),
                    "email": email.strip(),
                    "condomini": condomini.strip()
                }])
                df_agg = pd.concat([df_clienti, nuovo_cliente], ignore_index=True)
                salva_dati("clienti", df_agg)
                st.success(f"Scheda '{nome}' salvata permanentemente su Google Sheets!")
                st.rerun()

# =========================================================
# 2. SCHEDE CLIENTI E SOTTO-SCHEDE SINISTRI
# =========================================================
elif menu == "📂 Schede Clienti & Sinistri":
    st.title("📂 Schede Clienti & Sotto-Schede Sinistri")
    
    if df_clienti.empty:
        st.info("Nessun cliente ancora in archivio. Vai su '➕ Nuova Scheda Cliente / Studio' per inserire il primo.")
        st.stop()

    lista_clienti = df_clienti["nome"].dropna().tolist()
    cliente_scelto = st.sidebar.selectbox("Seleziona Scheda Cliente:", lista_clienti)
    
    idx_cli = df_clienti[df_clienti["nome"] == cliente_scelto].index[0]
    dati_cli = df_clienti.loc[idx_cli]

    # Box Anagrafica Cliente (modificabile)
    with st.expander(f"👤 Scheda Anagrafica: {dati_cli['nome']}", expanded=True):
        with st.form("modifica_cliente"):
            c1, c2 = st.columns(2)
            tel_mod = c1.text_input("Telefono", value=str(dati_cli["telefono"]) if pd.notna(dati_cli["telefono"]) else "")
            email_mod = c2.text_input("Email", value=str(dati_cli["email"]) if pd.notna(dati_cli["email"]) else "")
            cond_mod = st.text_area("Elenco Condomini", value=str(dati_cli["condomini"]) if pd.notna(dati_cli["condomini"]) else "")
            
            if st.form_submit_button("💾 Aggiorna Dati Cliente"):
                df_clienti.at[idx_cli, "telefono"] = tel_mod
                df_clienti.at[idx_cli, "email"] = email_mod
                df_clienti.at[idx_cli, "condomini"] = cond_mod
                salva_dati("clienti", df_clienti)
                st.success("Dati cliente aggiornati su Google Sheets!")
                st.rerun()

    st.markdown("---")
    
    tab_sottoschede, tab_nuovo_sx = st.tabs([
        "📑 Sotto-Schede Sinistri del Cliente",
        "➕ Apri Nuovo Sinistro per questo Cliente"
    ])

    # TAB A: SOTTO-SCHEDE SINISTRI DEL CLIENTE
    with tab_sottoschede:
        sinistri_cli = df_sinistri[df_sinistri["amministratore"].astype(str).str.strip() == cliente_scelto.strip()]
        
        if sinistri_cli.empty:
            st.info(f"Nessun sinistro registrato per {cliente_scelto}.")
        else:
            st.dataframe(
                sinistri_cli[["id", "condominio", "polizza", "danno", "stato", "data"]],
                use_container_width=True,
                hide_index=True
            )
            
            st.subheader("🔍 Apri Dettaglio Sotto-Scheda")
            opzioni_sx = {
                f"{r['id']} - {r['condominio']} ({r['stato']})": r["id"]
                for _, r in sinistri_cli.iterrows()
            }
            sx_label = st.selectbox("Seleziona Sinistro:", list(opzioni_sx.keys()))
            id_sx = opzioni_sx[sx_label]
            
            idx_sx = df_sinistri[df_sinistri["id"] == id_sx].index[0]
            dati_sx = df_sinistri.loc[idx_sx]

            with st.container(border=True):
                st.markdown(f"#### Pratica: `{id_sx}` — Condominio: **{dati_sx['condominio']}**")
                
                col_a, col_b = st.columns(2)
                stati = ["Inviata", "Aperta", "In lavorazione", "Perizia fissata", "Liquidata", "Chiusa / Senza seguito"]
                stato_att = str(dati_sx["stato"]).strip() if pd.notna(dati_sx["stato"]) else "Aperta"
                idx_st = stati.index(stato_att) if stato_att in stati else 0
                
                nuovo_stato = col_a.selectbox("Stato Pratica", stati, index=idx_st)
                nuova_polizza = col_a.text_input("Numero Polizza", value=str(dati_sx["polizza"]) if pd.notna(dati_sx["polizza"]) else "")
                nuovo_danno = col_b.text_input("Tipologia / Descrizione Danno", value=str(dati_sx["danno"]) if pd.notna(dati_sx["danno"]) else "")
                nuovi_allegati = col_b.text_input("Link Cartella Drive / Allegati", value=str(dati_sx["allegati"]) if pd.notna(dati_sx["allegati"]) else "")
                
                if st.button("💾 Salva Modifiche Sotto-Scheda"):
                    df_sinistri.at[idx_sx, "stato"] = nuovo_stato
                    df_sinistri.at[idx_sx, "polizza"] = nuova_polizza
                    df_sinistri.at[idx_sx, "danno"] = nuovo_danno
                    df_sinistri.at[idx_sx, "allegati"] = nuovi_allegati
                    salva_dati("sinistri", df_sinistri)
                    st.success("Sotto-scheda sinistro aggiornata su Google Sheets!")
                    st.rerun()

                # Diario Messaggi / Note nella colonna 'messaggi'
                st.markdown("---")
                st.markdown("##### 💬 Diario Messaggi & Aggiornamenti")
                storico_msg = str(dati_sx["messaggi"]) if pd.notna(dati_sx["messaggi"]) and str(dati_sx["messaggi"]).strip() != "" else ""
                if storico_msg:
                    st.text_area("Cronologia salvata:", value=storico_msg, height=150, disabled=True)
                else:
                    st.caption("Nessun messaggio inserito per questa pratica.")
                
                with st.form(f"msg_{id_sx}", clear_on_submit=True):
                    nuovo_msg = st.text_input("Scrivi nuovo aggiornamento / nota:")
                    if st.form_submit_button("Aggiungi Messaggio"):
                        if nuovo_msg.strip():
                            timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")
                            riga_agg = f"[{timestamp}] {nuovo_msg.strip()}"
                            testo_finale = f"{storico_msg}\n{riga_agg}".strip()
                            df_sinistri.at[idx_sx, "messaggi"] = testo_finale
                            salva_dati("sinistri", df_sinistri)
                            st.rerun()

    # TAB B: NUOVO SINISTRO PER QUESTO CLIENTE
    with tab_nuovo_sx:
        st.subheader(f"Nuovo sinistro per {cliente_scelto}")
        
        # Suggerisce i condomini già inseriti nella scheda del cliente
        lista_cond_suggeriti = [c.strip() for c in str(dati_cli["condomini"]).split(",") if c.strip()]
        
        with st.form("form_nuovo_sinistro", clear_on_submit=True):
            c1, c2 = st.columns(2)
            id_nuovo = c1.text_input("Codice / Numero Sinistro *", value=f"SX-{datetime.now().strftime('%y%m%d-%H%M')}")
            if lista_cond_suggeriti:
                cond_scelto = c1.selectbox("Condominio (dall'anagrafica cliente)", lista_cond_suggeriti + ["Altro (scrivi sotto)"])
                cond_altro = c1.text_input("Oppure scrivi indirizzo condominio:")
            else:
                cond_scelto = ""
                cond_altro = c1.text_input("Condominio / Indirizzo *")
                
            polizza_nuova = c2.text_input("Numero Polizza")
            data_sx = c2.date_input("Data Sinistro", datetime.now())
            stato_nuovo = c2.selectbox("Stato Iniziale", ["Inviata", "Aperta", "In lavorazione"])
            
            danno_nuovo = st.text_input("Descrizione Danno (es. Acqua condotta Int. 4)")
            allegati_nuovi = st.text_input("Link Google Drive Documenti / Foto (opzionale)")
            msg_iniziale = st.text_area("Nota iniziale:")
            
            if st.form_submit_button("💾 Crea Sotto-Scheda Sinistro"):
                condominio_finale = cond_altro.strip() if (not cond_scelto or cond_scelto == "Altro (scrivi sotto)") else cond_scelto
                if not condominio_finale:
                    st.error("Indica il condominio interessato.")
                else:
                    primo_msg = f"[{datetime.now().strftime('%d/%m/%Y %H:%M')}] {msg_iniziale.strip()}" if msg_iniziale.strip() else ""
                    nuovo_sx = pd.DataFrame([{
                        "id": id_nuovo.strip(),
                        "condominio": condominio_finale,
                        "amministratore": cliente_scelto.strip(),
                        "polizza": polizza_nuova.strip(),
                        "danno": danno_nuovo.strip(),
                        "stato": stato_nuovo,
                        "data": str(data_sx),
                        "allegati": allegati_nuovi.strip(),
                        "messaggi": primo_msg
                    }])
                    df_sx_agg = pd.concat([df_sinistri, nuovo_sx], ignore_index=True)
                    salva_dati("sinistri", df_sx_agg)
                    st.success(f"Sinistro {id_nuovo} salvato nella scheda 'sinistri'!")
                    st.rerun()

# =========================================================
# 3. VISTA GLOBALE TUTTI I SINISTRI
# =========================================================
elif menu == "📋 Tutti i Sinistri":
    st.title("📋 Riepilogo Generale Sinistri")
    if df_sinistri.empty:
        st.info("Nessun sinistro presente.")
    else:
        st.dataframe(df_sinistri, use_container_width=True, hide_index=True)
