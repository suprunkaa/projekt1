import streamlit as st
from supabase import create_client, Client
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# --- KONFIGURACJA UI ---
st.set_page_config(page_title="Logistics Command Center PRO", layout="wide")

# --- CUSTOM CSS: NATURALNE TŁO + MAKSYMALNA CZYTELNOŚĆ ---
st.markdown("""
    <style>
    .stApp {
        background: url("https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?q=80&w=2070&auto=format&fit=crop");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }
    .glass-card {
        background: rgba(15, 23, 42, 0.65);
        backdrop-filter: blur(20px) saturate(160%);
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 20px;
        padding: 25px;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.5);
        margin-bottom: 20px;
    }
    h1, h2, h3, p, span, label {
        color: #ffffff !important;
        text-shadow: 2px 2px 6px rgba(0, 0, 0, 0.9) !important;
        font-weight: 600 !important;
    }
    [data-testid="stMetricValue"] {
        color: #00e5ff !important;
        font-size: 2rem !important;
        font-weight: 800 !important;
    }
    .stButton>button {
        background: linear-gradient(135deg, #00d4ff 0%, #0072ff 100%) !important;
        color: white !important;
        font-weight: bold !important;
        border-radius: 10px !important;
    }
    /* Styl dla tabeli */
    .stDataFrame { background: rgba(255, 255, 255, 0.05); border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- POŁĄCZENIE Z BAZĄ ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

@st.cache_data(ttl=20)
def fetch_data():
    p = supabase.table("produkty").select("*").execute().data
    k = supabase.table("kategorie").select("*").execute().data
    return pd.DataFrame(p), pd.DataFrame(k)

# --- LOGIKA APLIKACJI ---
st.title("🛰️ Logistics Intelligence OS")

try:
    df_p, df_k = fetch_data()
    
    if not df_p.empty and not df_k.empty:
        df = df_p.merge(df_k, left_on="kategoria_id", right_on="id", suffixes=('_p', '_k'))
        df['wartosc'] = df['cena'] * df['liczba']

        # --- SEKCJA 1: RAPORTY I EXPORT ---
        with st.sidebar:
            st.markdown("### 📊 Centrum Raportów")
            csv = df[['nazwa_p', 'liczba', 'cena', 'nazwa_k', 'wartosc']].to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 Pobierz Raport Stanu (CSV)",
                data=csv,
                file_name=f"raport_magazyn_{datetime.now().strftime('%Y%m%d')}.csv",
                mime='text/csv',
            )
            st.info("Raport zawiera aktualne stany magazynowe i wycenę.")

        # --- SEKCJA 2: KPI ---
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.metric("Suma Aktywów", f"{df['wartosc'].sum():,.2f} zł")
            st.markdown("</div>", unsafe_allow_html=True)
        with c2:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.metric("Asortyment (SKU)", len(df))
            st.markdown("</div>", unsafe_allow_html=True)
        with c3:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.metric("Stan Całkowity", int(df['liczba'].sum()))
            st.markdown("</div>", unsafe_allow_html=True)
        with c4:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            low = len(df[df['liczba'] < 10])
            st.metric("Do uzupełnienia", low, delta="- Braki" if low > 0 else "OK")
            st.markdown("</div>", unsafe_allow_html=True)

        # --- SEKCJA 3: PANEL ZARZĄDZANIA ---
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        tab1, tab2, tab3, tab4 = st.tabs(["📋 Rejestr", "🚛 Planowanie Dostaw", "➕ Nowa Dostawa", "🗑️ Usuń"])
        
        with tab1:
            st.subheader("Aktualny inwentarz")
            st.dataframe(df[['id_p', 'nazwa_p', 'liczba', 'cena', 'nazwa_k', 'wartosc']], use_container_width=True)
            
        with tab2:
            st.subheader("Harmonogram nadchodzących dostaw")
            # Prosta tabela do wizualizacji dostaw (możesz ją potem połączyć z bazą Supabase)
            dostawy_mock = pd.DataFrame({
                "Data": ["2024-05-20", "2024-05-22"],
                "Dostawca": ["Dachser", "DHL Freight"],
                "Status": ["W drodze", "Zaplanowano"],
                "Towar": ["Elektronika", "Palety drewniane"]
            })
            st.table(dostawy_mock)
            st.info("Funkcja planowania pozwala uniknąć zatorów na rampie rozładunkowej.")

        with tab3:
            with st.form("new_delivery"):
                st.write("### Przyjęcie nowego towaru")
                f1, f2, f3 = st.columns(3)
                n = f1.text_input("Nazwa produktu")
                l = f2.number_input("Ilość (szt/kg)", min_value=1)
                c = f3.number_input("Cena zakupu netto", min_value=0.01)
                k = st.selectbox("Kategoria systemowa", df_k['nazwa'].unique())
                if st.form_submit_button("✅ POTWIERDŹ PRZYJĘCIE"):
                    kid = int(df_k[df_k['nazwa']==k]['id'].values[0])
                    supabase.table("produkty").insert({"nazwa":n, "liczba":l, "cena":c, "kategoria_id":kid}).execute()
                    st.success(f"Dodano: {n}")
                    st.rerun()

        with tab4:
            st.subheader("Usuwanie rekordów")
            del_id = st.number_input("Podaj ID do trwałego usunięcia", step=1, value=0)
            if st.button("🔴 USUŃ Z BAZY"):
                supabase.table("produkty").delete().eq("id", del_id).execute()
                st.warning(f"Usunięto produkt o ID {del_id}")
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        # --- SEKCJA 4: ANALITYKA ---
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.subheader("📈 Analiza trendów magazynowych")
        fig = px.area(df, x="nazwa_p", y="liczba", color="nazwa_k", template="plotly_dark", line_shape="spline")
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

except Exception as e:
    st.error(f"⚠️ Problem z systemem: {e}")
