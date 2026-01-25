import streamlit as st
import subprocess
import sys

# --- AUTOMATYCZNA INSTALACJA BRAKUJĄCYCH MODUŁÓW ---
def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
    import segno
except ImportError:
    install('segno')
    import segno

from supabase import create_client, Client
import pandas as pd
import plotly.express as px
import io

# --- KONFIGURACJA UI ---
st.set_page_config(page_title="Logistics Command Center", layout="wide")

# --- DESIGN: DARK LOGISTICS MODE ---
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(rgba(0, 0, 0, 0.75), rgba(0, 0, 0, 0.85)), 
                    url("https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?q=80&w=2070");
        background-size: cover;
        background-attachment: fixed;
    }
    .main-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 20px;
    }
    h1, h2, h3 { color: #3b82f6 !important; }
    .stMetric { background: rgba(0,0,0,0.3); border-radius: 10px; padding: 10px; border: 1px solid #1e293b; }
    </style>
    """, unsafe_allow_html=True)

# --- POŁĄCZENIE ---
@st.cache_resource
def init_connection():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_connection()

# --- DANE ---
def fetch_data():
    p = supabase.table("produkty").select("*").execute().data
    k = supabase.table("kategorie").select("*").execute().data
    df_p = pd.DataFrame(p)
    df_k = pd.DataFrame(k)
    if not df_p.empty and not df_k.empty:
        return df_p.merge(df_k, left_on="kategoria_id", right_on="id", suffixes=('_prod', '_kat'))
    return pd.DataFrame()

# --- DASHBOARD ---
st.title("🛰️ Magazyn Inteligentny v4.0")
df = fetch_data()

if not df.empty:
    df['total_val'] = df['cena'] * df['liczba']
    
    # 1. KPI
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Wartość Sumaryczna", f"{df['total_val'].sum():,.2f} zł")
    c2.metric("Liczba SKU", len(df))
    c3.metric("Stan magazynowy", int(df['liczba'].sum()))
    low_stock = len(df[df['liczba'] < 5])
    c4.metric("Alerty", low_stock, delta="- Braki!" if low_stock > 0 else "OK", delta_color="inverse")

    st.write("---")

    # 2. ANALITYKA
    col_l, col_r = st.columns([2, 1])
    with col_l:
        st.markdown("<div class='main-card'>", unsafe_allow_html=True)
        st.subheader("📊 Stan Zapasu per Produkt")
        fig = px.bar(df, x="nazwa_prod", y="liczba", color="nazwa_kat", template="plotly_dark")
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_r:
        st.markdown("<div class='main-card'>", unsafe_allow_html=True)
        st.subheader("🥧 Udział Kategorii")
        fig2 = px.pie(df, values='total_val', names='nazwa_kat', hole=0.4, template="plotly_dark")
        fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig2, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # 3. ZARZĄDZANIE (TABS)
    tab1, tab2, tab3 = st.tabs(["📋 Rejestr & QR", "➕ Dodaj Nowe", "🗑️ Usuwanie"])

    with tab1:
        st.dataframe(df[['id_prod', 'nazwa_prod', 'liczba', 'cena', 'nazwa_kat']], use_container_width=True)
        st.subheader("📱 Generuj Etykietę QR")
        selected = st.selectbox("Wybierz produkt", df['nazwa_prod'].unique())
        p_row = df[df['nazwa_prod'] == selected].iloc[0]
        
        qr = segno.make(f"ID:{p_row['id_prod']} | {p_row['nazwa_prod']} | Kat:{p_row['nazwa_kat']}")
        buff = io.BytesIO()
        qr.save(buff, kind='png', scale=10)
        st.image(buff.getvalue(), width=150, caption=f"Kod QR dla {selected}")

    with tab2:
        col_a, col_b = st.columns(2)
        with col_a:
            with st.form("new_p"):
                st.write("### Dodaj Produkt")
                n = st.text_input("Nazwa")
                l = st.number_input("Ilość", min_value=0)
                c = st.number_input("Cena", min_value=0.0)
                k = st.selectbox("Kategoria", df['nazwa_kat'].unique())
                if st.form_submit_button("Dodaj"):
                    k_id = int(df[df['nazwa_kat'] == k]['id_kat'].values[0])
                    supabase.table("produkty").insert({"nazwa":n, "liczba":l, "cena":c, "kategoria_id":k_id}).execute()
                    st.rerun()
        with col_b:
            with st.form("new_k"):
                st.write("### Nowa Kategoria")
                kn = st.text_input("Nazwa kategorii")
                if st.form_submit_button("Stwórz"):
                    supabase.table("kategorie").insert({"nazwa":kn}).execute()
                    st.rerun()

    with tab3:
        st.error("Strefa Usuwania")
        del_id = st.number_input("Podaj ID produktu do usunięcia", step=1)
        if st.button("🔴 USUŃ TRWALE"):
            supabase.table("produkty").delete().eq("id", del_id).execute()
            st.success("Usunięto!")
            st.rerun()

else:
    st.info("Baza jest pusta. Zainicjuj dane w zakładce Dodaj Nowe.")
