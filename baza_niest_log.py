import streamlit as st
from supabase import create_client, Client
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Logistics Intelligence OS", layout="wide")

# --- CUSTOM CSS: NATURALNE TŁO + MOCNE SZKŁO ---
st.markdown("""
    <style>
    /* Naturalne tło magazynu bez nakładek kolorystycznych */
    .stApp {
        background: url("https://images.unsplash.com/photo-1587293855946-90c5df244543?q=80&w=2070&auto=format&fit=crop");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }

    /* Karty Glassmorphism - mocne rozmycie tła zamiast koloru */
    .glass-card {
        background: rgba(255, 255, 255, 0.15); /* Prawie przezroczyste */
        backdrop-filter: blur(20px) saturate(180%); /* Tu dzieje się magia */
        -webkit-backdrop-filter: blur(20px) saturate(180%);
        border: 1px solid rgba(255, 255, 255, 0.3);
        border-radius: 20px;
        padding: 25px;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.2);
        margin-bottom: 20px;
        color: white; /* Tekst biały, aby odbijał od rozmytego tła */
    }

    /* Nagłówki z cieniem dla lepszej czytelności na tle */
    h1, h2, h3 {
        color: white !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        font-weight: 800 !important;
    }

    /* Metryki - neonowy błękit dla kontrastu */
    [data-testid="stMetricValue"] {
        color: #00d4ff !important;
        font-size: 2.2rem !important;
        text-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
    }
    
    [data-testid="stMetricLabel"] {
        color: #e0e0e0 !important;
        letter-spacing: 1px;
    }

    /* Przycisk akcji */
    .stButton>button {
        background: linear-gradient(135deg, #00d4ff 0%, #0072ff 100%) !important;
        color: white !important;
        border: none !important;
        padding: 12px 30px !important;
        border-radius: 12px !important;
        font-weight: bold !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3) !important;
    }
    
    /* Tabela - tło dopasowane do kart */
    .stDataFrame {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- POŁĄCZENIE Z BAZĄ ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

@st.cache_data(ttl=30)
def fetch_data():
    p = supabase.table("produkty").select("*").execute().data
    k = supabase.table("kategorie").select("*").execute().data
    return pd.DataFrame(p), pd.DataFrame(k)

# --- NAGŁÓWEK ---
st.title("📦 Logistics Command Center")
st.markdown("### Monitorowanie Operacyjne Magazynu")

try:
    df_p, df_k = fetch_data()
    
    if not df_p.empty and not df_k.empty:
        df = df_p.merge(df_k, left_on="kategoria_id", right_on="id", suffixes=('_p', '_k'))
        df['total_val'] = df['cena'] * df['liczba']

        # --- SEKCJA 1: WSKAŹNIKI (W KARTACH) ---
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.metric("Kapitał", f"{df['total_val'].sum():,.0f} PLN")
            st.markdown("</div>", unsafe_allow_html=True)
        with m2:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.metric("Indeksy SKU", len(df))
            st.markdown("</div>", unsafe_allow_html=True)
        with m3:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.metric("Suma sztuk", int(df['liczba'].sum()))
            st.markdown("</div>", unsafe_allow_html=True)
        with m4:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            n_alert = len(df[df['liczba'] < 10])
            st.metric("Alerty", n_alert, delta="Braki" if n_alert > 0 else "OK")
            st.markdown("</div>", unsafe_allow_html=True)

        # --- SEKCJA 2: WYKRESY ---
        col_l, col_r = st.columns([1.6, 1])

        with col_l:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.subheader("📊 Poziomy zapasów")
            fig = px.bar(df, x="nazwa_p", y="liczba", color="nazwa_k",
                         template="plotly_dark", barmode="group",
                         color_discrete_sequence=px.colors.sequential.Cyan_r)
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with col_r:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.subheader("💰 Udział wartości")
            fig2 = px.pie(df, values='total_val', names='nazwa_k', hole=0.6)
            fig2.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', showlegend=False)
            st.plotly_chart(fig2, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # --- SEKCJA 3: PANEL ZARZĄDZANIA ---
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.subheader("⚙️ Zarządzanie Bazą")
        t1, t2, t3 = st.tabs(["📋 Widok Tabeli", "➕ Dodaj Towar", "🗑️ Usuń"])
        
        with t1:
            st.dataframe(df[['id_p', 'nazwa_p', 'liczba', 'cena', 'nazwa_k']], use_container_width=True)
            
        with t2:
            with st.form("add_form"):
                f1, f2, f3 = st.columns(3)
                name = f1.text_input("Nazwa")
                qty = f2.number_input("Ilość", min_value=1)
                price = f3.number_input("Cena", min_value=0.01)
                kat = st.selectbox("Kategoria", df_k['nazwa'].unique())
                if st.form_submit_button("DODAJ PRODUKT"):
                    k_id = int(df_k[df_k['nazwa']==kat]['id'].values[0])
                    supabase.table("produkty").insert({"nazwa":name, "liczba":qty, "cena":price, "kategoria_id":k_id}).execute()
                    st.rerun()
                    
        with t3:
            del_id = st.number_input("ID do usunięcia", step=1)
            if st.button("USUŃ Z BAZY"):
                supabase.table("produkty").delete().eq("id", del_id).execute()
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

except Exception as e:
    st.error(f"Błąd: {e}")
