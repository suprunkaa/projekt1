import streamlit as st
from supabase import create_client, Client
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- KONFIGURACJA UI ---
st.set_page_config(page_title="Logistics Command Center", layout="wide")

# --- CUSTOM CSS: MAKSYMALNA WIDOCZNOŚĆ ---
st.markdown("""
    <style>
    /* 1. Tło magazynu */
    .stApp {
        background: url("https://images.unsplash.com/photo-1587293855946-90c5df244543?q=80&w=2070&auto=format&fit=crop");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }

    /* 2. Karty - Mocniejsze szkło i kontrast */
    .glass-card {
        background: rgba(15, 23, 42, 0.4); /* Ciemniejsza baza pod tekst */
        backdrop-filter: blur(25px) saturate(150%);
        -webkit-backdrop-filter: blur(25px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 20px;
        padding: 25px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
        margin-bottom: 20px;
    }

    /* 3. Napisy - Dodany cień (Text Shadow) dla czytelności */
    h1, h2, h3, p, span, label, .stMarkdown {
        color: #ffffff !important;
        text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.9), 0px 0px 10px rgba(0, 0, 0, 0.5) !important;
        font-weight: 600 !important;
    }

    /* 4. Metryki - Bardziej wyraziste */
    [data-testid="stMetricValue"] {
        color: #38bdf8 !important; /* Jasny błękit */
        font-size: 2.2rem !important;
        font-weight: 800 !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.8) !important;
    }
    
    [data-testid="stMetricLabel"] {
        color: #f1f5f9 !important;
        background: rgba(0,0,0,0.3); /* Lekkie tło pod samą etykietę */
        padding: 2px 8px;
        border-radius: 5px;
    }

    /* 5. Inputs - Wyraźne pola tekstowe */
    .stTextInput input, .stNumberInput input, .stSelectbox div {
        background-color: rgba(255, 255, 255, 0.9) !important;
        color: #0f172a !important;
        font-weight: 700 !important;
    }

    /* 6. Przyciski */
    .stButton>button {
        background: linear-gradient(135deg, #0ea5e9 0%, #2563eb 100%) !important;
        border: none !important;
        font-weight: 800 !important;
        text-transform: uppercase;
        letter-spacing: 1px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4) !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- POŁĄCZENIE Z BAZĄ ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

@st.cache_data(ttl=30)
def fetch_all_data():
    try:
        p = supabase.table("produkty").select("*").execute().data
        k = supabase.table("kategorie").select("*").execute().data
        return pd.DataFrame(p), pd.DataFrame(k)
    except:
        return pd.DataFrame(), pd.DataFrame()

# --- UKŁAD ---
st.title("🌐 Logistics Command Center")

try:
    df_p, df_k = fetch_all_data()
    
    if not df_p.empty and not df_k.empty:
        df = df_p.merge(df_k, left_on="kategoria_id", right_on="id", suffixes=('_p', '_k'))
        df['total_val'] = df['cena'] * df['liczba']

        # --- SEKCJA 1: KPI ---
        cols = st.columns(4)
        metrics = [
            ("Kapitał", f"{df['total_val'].sum():,.2f} zł"),
            ("Liczba SKU", len(df)),
            ("Suma sztuk", int(df['liczba'].sum())),
            ("Alerty", len(df[df['liczba'] < 10]))
        ]
        
        for i, (label, val) in enumerate(metrics):
            with cols[i]:
                st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
                st.metric(label, val)
                st.markdown("</div>", unsafe_allow_html=True)

        # --- SEKCJA 2: ANALITYKA ---
        cl, cr = st.columns([1.6, 1])
        
        with cl:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.subheader("📦 Monitoring Stanów")
            fig = px.bar(df, x="nazwa_p", y="liczba", color="nazwa_k", template="plotly_dark")
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with cr:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.subheader("💰 Struktura Wartości")
            fig2 = go.Figure(data=[go.Pie(labels=df['nazwa_k'], values=df['total_val'], hole=.5)])
            fig2.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', showlegend=False)
            st.plotly_chart(fig2, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # --- SEKCJA 3: PANEL ZARZĄDZANIA ---
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        t1, t2, t3 = st.tabs(["📋 Baza Danych", "⚙️ Kontrola", "➕ Operacje"])
        
        with t1:
            st.dataframe(df[['id_p', 'nazwa_p', 'liczba', 'cena', 'nazwa_k']], use_container_width=True)
            
        with t2:
            del_id = st.number_input("ID produktu do usunięcia", step=1, value=0)
            if st.button("USUŃ Z SERWERA"):
                supabase.table("produkty").delete().eq("id", del_id).execute()
                st.success("Usunięto.")
                st.rerun()

        with t3:
            with st.form("add_p"):
                st.write("### Dodaj Nowy Produkt")
                n = st.text_input("Nazwa")
                l = st.number_input("Ilość", min_value=1)
                c = st.number_input("Cena", min_value=0.1)
                k = st.selectbox("Kategoria", df_k['nazwa'].unique())
                if st.form_submit_button("ZATWIERDŹ"):
                    k_id = int(df_k[df_k['nazwa']==k]['id'].values[0])
                    supabase.table("produkty").insert({"nazwa":n, "liczba":l, "cena":c, "kategoria_id":k_id}).execute()
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

except Exception as e:
    st.error(f"Błąd: {e}")
