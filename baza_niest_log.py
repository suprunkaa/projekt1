import streamlit as st
from supabase import create_client, Client
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- KONFIGURACJA UI ---
st.set_page_config(page_title="Magazyn Pro | Command Center", layout="wide", initial_sidebar_state="collapsed")

# --- CUSTOM CSS: NOWOCZESNY DESIGN ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');

    html, body, [data-testid="stsidebar"] {
        font-family: 'Inter', sans-serif;
    }

    /* Tło z efektem głębi */
    .stApp {
        background: radial-gradient(circle at top right, rgba(29, 78, 216, 0.15), transparent),
                    linear-gradient(rgba(15, 23, 42, 0.85), rgba(15, 23, 42, 0.95)), 
                    url("https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?q=80&w=2070&auto=format&fit=crop");
        background-size: cover;
        background-attachment: fixed;
    }

    /* Nowoczesne karty szklane */
    .glass-card {
        background: rgba(30, 41, 59, 0.5);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 24px;
        padding: 2rem;
        box-shadow: 0 20px 50px rgba(0, 0, 0, 0.3);
        margin-bottom: 25px;
        transition: transform 0.3s ease;
    }

    /* Efekt po najechaniu na kartę */
    .glass-card:hover {
        border: 1px solid rgba(59, 130, 246, 0.5);
    }

    /* Stylizacja metryk (KPI) */
    [data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.03);
        border-radius: 16px;
        padding: 15px !important;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }

    [data-testid="stMetricValue"] {
        color: #38bdf8 !important; /* Cyjanowy błękit */
        font-weight: 800 !important;
        letter-spacing: -1px;
    }

    /* Przycisk akcji - Gradientowy */
    .stButton>button {
        background: linear-gradient(135deg, #0ea5e9 0%, #2563eb 100%) !important;
        color: white !important;
        border: none !important;
        padding: 0.75rem 2rem !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 25px rgba(37, 99, 235, 0.4);
    }

    /* Stylizacja Tabel */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
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

# --- NAGŁÓWEK ---
col_head1, col_head2 = st.columns([3, 1])
with col_head1:
    st.title("🛰️ Magazyn Command Center")
    st.caption("v3.5 Platinum Edition | System Monitorowania Operacyjnego")

# --- LOGIKA DANYCH ---
try:
    df_p, df_k = fetch_all_data()
    
    if not df_p.empty and not df_k.empty:
        df = df_p.merge(df_k, left_on="kategoria_id", right_on="id", suffixes=('_p', '_k'))
        df['total_val'] = df['cena'] * df['liczba']

        # --- SEKCJA 1: KPI (Metric Cards) ---
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Wartość Aktywów", f"{df['total_val'].sum():,.2f} zł")
        m2.metric("Unikalne SKU", len(df))
        m3.metric("Sztuki w Magazynie", int(df['liczba'].sum()))
        
        low_stock = len(df[df['liczba'] < 10])
        status_color = "normal" if low_stock == 0 else "inverse"
        m4.metric("Alerty Zapasu", low_stock, delta=f"{low_stock} SKU Low", delta_color=status_color)

        st.markdown("---")

        # --- SEKCJA 2: ANALITYKA WIZUALNA ---
        col_l, col_r = st.columns([1.6, 1])

        with col_l:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.subheader("📈 Przepływ Towarowy (SKU/Ilość)")
            
            # Nowoczesny wykres z linią trendu (Spline)
            fig = px.area(df.sort_values('liczba', ascending=False), 
                          x="nazwa_p", y="liczba", color="nazwa_k",
                          template="plotly_dark", line_shape="spline",
                          color_discrete_sequence=px.colors.sequential.Electric)
            
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', 
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis={'showgrid': False},
                yaxis={'showgrid': True, 'gridcolor': 'rgba(255,255,255,0.05)'},
                margin=dict(l=0, r=0, t=20, b=0)
            )
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with col_r:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.subheader("💎 Podział Wartościowy")
            
            # Wykres Donut "Glow"
            fig2 = go.Figure(data=[go.Pie(labels=df['nazwa_k'], values=df['total_val'], hole=.6)])
            fig2.update_traces(
                hoverinfo='label+percent', 
                textinfo='none',
                marker=dict(colors=px.colors.sequential.Icefire_r, line=dict(color='rgba(0,0,0,0)', width=2))
            )
            fig2.update_layout(
                template="plotly_dark", 
                paper_bgcolor='rgba(0,0,0,0)', 
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig2, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # --- SEKCJA 3: PANEL OPERACYJNY ---
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.subheader("🛠️ Zarządzanie Zasobami")
        
        t1, t2, t3 = st.tabs(["📋 Rejestr Systemowy", "⚙️ Modyfikacja", "➕ Nowa Dostawa"])
        
        with t1:
            search_col, filter_col = st.columns([2, 1])
            query = search_col.text_input("🔍 Szybkie szukanie (Nazwa/Kategoria)...")
            
            if query:
                df_view = df[df['nazwa_p'].str.contains(query, case=False) | df['nazwa_k'].str.contains(query, case=False)]
            else:
                df_view = df
            
            st.dataframe(df_view[['id_p', 'nazwa_p', 'liczba', 'cena', 'nazwa_k', 'total_val']], 
                         use_container_width=True, hide_index=True)
            
        with t2:
            st.write("### Tryb Administracyjny")
            c_ed1, c_ed2 = st.columns(2)
            del_id = c_ed1.number_input("Wpisz ID produktu do usunięcia", step=1, min_value=1)
            
            if c_ed1.button("🔥 USUŃ PERMANENTNIE"):
                with st.spinner("Usuwanie..."):
                    supabase.table("produkty").delete().eq("id", del_id).execute()
                    st.toast(f"Usunięto rekord {del_id}", icon="✅")
                    st.rerun()
            
            c_ed2.info("Pamiętaj: Operacji usunięcia nie można cofnąć. Sprawdź dwukrotnie ID w tabeli obok.")

        with t3:
            st.write("### Formularz Przyjęcia Towaru")
            with st.form("main_form", clear_on_submit=True):
                c_f1, c_f2, c_f3 = st.columns(3)
                p_name = c_f1.text_input("Nazwa Produktu")
                p_qty = c_f2.number_input("Ilość", min_value=1)
                p_price = c_f3.number_input("Cena Netto", min_value=0.01)
                
                p_kat = st.selectbox("Wybierz Kategorę Magazynową", df_k['nazwa'].unique())
                
                if st.form_submit_button("✅ DODAJ DO SYSTEMU"):
                    k_id = int(df_k[df_k['nazwa'] == p_kat]['id'].values[0])
                    supabase.table("produkty").insert({
                        "nazwa": p_name, "liczba": p_qty, "cena": p_price, "kategoria_id": k_id
                    }).execute()
                    st.toast("Produkt dodany pomyślnie!", icon="🚀")
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    else:
        st.warning("Baza danych jest pusta. Dodaj pierwszą kategorię, aby rozpocząć.")

except Exception as e:
    st.error(f"🛰️ Utrata sygnału z bazą: {e}")
