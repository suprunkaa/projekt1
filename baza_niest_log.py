import streamlit as st
from supabase import create_client, Client
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- KONFIGURACJA UI ---
st.set_page_config(page_title="Logistics Intelligence OS", layout="wide")

# --- CUSTOM CSS: LOGISTYKA & GLASSMORPHISM ---
st.markdown("""
    <style>
    /* Dynamiczne tło logistyczne z nakładką */
    .stApp {
        background: linear-gradient(rgba(15, 23, 42, 0.6), rgba(15, 23, 42, 0.6)), 
                    url("https://images.unsplash.com/photo-1580674285054-bed31e145f59?q=80&w=2070&auto=format&fit=crop");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }

    /* Szklane karty (Glassmorphism) */
    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(15px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 25px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        margin-bottom: 20px;
    }

    /* Stylizacja metryk */
    [data-testid="stMetricValue"] {
        color: #60a5fa !important;
        font-size: 1.8rem !important;
        font-weight: 800 !important;
    }
    
    [data-testid="stMetricLabel"] {
        color: #cbd5e1 !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* Przycisk akcji */
    .stButton>button {
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
        color: white;
        border: none;
        padding: 12px 30px;
        border-radius: 12px;
        font-weight: bold;
        transition: all 0.4s ease;
        width: 100%;
    }
    .stButton>button:hover {
        transform: scale(1.05);
        box-shadow: 0 0 20px rgba(59, 130, 246, 0.5);
    }
    </style>
    """, unsafe_allow_html=True)

# --- POŁĄCZENIE Z BAZĄ ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

@st.cache_data(ttl=30)
def fetch_all_data():
    p = supabase.table("produkty").select("*").execute().data
    k = supabase.table("kategorie").select("*").execute().data
    return pd.DataFrame(p), pd.DataFrame(k)

# --- LAYOUT APLIKACJI ---
st.title("🌐 Logistics Command Center v3.0")
st.markdown("Automatyzacja i Monitoring Zasobów Magazynowych")

try:
    df_p, df_k = fetch_all_data()
    
    if not df_p.empty and not df_k.empty:
        df = df_p.merge(df_k, left_on="kategoria_id", right_on="id", suffixes=('_p', '_k'))
        df['total_val'] = df['cena'] * df['liczba']

        # --- SEKCJA 1: INTELIGENTNE WSKAŹNIKI ---
        m1, m2, m3, m4 = st.columns(4)
        with m1: st.metric("Kapitał w towarze", f"{df['total_val'].sum():,.2f} zł")
        with m2: st.metric("Liczba SKU", len(df))
        with m3: st.metric("Jednostki ogółem", int(df['liczba'].sum()))
        with m4:
            low_stock_count = len(df[df['liczba'] < 10])
            st.metric("Alerty zapasów", low_stock_count, delta="- Krytyczne" if low_stock_count > 0 else "OK")

        st.write("##")

        # --- SEKCJA 2: ANALITYKA PREMIUM ---
        col_left, col_right = st.columns([1.6, 1])

        with col_left:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.subheader("📦 Monitoring Stanów Magazynowych")
            # Wykres z gradientem
            fig = px.area(df.sort_values('liczba', ascending=False), 
                          x="nazwa_p", y="liczba", color="nazwa_k",
                          template="plotly_dark", line_shape="spline")
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                              xaxis_title="", yaxis_title="Ilość (szt)")
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with col_right:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.subheader("💰 Struktura Wartości")
            # Wykres Donut 3D-style
            fig2 = go.Figure(data=[go.Pie(labels=df['nazwa_k'], values=df['total_val'], hole=.5)])
            fig2.update_traces(hoverinfo='label+percent', textinfo='value', 
                               marker=dict(colors=px.colors.sequential.RdBu))
            fig2.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', showlegend=False)
            st.plotly_chart(fig2, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # --- SEKCJA 3: INTERAKTYWNY PANEL ZARZĄDZANIA ---
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        t1, t2, t3 = st.tabs(["📋 Baza Danych", "⚙️ Kontrola Zasobów", "➕ Operacje"])
        
        with t1:
            query = st.text_input("Szukaj produktu lub kategorii...")
            if query:
                df_view = df[df['nazwa_p'].str.contains(query, case=False) | df['nazwa_k'].str.contains(query, case=False)]
            else:
                df_view = df
            st.dataframe(df_view[['id_p', 'nazwa_p', 'liczba', 'cena', 'nazwa_k', 'total_val']], 
                         use_container_width=True, hide_index=True)
            
        with t2:
            st.write("### Szybka Edycja / Usuwanie")
            c_del1, c_del2 = st.columns(2)
            del_id = c_del1.number_input("Wpisz ID produktu do usunięcia", step=1)
            if c_del1.button("USUŃ DEFINITYWNIE"):
                supabase.table("produkty").delete().eq("id", del_id).execute()
                st.success("Rekord został usunięty z serwera.")
                st.rerun()
            
            c_del2.info("Wskazówka: ID produktu znajdziesz w zakładce Baza Danych.")

        with t3:
            st.write("### Dodaj Nowe Zasoby")
            ca, cb = st.columns(2)
            with ca:
                with st.form("add_p"):
                    st.write("**Nowy Produkt**")
                    p_name = st.text_input("Nazwa przedmiotu")
                    p_qty = st.number_input("Ilość", min_value=0)
                    p_price = st.number_input("Cena jedn.", min_value=0.0)
                    p_kat = st.selectbox("Kategoria", df_k['nazwa'].unique())
                    if st.form_submit_button("DODAJ PRODUKT"):
                        k_id = int(df_k[df_k['nazwa']==p_kat]['id'].values[0])
                        supabase.table("produkty").insert({"nazwa":p_name, "liczba":p_qty, "cena":p_price, "kategoria_id":k_id}).execute()
                        st.rerun()
            with cb:
                with st.form("add_k"):
                    st.write("**Nowa Kategoria**")
                    k_name = st.text_input("Nazwa kategorii")
                    if st.form_submit_button("DODAJ KATEGORIĘ"):
                        supabase.table("kategorie").insert({"nazwa":k_name}).execute()
                        st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

except Exception as e:
    st.error(f"⚠️ Błąd krytyczny połączenia: {e}")
