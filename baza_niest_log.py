import streamlit as st
from supabase import create_client, Client
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- KONFIGURACJA UI ---
st.set_page_config(page_title="Logistics Command Center", layout="wide")

# --- CUSTOM CSS: NATURALNE TŁO + MAKSYMALNA CZYTELNOŚĆ ---
st.markdown("""
    <style>
    /* 1. Naturalne tło magazynu */
    .stApp {
        background: url("https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?q=80&w=2070&auto=format&fit=crop");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }

    /* 2. Karty - Mocne rozmycie (Blur) i przyciemnienie dla czytelności */
    .glass-card {
        background: rgba(15, 23, 42, 0.55); /* Ciemniejsza baza pod białe napisy */
        backdrop-filter: blur(20px) saturate(160%);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 25px;
        padding: 30px;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.6);
        margin-bottom: 25px;
    }

    /* 3. Napisy - Dodany mocny cień dla odcięcia od tła */
    h1, h2, h3, p, span, label {
        color: #ffffff !important;
        text-shadow: 2px 2px 8px rgba(0, 0, 0, 1), 0px 0px 15px rgba(0, 0, 0, 0.8) !important;
        font-weight: 700 !important;
    }

    /* 4. Metryki - Jaskrawy cyjan (bardzo czytelny) */
    [data-testid="stMetricValue"] {
        color: #00e5ff !important;
        font-size: 2.3rem !important;
        font-weight: 900 !important;
        text-shadow: 0px 0px 15px rgba(0, 229, 255, 0.4) !important;
    }
    
    [data-testid="stMetricLabel"] {
        color: #cbd5e1 !important;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        font-size: 0.9rem !important;
    }

    /* 5. Kontrola formularzy - Wysoki kontrast białego tła */
    .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] {
        background-color: rgba(255, 255, 255, 1) !important;
        color: #0f172a !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
    }

    /* 6. Przyciski - Gradient logistyczny */
    .stButton>button {
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%) !important;
        color: white !important;
        border: none !important;
        padding: 14px 30px !important;
        border-radius: 12px !important;
        font-weight: 800 !important;
        letter-spacing: 1px;
        transition: all 0.3s ease !important;
    }
    .stButton>button:hover {
        transform: scale(1.03);
        box-shadow: 0 0 20px rgba(59, 130, 246, 0.6) !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- POŁĄCZENIE Z BAZĄ ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

@st.cache_data(ttl=20)
def fetch_data():
    try:
        p = supabase.table("produkty").select("*").execute().data
        k = supabase.table("kategorie").select("*").execute().data
        return pd.DataFrame(p), pd.DataFrame(k)
    except:
        return pd.DataFrame(), pd.DataFrame()

# --- INTERFEJS ---
st.title("🛰️ Logistics Command Center v4.0")
st.markdown("### System Monitoringu i Zarządzania Zapasami")

try:
    df_p, df_k = fetch_data()
    
    if not df_p.empty and not df_k.empty:
        df = df_p.merge(df_k, left_on="kategoria_id", right_on="id", suffixes=('_p', '_k'))
        df['wartosc'] = df['cena'] * df['liczba']

        # --- KPI ---
        c1, c2, c3, c4 = st.columns(4)
        kpis = [
            ("Kapitał Towarowy", f"{df['wartosc'].sum():,.2f} zł"),
            ("Jednostki SKU", len(df)),
            ("Stan Magazynu", int(df['liczba'].sum())),
            ("Alerty Krytyczne", len(df[df['liczba'] < 5]))
        ]
        
        for i, (lab, val) in enumerate(kpis):
            with [c1, c2, c3, c4][i]:
                st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
                st.metric(lab, val)
                st.markdown("</div>", unsafe_allow_html=True)

        # --- WYKRESY ---
        col_chart1, col_chart2 = st.columns([1.5, 1])
        
        with col_chart1:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.subheader("📊 Monitoring Poziomu Zapasów")
            fig = px.bar(df, x="nazwa_p", y="liczba", color="nazwa_k", template="plotly_dark")
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with col_chart2:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.subheader("💰 Podział Wartościowy")
            fig2 = go.Figure(data=[go.Pie(labels=df['nazwa_k'], values=df['wartosc'], hole=.5)])
            fig2.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', showlegend=False)
            st.plotly_chart(fig2, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # --- OPERACJE ---
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        tab1, tab2, tab3 = st.tabs(["📋 Rejestr", "➕ Nowa Dostawa", "🗑️ Usuwanie"])
        
        with tab1:
            st.dataframe(df[['id_p', 'nazwa_p', 'liczba', 'cena', 'nazwa_k']], use_container_width=True)
            
        with tab2:
            with st.form("add"):
                fa, fb, fc = st.columns(3)
                n = fa.text_input("Nazwa produktu")
                l = fb.number_input("Ilość", min_value=1)
                c = fc.number_input("Cena", min_value=0.01)
                k = st.selectbox("Wybierz kategorię", df_k['nazwa'].unique())
                if st.form_submit_button("DODAJ DO BAZY"):
                    kid = int(df_k[df_k['nazwa']==k]['id'].values[0])
                    supabase.table("produkty").insert({"nazwa":n, "liczba":l, "cena":c, "kategoria_id":kid}).execute()
                    st.rerun()

        with tab3:
            did = st.number_input("Podaj ID do usunięcia", step=1, value=0)
            if st.button("🔴 POTWIERDŹ USUNIĘCIE"):
                supabase.table("produkty").delete().eq("id", did).execute()
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

except Exception as e:
    st.error(f"⚠️ Utrata połączenia: {e}")
