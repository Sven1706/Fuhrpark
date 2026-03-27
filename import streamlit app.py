import streamlit as st
import pandas as pd
from datetime import datetime

# --- 1. ADMIN-EINSTELLUNG ---
ADMIN_EMAIL = "deine-email@beispiel.de" # <-- DEINE EMAIL HIER EINTRAGEN

# Sicherer Check der Benutzer-E-Mail
try:
    # Versuche die E-Mail abzurufen (funktioniert nur live in der Cloud)
    user_email = st.user.email 
except:
    user_email = None

# --- 2. DATENBANK-SETUP ---
def get_conn():
    return st.connection('werkstatt_db', type='sql')

def init_db():
    conn = get_conn()
    with conn.session as s:
        # Grundtabellen
        s.execute("CREATE TABLE IF NOT EXISTS fahrzeuge (id INTEGER PRIMARY KEY, name TEXT UNIQUE, stand REAL, einheit TEXT);")
        s.execute("CREATE TABLE IF NOT EXISTS schaeden (id INTEGER PRIMARY KEY, zeitpunkt TEXT, fz_name TEXT, info TEXT, status TEXT DEFAULT 'Offen');")
        
        # Spalte TYP nachträglich hinzufügen, falls sie fehlt
        try:
            s.execute("ALTER TABLE fahrzeuge ADD COLUMN typ TEXT;")
        except:
            pass 
        s.commit()

init_db()

# --- 3. NAVIGATION ---
menu = ["📊 Monitor", "📸 Schadensmeldung"]
is_admin = (user_email == ADMIN_EMAIL)

if is_admin:
    menu.append("🚜 Fahrzeugstamm (Admin)")

st.sidebar.title("🛠️ Werkstatt-System")
choice = st.sidebar.radio("Navigation:", menu)
if user_email:
    st.sidebar.caption(f"Eingeloggt als: {user_email}")

# --- 4. LOGIK: SCHADENSMELDUNG ---
if choice == "📸 Schadensmeldung":
    st.header("📸 Neuen Schaden melden")
    conn = get_conn()
    df_fz = conn.query("SELECT name FROM fahrzeuge")
    
    if df_fz.empty:
        st.warning("⚠️ Keine Fahrzeuge im System. Bitte Admin kontaktieren.")
    else:
        with st.form("meldung_form"):
            fz = st.selectbox("Betroffenes Fahrzeug:", df_fz['name'])
            info = st.text_area("Was ist defekt?", placeholder="Kurze Beschreibung...")
            foto = st.file_uploader("Foto hinzufügen (Galerie oder Kamera)", type=["jpg", "jpeg", "png"])
            
            if st.form_submit_button("Meldung abschicken"):
                if info:
                    zeit = datetime.now().strftime("%d.%m.%Y %H:%M")
                    with conn.session as s:
                        s.execute(
                            "INSERT INTO schaeden (zeitpunkt, fz_name, info) VALUES (:z, :f, :i)",
                            params={"z": zeit, "f": fz, "i": info}
                        )
                        s.commit()
                    st.success(f"✅ Schaden an {fz} wurde gemeldet!")
                else:
                    st.error("Bitte gib eine Beschreibung an.")

# --- 5. LOGIK: MONITOR ---
elif choice == "📊 Monitor":
    st.header("📊 Aktuelle Meldungen")
    conn = get_conn()
    df = conn.query("SELECT zeitpunkt, fz_name, info, status FROM schaeden ORDER BY id DESC")
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Keine Meldungen vorhanden.")

# --- 6. LOGIK: FAHRZEUGSTAMM (ADMIN) ---
elif choice == "🚜 Fahrzeugstamm (Admin)":
    st.header("🚜 Fahrzeugverwaltung")
    
    with st.form("neu_fz"):
        col1, col2 = st.columns(2)
        with col1:
            n = st.text_input("Bezeichnung (z.B. Bagger 01)")
            t = st.selectbox("Typ", ["LKW", "Bagger", "PKW", "Radlader", "Sonstiges"])
        with col2:
            s = st.number_input("Stand", min_value=0.0)
            e = st.selectbox("Einheit", ["h", "km"])
            
        if st.form_submit_button("Speichern"):
            if n:
                conn = get_conn()
                with conn.session as s_db:
                    s_db.execute(
                        "INSERT INTO fahrzeuge (name, typ, stand, einheit) VALUES (:n, :t, :s, :e)",
                        params={"n": n, "t": t, "s": s, "e": e}
                    )
                    s_db.commit()
                st.success(f"{t} '{n}' angelegt!")
                st.rerun()
            else:
                st.error("Name fehlt!")
