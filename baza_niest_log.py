import streamlit as st
from supabase import create_client, Client
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import segno
import io

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Smart Logistics OS", layout="wide")

# --- CUSTOM CSS: PREMIUM DARK & LOGISTICS ---
st.markdown("""
    <style>
    /* Tło z dynamicznym gradientem i obrazem logistycznym */
    .stApp {
        background: linear-gradient(rgba(10, 20, 30, 0.8), rgba(10, 20, 30, 0.9)), 
                    url("https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?q=80&w=2070&auto=format&fit=crop");
        background-size: cover;
        background-attachment: fixed;
    }
    
    /* Szklane panele (Glassmorphism) */
    .glass-card {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 20px;
    }

    /* Neonowe metryki */
    [data-testid="stMetricValue"] {
        color: #3b82f6 !important;
        text-shadow: 0 0 10px rgba(59, 130, 246, 0.5);
    }
    
    /* Stylizacja przycisków */
    .stButton>button {
        background: linear-gradient(135deg, #2563eb, #7c3aed) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        transition: 0.3s !important;
    }
    .stButton>button:hover {
        transform: scale(1.02) !important;
        box-shadow: 0 0 15px rgba(124, 58, 237, 0.4) !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- POŁĄCZENIE Z SUPABASE ---
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# --- POBIERANIE DANYCH ---
def get_full_data():
    p = supabase.table("produkty").select("*").execute().data
    k = supabase.table("kategorie").select("*").execute().data
    df_p = pd.DataFrame(p)
    df_k = pd.DataFrame(k)
    if not df_p.empty and not df_k.empty:
        return df_p.merge(df_k, left_on="kategoria_id", right_on="id", suffixes=('_prod', '_kat'))
    return pd.DataFrame()

# --- GŁÓWNY PANEL ---
st.title("🛰️ Logistics Command Center")
st.caption("System v3.5 | Integrated QR & Analytics")

# Pobierz dane
df = get_full_data()

if not df.empty:
    df['total_val'] = df['cena'] * df['liczba']

    # --- SEKCJA 1: STATYSTYKI (KPI) ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Wycena Magazynu", f"{df['total_val'].sum():,.2f} zł")
    c2.metric("Liczba SKU", len(df))
    c3.metric("Suma Jednostek", int(df['liczba'].sum()))
    
    low_stock = df[df['liczba'] < 5]
    c4.metric("Alerty Braków", len(low_stock), delta="- Uzupełnij!" if len(low_stock) > 0 else "OK", delta_color="inverse")

    st.write("---")

    # --- SEKCJA 2: WYKRESY INTERAKTYWNE ---
    col_l, col_r = st.columns([1.5, 1])
    
    with col_l:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.subheader("📊 Poziom zapasów (szt.)")
        fig = px.bar(df, x="nazwa_prod", y="liczba", color="nazwa_kat", 
                     template="plotly_dark", barmode="group",
                     color_discrete_sequence=px.colors.qualitative.Pastel)
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_r:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.subheader("🥧 Struktura wartości")
        fig2 = px.pie(df, values='total_val', names='nazwa_kat', hole=0.4, template="plotly_dark")
        fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # --- SEKCJA 3: PANEL OPERACYJNY ---
    tabs = st.tabs(["🔍 Inwentarz", "📱 Generator Kodów QR", "➕ Dodaj/Edytuj", "🗑️ Usuwanie"])

    with tabs[0]:
        st.dataframe(df[['id_prod', 'nazwa_prod', 'liczba', 'cena', 'nazwa_kat', 'total_val']], use_container_width=True)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Pobierz Pełny Raport CSV", csv, "magazyn_raport.csv", "text/csv")

    with tabs[1]:
        st.subheader("Generator Etykiet")
        selected_prod = st.selectbox("Wybierz produkt", df['nazwa_prod'].unique())
        prod_data = df[df['nazwa_prod'] == selected_prod].iloc[0]
        
        # Generowanie QR używając biblioteki Segno
        qr = segno.make(f"PROD_ID:{prod_data['id_prod']} | {prod_data['nazwa_prod']}")
        buffer = io.BytesIO()
        qr.save(buffer, kind='png', scale=10)
        
        col_q1, col_q2 = st.columns([1, 2])
        col_q1.image(buffer.getvalue(), width=200, caption=f"QR: {selected_prod}")
        col_q2.info(f"**Informacje zakodowane:**\n\nNazwa: {prod_data['nazwa_prod']}\nKategoria: {prod_data['nazwa_kat']}\nID Bazy: {prod_data['id_prod']}")
        col_q2.download_button("Pobierz PNG do druku", buffer.getvalue(), f"QR_{selected_prod}.png")

    with tabs[2]:
        ca, cb = st.columns(2)
        with ca:
            with st.form("new_product"):
                st.write("### Nowy Produkt")
                n = st.text_input("Nazwa")
                l = st.number_input("Ilość", min_value=0)
                c = st.number_input("Cena", min_value=0.0)
                k_names = df['nazwa_kat'].unique()
                k = st.selectbox("Kategoria", k_names)
                if st.form_submit_button("Zatwierdź"):
                    k_id = int(df[df['nazwa_kat'] == k]['id_kat'].values[0])
                    supabase.table("produkty").insert({"nazwa": n, "liczba": l, "cena": c, "kategoria_id": k_id}).execute()
                    st.rerun()
        with cb:
            with st.form("new_category"):
                st.write("### Nowa Kategoria")
                kn = st.text_input("Nazwa")
                if st.form_submit_button("Dodaj"):
                    supabase.table("kategorie").insert({"nazwa": kn}).execute()
                    st.rerun()

    with tabs[3]:
        st.warning("Uwaga: Usunięcie produktu jest nieodwracalne.")
        del_id = st.number_input("ID produktu do usunięcia", step=1)
        if st.button("🔴 POTWIERDŹ USUNIĘCIE"):
            supabase.table("produkty").delete().eq("id", del_id).execute()
            st.success(f"Usunięto produkt o ID {del_id}")
            st.rerun()

else:
    st.info("Baza danych jest pusta. Dodaj pierwszą kategorię i produkt w zakładce Dodaj/Edytuj.")
    # Uproszczony formularz dla pustej bazy
    if st.button("Zainicjuj bazę (Dodaj kategorię Ogólne)"):
        supabase.table("kategorie").insert({"nazwa": "Ogólne"}).execute()
        st.rerun()
