import streamlit as st
import pandas as pd
from datetime import datetime

# --- 1. ADMIN-EINSTELLUNG ---
# Trage hier DEINE E-Mail ein, um Admin-Rechte zu haben
ADMIN_EMAIL = "deine-email@beispiel.de" 

# Prüfen, wer eingeloggt ist (Streamlit Cloud erkennt das automatisch)
user_email = st.experimental_user.email 

# --- 2. DATENBANK-SETUP ---
# Wir nutzen die "Permanent-Datei" über die Streamlit Secrets (wie besprochen)
def get_conn():
    return st.connection('werkstatt_db', type='sql')

def init_db():
    conn = get_conn()
    with conn.session as s:
        s.execute("CREATE TABLE IF NOT EXISTS fahrzeuge (id INTEGER PRIMARY KEY, name TEXT UNIQUE, stand REAL, einheit TEXT);")
        s.execute("CREATE TABLE IF NOT EXISTS schaeden (id INTEGER PRIMARY KEY, zeitpunkt TEXT, fz_name TEXT, info TEXT, status TEXT DEFAULT 'Offen');")
        s.commit()

init_db()

# --- 3. DYNAMISCHES MENÜ (ADMIN-SPERRE) ---
# Standard-Menü für alle (Externe/Kollegen)
menu = ["📊 Monitor", "📸 Schadensmeldung"]

# Admin-Erweiterung nur für dich sichtbar
is_admin = (user_email == ADMIN_EMAIL)
if is_admin:
    menu.append("🚜 Fahrzeugstamm (Admin)")

st.sidebar.title("🛠️ Werkstatt-System")
choice = st.sidebar.radio("Navigation:", menu)
if user_email:
    st.sidebar.caption(f"Eingeloggt als: {user_email}")

# --- 4. LOGIK: SCHADENSMELDUNG (MOBIL OPTIMIERT) ---
if choice == "📸 Schadensmeldung":
    st.header("📸 Neuen Schaden melden")
def init_db():
    conn = get_conn()
    with conn.session as s:
        s.execute("CREATE TABLE IF NOT EXISTS fahrzeuge (id INTEGER PRIMARY KEY, name TEXT UNIQUE, stand REAL, einheit TEXT);")
        # DIESE ZEILE FÜGT DIE TYP-SPALTE NACHTRÄGLICH EIN (falls sie fehlt):
        try:
            s.execute("ALTER TABLE fahrzeuge ADD COLUMN typ TEXT;")
        except:
            pass # Falls die Spalte schon da ist, ignoriere den Fehler
        
        s.execute("CREATE TABLE IF NOT EXISTS schaeden (id INTEGER PRIMARY KEY, zeitpunkt TEXT, fz_name TEXT, info TEXT, status TEXT DEFAULT 'Offen');")
        s.commit()
