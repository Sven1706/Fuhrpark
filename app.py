import streamlit as st
import pandas as pd
from datetime import datetime
from sqlalchemy import text

# --- 1. EINSTELLUNGEN ---
# WICHTIG: Hier deine E-Mail-Adresse eintragen!
ADMIN_EMAIL = "deine-email@beispiel.de" 

# Prüft, wer eingeloggt ist (Sichere Variante)
try:
    user_email = st.user.email 
except:
    user_email = None

# --- 2. DATENBANK ---
def get_conn():
    return st.connection('werkstatt_db', type='sql')

def init_db():
    conn = get_conn()
    with conn.session as s:
        # Grundtabellen erstellen, falls nicht vorhanden
        s.execute(text("CREATE TABLE IF NOT EXISTS fahrzeuge (id INTEGER PRIMARY KEY, name TEXT UNIQUE, stand REAL, einheit TEXT);"))
        s.execute(text("CREATE TABLE IF NOT EXISTS schaeden (id INTEGER PRIMARY KEY, zeitpunkt TEXT, fz_name TEXT, info TEXT, status TEXT DEFAULT 'Offen');"))
        
        # Neue Typ-Spalte anbauen (Fehler wird ignoriert, falls Spalte schon da ist)
        try:
            s.execute(text("ALTER TABLE fahrzeuge ADD COLUMN typ TEXT;"))
        except:
            pass 
        s.commit()

# Startet die Datenbankprüfung
init_db()

# --- 3. MENÜ & NAVIGATION ---
menu = ["📊 Monitor", "📸 Schadensmeldung"]
is_admin = (user_email == ADMIN_EMAIL)

if is_admin:
    menu.append("🚜 Fahrzeugstamm (Admin)")

st.sidebar.title("🛠️ Werkstatt-System")
choice = st.sidebar.radio("Navigation:", menu)

if user_email:
    st.sidebar.caption(f"Eingeloggt als: {user_email}")
else:
    st.sidebar.caption("Nicht eingeloggt (Gastmodus)")

# --- 4. SCHADENSMELDUNG ---
if choice == "📸 Schadensmeldung":
    st.header("📸 Neuen Schaden melden")
    conn = get_conn()
    
    # Fahrzeuge aus der Datenbank holen
    df_fz = conn.query("SELECT name FROM fahrzeuge")
    
    if df_fz.empty:
        st.warning("⚠️ Keine Fahrzeuge im System. Bitte Admin kontaktieren.")
    else:
        with st.form("meldung_form"):
            fz = st.selectbox("Betroffenes Fahrzeug:", df_fz['name'])
            info = st.text_area("Was ist defekt?", placeholder="Kurze Beschreibung...")
            foto = st.file_uploader("Foto hinzufügen", type=["jpg", "jpeg", "png"])
            
            if st.form_submit_button("Meldung abschicken"):
                if info:
                    zeit = datetime.now().strftime("%d.%m.%Y %H:%M")
                    with conn.session as s:
                        s.execute(
                            text("INSERT INTO schaeden (zeitpunkt, fz_name, info) VALUES (:z, :f, :i)"),
                            params={"z": zeit, "f": fz, "i": info}
                        )
                        s.commit()
                    st.success(f"✅ Schaden an {fz} wurde gemeldet!")
                else:
                    st.error("Bitte gib eine Beschreibung an.")

# --- 5. MONITOR ---
elif choice == "📊 Monitor":
    st.header("📊 Aktuelle Meldungen")
    conn = get_conn()
    df = conn.query("SELECT zeitpunkt, fz_name, info, status FROM schaeden ORDER BY id DESC")
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Aktuell liegen keine Meldungen vor.")

# --- 6. ADMIN-BEREICH ---
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
                    try:
                        s_db.execute(
                            text("INSERT INTO fahrzeuge (name, typ, stand, einheit) VALUES (:n, :t, :s, :e)"),
                            params={"n": n, "t": t, "s": s, "e": e}
                        )
                        s_db.commit()
                        st.success(f"{t} '{n}' wurde angelegt!")
                    except Exception as e_msg:
                        st.error("Fehler: Möglicherweise existiert dieser Name bereits.")
            else:
                st.error("Bitte einen Namen eingeben.")
