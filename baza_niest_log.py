import streamlit as st
from supabase import create_client, Client
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from segno import make_qr
import io
from PIL import Image

# --- KONFIGURACJA ---
st.set_page_config(page_title="Warehouse Intelligence OS", layout="wide")

# --- CUSTOM CSS (PREMIUM DARK LOGISTICS) ---
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(rgba(10, 20, 30, 0.85), rgba(10, 20, 30, 0.95)), 
                    url("https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?q=80&w=2070&auto=format&fit=crop");
        background-size: cover; background-attachment: fixed;
    }
    .glass-card {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(15px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px; padding: 25px; margin-bottom: 20px;
    }
    .status-critical { border-left: 5px solid #ff4b4b; background: rgba(255, 75, 75, 0.1); padding: 10px; border-radius: 5px; }
    h1, h2, h3 { color: #60a5fa !important; font-family: 'Inter', sans-serif; }
    .stMetric { background: rgba(0,0,0,0.2); padding: 15px; border-radius: 15px; border: 1px solid #1e293b; }
    </style>
    """, unsafe_allow_html=True)

# --- POŁĄCZENIE ---
url, key = st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# --- LOGIKA DANYCH ---
def get_data():
    p = supabase.table("produkty").select("*").execute().data
    k = supabase.table("kategorie").select("*").execute().data
    return pd.DataFrame(p), pd.DataFrame(k)

# Inicjalizacja historii w sesji (Audit Log)
if 'history' not in st.session_state:
    st.session_state.history = []

def log_event(action):
    st.session_state.history.append({"Czas": pd.Timestamp.now().strftime("%H:%M:%S"), "Akcja": action})

# --- START APLIKACJI ---
st.title("🛰️ Warehouse Intelligence OS")
st.markdown("Zintegrowany System Zarządzania i Analizy Logistycznej")

try:
    df_p, df_k = get_data()
    if not df_p.empty and not df_k.empty:
        df = df_p.merge(df_k, left_on="kategoria_id", right_on="id", suffixes=('_p', '_k'))
        df['wartosc_total'] = df['cena'] * df['liczba']

        # --- SEKCJA 1: SMART ALERTS ---
        critical = df[df['liczba'] < 5]
        if not critical.empty:
            with st.container():
                st.markdown(f"<div class='status-critical'>⚠️ <b>ALERTA ZAPASÓW:</b> {len(critical)} produktów wymaga pilnego uzupełnienia!</div>", unsafe_allow_html=True)
                st.write("##")

        # --- SEKCJA 2: KPI & FINANCIALS ---
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Kapitał Zamrożony", f"{df['wartosc_total'].sum():,.2f} zł")
        c2.metric("Jednostki (Łącznie)", int(df['liczba'].sum()))
        c3.metric("Średnia Marża (Est.)", "24.5%")
        c4.metric("Wydajność Magazynu", "92%", delta="4%")

        st.write("---")

        # --- SEKCJA 3: ANALITYKA ---
        col_main, col_side = st.columns([2, 1])
        
        with col_main:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.subheader("📊 Analiza Dostępności SKU")
            fig = px.bar(df, x="nazwa_p", y="liczba", color="wartosc_total", 
                         template="plotly_dark", color_continuous_scale="Blues")
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with col_side:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.subheader("📦 Podział Kategorii")
            fig_pie = px.pie(df, values='liczba', names='nazwa_k', hole=0.5, template="plotly_dark")
            fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', showlegend=False)
            st.plotly_chart(fig_pie, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # --- SEKCJA 4: OPERACJE (TABS) ---
        t_inv, t_qr, t_add, t_logs = st.tabs(["📋 Inwentarz", "📱 Generator QR", "➕ Nowa Dostawa", "📜 Dziennik Zdarzeń"])

        with t_inv:
            search = st.text_input("🔍 Szybkie filtrowanie bazy danych...")
            df_f = df[df['nazwa_p'].str.contains(search, case=False)] if search else df
            st.dataframe(df_f[['id_p', 'nazwa_p', 'liczba', 'cena', 'nazwa_k', 'wartosc_total']], use_container_width=True)
            
            # Usuwanie
            with st.expander("🔴 Usuwanie produktów"):
                del_id = st.number_input("Podaj ID do usunięcia", step=1)
                if st.button("POTWIERDŹ USUNIĘCIE"):
                    supabase.table("produkty").delete().eq("id", del_id).execute()
                    log_event(f"Usunięto produkt ID: {del_id}")
                    st.rerun()

        with t_qr:
            st.subheader("Generowanie etykiet QR")
            sel_prod = st.selectbox("Wybierz produkt do etykiety", df['nazwa_p'].unique())
            prod_info = df[df['nazwa_p'] == sel_prod].iloc[0]
            
            # Generowanie QR
            qr_content = f"ID: {prod_info['id_p']} | Nazwa: {prod_info['nazwa_p']} | Magazyn Centralny"
            qrcode = make_qr(qr_content)
            out = io.BytesIO()
            qrcode.save(out, kind='png', scale=10)
            
            col_qr1, col_qr2 = st.columns([1, 2])
            col_qr1.image(out.getvalue(), caption=f"Kod QR dla {sel_prod}")
            col_qr2.write(f"**Dane zakodowane:**\n\n{qr_content}")
            col_qr2.download_button("Pobierz Etykietę PNG", out.getvalue(), f"QR_{sel_prod}.png")

        with t_add:
            c_p, c_k = st.columns(2)
            with c_p:
                with st.form("p_form"):
                    st.write("### ➕ Produkt")
                    n = st.text_input("Nazwa")
                    l = st.number_input("Ilość", min_value=0)
                    c = st.number_input("Cena", min_value=0.0)
                    k = st.selectbox("Kategoria", df_k['nazwa'].unique())
                    if st.form_submit_button("DODAJ"):
                        kid = int(df_k[df_k['nazwa']==k]['id'].values[0])
                        supabase.table("produkty").insert({"nazwa":n, "liczba":l, "cena":c, "kategoria_id":kid}).execute()
                        log_event(f"Dodano produkt: {n}")
                        st.rerun()
            with c_k:
                with st.form("k_form"):
                    st.write("### 📂 Kategoria")
                    kn = st.text_input("Nazwa")
                    if st.form_submit_button("UTWÓRZ"):
                        supabase.table("kategorie").insert({"nazwa":kn}).execute()
                        log_event(f"Dodano kategorię: {kn}")
                        st.rerun()

        with t_logs:
            st.subheader("Historia ostatnich działań")
            if st.session_state.history:
                st.table(pd.DataFrame(st.session_state.history).iloc[::-1])
            else:
                st.info("Brak zarejestrowanych działań w tej sesji.")

except Exception as e:
    st.error(f"Połącz bazę Supabase w Secrets! Błąd: {e}")
