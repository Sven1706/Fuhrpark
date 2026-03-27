import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import io
from PIL import Image

# --- 1. DATENBANK-LOGIK ---
def get_db_connection():
    conn = sqlite3.connect('werkstatt_v9.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    # Fahrzeugtabelle
    conn.execute("""CREATE TABLE IF NOT EXISTS fahrzeugstamm (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        hersteller TEXT,
        stand REAL DEFAULT 0,
        einheit TEXT DEFAULT 'h'
    )""")
    # Schadensmeldungen
    conn.execute("""CREATE TABLE IF NOT EXISTS schadensmeldungen (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        zeitpunkt TEXT,
        fahrzeug_name TEXT,
        beschreibung TEXT,
        dringlichkeit TEXT,
        status TEXT DEFAULT 'Offen'
    )""")
    conn.commit()
    conn.close()

init_db()

# --- 2. NAVIGATION ---
st.sidebar.title("🛠️ Werkstatt-System v9")
menu = ["📊 Monitor", "📸 Schadensmeldung", "🚜 Fahrzeugstamm"]
choice = st.sidebar.radio("Bereich wählen:", menu)

conn = get_db_connection()

# --- BEREICH: SCHADENSMELDUNG (EXTERN & LIVE) ---
if choice == "📸 Schadensmeldung":
    st.header("📸 Schadensmeldung aufnehmen")
    st.info("Du kannst entweder ein Live-Foto machen oder ein Bild von deinem Gerät hochladen.")
    
    df_fz = pd.read_sql_query("SELECT name FROM fahrzeugstamm", conn)
    
    if df_fz.empty:
        st.warning("⚠️ Bitte zuerst Fahrzeuge im Fahrzeugstamm anlegen!")
    else:
        # Auswahl des Fahrzeugs (wichtig für die Zuordnung)
        fz_name = st.selectbox("Betroffenes Fahrzeug", df_fz['name'])
        
        # Eingabe der Details
        beschreibung = st.text_area("Was ist defekt?", placeholder="Beschreibe den Schaden kurz...")
        dringlichkeit = st.select_slider("Dringlichkeit", options=["Niedrig", "Mittel", "Hoch", "🚨 Sofort-Stopp"])
        
        st.divider()
        
        # --- ZWEI WEGE FÜR BILDER ---
        col_cam, col_file = st.columns(2)
        
        with col_cam:
            st.write("### 📸 Live-Kamera")
            foto_live = st.camera_input("Kamera starten")
            
        with col_file:
            st.write("### 📁 Bild hochladen")
            foto_upload = st.file_uploader("Bild aus Galerie/Ordner wählen", type=["jpg", "jpeg", "png"])

        # Logik zum Speichern
        if st.button("Schaden jetzt verbindlich melden", use_container_width=True, type="primary"):
            if beschreibung:
                zeit = datetime.now().strftime("%d.%m.%Y %H:%M")
                conn.execute("""INSERT INTO schadensmeldungen (zeitpunkt, fahrzeug_name, beschreibung, dringlichkeit) 
                             VALUES (?,?,?,?)""", (zeit, fz_name, beschreibung, dringlichkeit))
                conn.commit()
                
                st.success(f"✅ Schaden an {fz_name} wurde gemeldet!")
                
                # Vorschau anzeigen, falls ein Bild vorhanden ist
                if foto_live:
                    st.image(foto_live, caption="Aufgenommenes Live-Foto", width=300)
                elif foto_upload:
                    st.image(foto_upload, caption="Hochgeladenes Bild", width=300)
            else:
                st.error("Bitte gib eine Beschreibung des Schadens an.")

# --- BEREICH: MONITOR ---
elif choice == "📊 Monitor":
    st.header("📊 Werkstatt-Monitor")
    
    st.subheader("🚨 Offene Schadensmeldungen")
    df_schaden = pd.read_sql_query("SELECT * FROM schadensmeldungen WHERE status='Offen' ORDER BY id DESC", conn)
    
    if df_schaden.empty:
        st.success("Aktuell keine Schäden gemeldet.")
    else:
        st.table(df_schaden) # Tabelle für bessere Übersicht

# --- BEREICH: FAHRZEUGSTAMM (KORREKTUR km/h) ---
elif choice == "🚜 Fahrzeugstamm":
    st.header("🚜 Fahrzeugstamm-Verwaltung")
    
    with st.expander("➕ Neues Fahrzeug anlegen"):
        with st.form("neu"):
            c1, c2 = st.columns(2)
            n = c1.text_input("Name/ID")
            h = c1.text_input("Hersteller")
            s = c2.number_input("Stand", min_value=0.0)
            e = c2.selectbox("Einheit", ["h", "km"])
            if st.form_submit_button("Speichern"):
                conn.execute("INSERT INTO fahrzeugstamm (name, hersteller, stand, einheit) VALUES (?,?,?,?)", (n, h, s, e))
                conn.commit()
                st.rerun()

    st.subheader("📝 Zählerstände & Einheiten anpassen")
    df = pd.read_sql_query("SELECT * FROM fahrzeugstamm", conn)
    for _, r in df.iterrows():
        c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
        c1.write(f"**{r['name']}**")
        n_s = c2.number_input(f"S_{r['id']}", value=float(r['stand']), key=f"s_{r['id']}", label_visibility="collapsed")
        n_e = c3.selectbox(f"E_{r['id']}", ["h", "km"], index=(0 if r['einheit']=='h' else 1), key=f"e_{r['id']}", label_visibility="collapsed")
        if c4.button("💾", key=f"b_{r['id']}"):
            conn.execute("UPDATE fahrzeugstamm SET stand=?, einheit=? WHERE id=?", (n_s, n_e, r['id']))
            conn.commit()
            st.rerun()

conn.close()
