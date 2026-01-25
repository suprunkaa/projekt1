import streamlit as st
from supabase import create_client, Client
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- KONFIGURACJA UI ---
st.set_page_config(page_title="Logistics Command Center", layout="wide")

# --- CUSTOM CSS: CRYSTAL CLEAR DESIGN ---
st.markdown("""
    <style>
    /* Nowoczesne, jasne tło z delikatnym gradientem */
    .stApp {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        background-attachment: fixed;
    }

    /* Karty typu "White Glass" - wyraźne i jasne */
    .glass-card {
        background: rgba(255, 255, 255, 0.8);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 1);
        border-radius: 20px;
        padding: 25px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.05);
        margin-bottom: 20px;
        color: #1e293b;
    }

    /* Nagłówki */
    h1, h2, h3 {
        color: #0f172a !important;
        font-weight: 700 !important;
    }

    /* Metryki - wyraźne kolory na jasnym tle */
    [data-testid="stMetricValue"] {
        color: #2563eb !important;
        font-weight: 800 !important;
    }
    
    [data-testid="stMetricLabel"] {
        color: #64748b !important;
        font-size: 0.9rem !important;
    }

    /* Przyciski - żywe kolory */
    .stButton>button {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 10px 24px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
    }

    /* Stylizacja zakładek (Tabs) */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border-radius: 8px;
        padding: 10px 20px;
        color: #64748b;
    }
    .stTabs [aria-selected="true"] {
        background-color: white !important;
        color: #2563eb !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
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

# --- UKŁAD STRONY ---
col_title, col_status = st.columns([3, 1])
with col_title:
    st.title("🌐 Logistics Command Center")
    st.markdown("<p style='color: #64748b; font-size: 1.1rem;'>Zarządzanie operacyjne i monitoring zasobów</p>", unsafe_allow_html=True)

try:
    df_p, df_k = fetch_all_data()
    
    if not df_p.empty and not df_k.empty:
        df = df_p.merge(df_k, left_on="kategoria_id", right_on="id", suffixes=('_p', '_k'))
        df['total_val'] = df['cena'] * df['liczba']

        # --- SEKCJA 1: KPI ---
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Wartość towaru", f"{df['total_val'].sum():,.2f} zł")
        m2.metric("Liczba SKU", len(df))
        m3.metric("Wszystkie jednostki", int(df['liczba'].sum()))
        
        low_stock = len(df[df['liczba'] < 10])
        m4.metric("Alerty zapasów", low_stock, delta=f"{low_stock} krytycznych" if low_stock > 0 else "W normie", delta_color="inverse")
        st.markdown("</div>", unsafe_allow_html=True)

        # --- SEKCJA 2: ANALITYKA ---
        c_left, c_right = st.columns([1.6, 1])

        with c_left:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.subheader("📦 Stan magazynowy")
            fig = px.bar(df.sort_values('liczba', ascending=False), 
                         x="nazwa_p", y="liczba", color="nazwa_k",
                         template="plotly_white", # Zmiana na jasny motyw
                         color_discrete_sequence=px.colors.qualitative.Safe)
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', 
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color="#1e293b")
            )
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with c_right:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.subheader("💰 Struktura finansowa")
            fig2 = px.pie(df, values='total_val', names='nazwa_k', hole=0.5,
                          color_discrete_sequence=px.colors.qualitative.Pastel)
            fig2.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', 
                font=dict(color="#1e293b"),
                legend=dict(orientation="h", yanchor="bottom", y=-0.2)
            )
            st.plotly_chart(fig2, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # --- SEKCJA 3: MANAGEMENT ---
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.subheader("🛠️ Panel zarządzania")
        
        t1, t2, t3 = st.tabs(["📋 Lista towarów", "⚙️ Kontrola ID", "➕ Nowa dostawa"])
        
        with t1:
            query = st.text_input("Szukaj (nazwa produktu lub kategorii)...")
            df_view = df[df['nazwa_p'].str.contains(query, case=False) | df['nazwa_k'].str.contains(query, case=False)] if query else df
            st.dataframe(df_view[['id_p', 'nazwa_p', 'liczba', 'cena', 'nazwa_k', 'total_val']], 
                         use_container_width=True)
            
        with t2:
            st.write("### Usuwanie i korekta")
            col_del1, col_del2 = st.columns(2)
            del_id = col_del1.number_input("Wpisz ID produktu", step=1, value=0)
            if col_del1.button("USUŃ PRODUKT"):
                if del_id > 0:
                    supabase.table("produkty").delete().eq("id", del_id).execute()
                    st.success(f"Produkt {del_id} usunięty.")
                    st.rerun()
            col_del2.info("Skorzystaj z zakładki 'Lista towarów', aby sprawdzić poprawne ID.")

        with t3:
            st.write("### Przyjęcie towaru")
            with st.form("add_new"):
                f1, f2, f3 = st.columns(3)
                name = f1.text_input("Nazwa przedmiotu")
                qty = f2.number_input("Ilość", min_value=1)
                price = f3.number_input("Cena (PLN)", min_value=0.01)
                kat = st.selectbox("Wybierz kategorię", df_k['nazwa'].unique())
                
                if st.form_submit_button("DODAJ DO BAZY"):
                    k_id = int(df_k[df_k['nazwa']==kat]['id'].values[0])
                    supabase.table("produkty").insert({"nazwa":name, "liczba":qty, "cena":price, "kategoria_id":k_id}).execute()
                    st.success("Dodano pomyślnie!")
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

except Exception as e:
    st.error(f"⚠️ Problem z połączeniem: {e}")
