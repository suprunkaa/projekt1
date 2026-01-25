import streamlit as st
from supabase import create_client, Client
import pandas as pd
import plotly.express as px
import segno
import io

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Logistic Intelligence OS", layout="wide")

# --- DESIGN: DARK GLASSMORPHISM ---
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(rgba(0, 0, 0, 0.8), rgba(0, 10, 30, 0.9)), 
                    url("https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?q=80&w=2070");
        background-size: cover;
        background-attachment: fixed;
    }
    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(15px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 25px;
        margin-bottom: 20px;
    }
    h1, h2, h3 { color: #60a5fa !important; text-shadow: 0 0 10px rgba(96, 165, 250, 0.3); }
    .stMetric { background: rgba(0,0,0,0.4); border-radius: 15px; padding: 15px; border: 1px solid #1e293b; }
    </style>
    """, unsafe_allow_html=True)

# --- POŁĄCZENIE Z BAZĄ ---
# Dane pobierane z ustawień Streamlit Cloud (Secrets)
@st.cache_resource
def init_db():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_db()

def fetch_data():
    # Pobieramy dane z Twoich tabel: produkty i kategorie
    p = supabase.table("produkty").select("*").execute().data
    k = supabase.table("kategorie").select("*").execute().data
    df_p = pd.DataFrame(p)
    df_k = pd.DataFrame(k)
    if not df_p.empty and not df_k.empty:
        # Łączymy po ID kategorii zgodnie z Twoim schematem
        return df_p.merge(df_k, left_on="kategoria_id", right_on="id", suffixes=('_prod', '_kat'))
    return pd.DataFrame()

# --- INTERFEJS GŁÓWNY ---
st.title("🛰️ Command Center: Logistyka")
df = fetch_data()

if not df.empty:
    df['wartosc_magazynu'] = df['cena'] * df['liczba']
    
    # --- KPI (Statystyki) ---
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Wartość Towaru", f"{df['wartosc_magazynu'].sum():,.2f} zł")
    with c2: st.metric("Produkty (SKU)", len(df))
    with c3: st.metric("Suma Sztuk", int(df['liczba'].sum()))
    with c4:
        braki = len(df[df['liczba'] < 5])
        st.metric("Alerty", braki, delta="- Uzupelnij" if braki > 0 else "OK", delta_color="inverse")

    st.write("##")

    # --- ANALITYKA (Wykresy) ---
    col_l, col_r = st.columns([1.5, 1])
    
    with col_l:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.subheader("📊 Stan Zapasu per Produkt")
        fig = px.bar(df, x="nazwa_prod", y="liczba", color="nazwa_kat", 
                     template="plotly_dark", color_discrete_sequence=px.colors.qualitative.Bold)
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_r:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.subheader("🥧 Udział Kategorii")
        fig2 = px.pie(df, values='wartosc_magazynu', names='nazwa_kat', hole=0.5, template="plotly_dark")
        fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig2, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # --- OPERACJE (Tabs) ---
    t_data, t_qr, t_add, t_del = st.tabs(["📋 Rejestr", "📱 Kody QR", "➕ Dodaj", "🗑️ Usuń"])

    with t_data:
        st.dataframe(df[['id_prod', 'nazwa_prod', 'liczba', 'cena', 'nazwa_kat']], use_container_width=True)

    with t_qr:
        st.subheader("Generowanie Etykiet")
        wybor = st.selectbox("Wybierz produkt do etykiety", df['nazwa_prod'].unique())
        p_data = df[df['nazwa_prod'] == wybor].iloc[0]
        
        # QR Code z Segno
        qr = segno.make(f"ID:{p_data['id_prod']} | {p_data['nazwa_prod']}")
        out = io.BytesIO()
        qr.save(out, kind='png', scale=10)
        st.image(out.getvalue(), width=200, caption=f"QR dla {wybor}")

    with t_add:
        c_a, c_b = st.columns(2)
        with c_a:
            with st.form("add_p"):
                st.write("### Dodaj Produkt")
                n = st.text_input("Nazwa produktu")
                l = st.number_input("Ilość", min_value=0)
                c = st.number_input("Cena", min_value=0.0)
                k = st.selectbox("Kategoria", df['nazwa_kat'].unique())
                if st.form_submit_button("Zapisz Produkt"):
                    k_id = int(df[df['nazwa_kat'] == k]['id_kat'].values[0])
                    supabase.table("produkty").insert({"nazwa":n, "liczba":l, "cena":c, "kategoria_id":k_id}).execute()
                    st.rerun()
        with c_b:
            with st.form("add_k"):
                st.write("### Nowa Kategoria")
                kn = st.text_input("Nazwa nowej kategorii")
                if st.form_submit_button("Utwórz"):
                    supabase.table("kategorie").insert({"nazwa":kn}).execute()
                    st.rerun()

    with t_del:
        st.warning("Usuwanie danych z bazy")
        target_id = st.number_input("Wpisz ID do usunięcia", step=1)
        if st.button("🔴 POTWIERDŹ USUNIĘCIE"):
            supabase.table("produkty").delete().eq("id", target_id).execute()
            st.success("Produkt usunięty!")
            st.rerun()

else:
    st.info("Baza danych jest pusta lub brak połączenia.")
