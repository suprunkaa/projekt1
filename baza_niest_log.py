import streamlit as st
from supabase import create_client, Client
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Magazyn Inteligentny v2", layout="wide")

# --- CUSTOM CSS (USUNIĘCIE BIAŁEJ POŚWIATY I TRYB DARK) ---
st.markdown("""
    <style>
    /* Usunięcie białego tła i ustawienie głębokiej ciemności */
    .stApp {
        background: linear-gradient(rgba(0, 0, 0, 0.85), rgba(0, 0, 0, 0.95)), 
                    url("https://images.unsplash.com/photo-1553413077-190dd305871c?q=80&w=2000&auto=format&fit=crop");
        background-size: cover;
        background-attachment: fixed;
    }
    
    /* Naprawa kolorów tekstu */
    h1, h2, h3, p, span, label, .stMarkdown {
        color: #e2e8f0 !important;
    }

    /* Stylizacja kart z efektem neonu */
    .metric-box {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid #3b82f6;
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 0 15px rgba(59, 130, 246, 0.2);
    }

    /* Stylizacja tabeli (usuwanie białych elementów) */
    .stDataFrame {
        background: rgba(15, 23, 42, 0.8) !important;
        border-radius: 10px;
    }

    /* Przyciski */
    div.stButton > button {
        background: linear-gradient(45deg, #2563eb, #7c3aed);
        color: white;
        border: none;
        font-weight: bold;
        padding: 10px 24px;
        border-radius: 10px;
        transition: 0.3s;
    }
    
    div.stButton > button:hover {
        box-shadow: 0 0 20px rgba(124, 58, 237, 0.6);
        transform: scale(1.02);
    }
    </style>
    """, unsafe_allow_html=True)

# --- INICJALIZACJA SUPABASE ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- FUNKCJE DANYCH ---
@st.cache_data(ttl=60)
def load_data():
    p = supabase.table("produkty").select("*").execute().data
    k = supabase.table("kategorie").select("*").execute().data
    return pd.DataFrame(p), pd.DataFrame(k)

# --- GŁÓWNY PANEL ---
st.title("🌌 Magazyn Command Center")
st.markdown("Zarządzanie zasobami w czasie rzeczywistym")

try:
    df_p, df_k = load_data()
    
    if not df_p.empty and not df_k.empty:
        # Przetwarzanie danych
        df = df_p.merge(df_k, left_on="kategoria_id", right_on="id", suffixes=('_prod', '_kat'))
        df['wartosc'] = df['cena'] * df['liczba']

        # --- SEKCJA 1: WIZUALNE KPI ---
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"<div class='metric-box'><small>WARTOŚĆ TOTAL</small><h2>{df['wartosc'].sum():,.2f} zł</h2></div>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<div class='metric-box'><small>ASORTYMENT</small><h2>{len(df)} poz.</h2></div>", unsafe_allow_html=True)
        with col3:
            st.markdown(f"<div class='metric-box'><small>NAJDROŻSZY</small><h2>{df['cena'].max():,.2f} zł</h2></div>", unsafe_allow_html=True)
        with col4:
            st.markdown(f"<div class='metric-box'><small>BRAKI (0 szt.)</small><h2 style='color:#f87171;'>{len(df[df['liczba']==0])}</h2></div>", unsafe_allow_html=True)

        st.write("---")

        # --- SEKCJA 2: MODERNE WYKRESY (PLOTLY) ---
        c1, c2 = st.columns([1.5, 1])
        
        with c1:
            st.subheader("📊 Dostępność towarów")
            fig = px.bar(df, x="nazwa_prod", y="liczba", color="liczba",
                         color_continuous_scale="Viridis",
                         template="plotly_dark")
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            st.subheader("💎 Udział w kapitale")
            fig2 = px.pie(df, values='wartosc', names='nazwa_kat', hole=0.6,
                          color_discrete_sequence=px.colors.sequential.Electric)
            fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', showlegend=True)
            st.plotly_chart(fig2, use_container_width=True)

        # --- SEKCJA 3: SMART MANAGEMENT ---
        st.subheader("🛠️ Operacje i Rejestr")
        
        tab_list, tab_add, tab_warn = st.tabs(["📋 Rejestr", "➕ Nowy wpis", "⚠️ Alerty"])
        
        with tab_list:
            search = st.text_input("🔍 Wyszukaj produkt...")
            filtred = df[df['nazwa_prod'].str.contains(search, case=False)] if search else df
            st.dataframe(filtred[['id_prod', 'nazwa_prod', 'liczba', 'cena', 'nazwa_kat', 'wartosc']], use_container_width=True)
            
            # Nowa funkcja: Eksport
            st.download_button("Pobierz raport PDF/CSV", data=filtred.to_csv(), file_name="magazyn.csv")

        with tab_add:
            ca, cb = st.columns(2)
            with ca:
                with st.form("p_f"):
                    st.write("**Dodaj Produkt**")
                    n = st.text_input("Nazwa")
                    l = st.number_input("Ilość", min_value=0)
                    c = st.number_input("Cena", min_value=0.0)
                    k = st.selectbox("Kategoria", df_k['nazwa'].unique())
                    if st.form_submit_button("Zatwierdź"):
                        kid = int(df_k[df_k['nazwa']==k]['id'].values[0])
                        supabase.table("produkty").insert({"nazwa":n, "liczba":l, "cena":c, "kategoria_id":kid}).execute()
                        st.rerun()
            with cb:
                with st.form("k_f"):
                    st.write("**Nowa Kategoria**")
                    kn = st.text_input("Nazwa")
                    ko = st.text_input("Opis")
                    if st.form_submit_button("Stwórz"):
                        supabase.table("kategorie").insert({"nazwa":kn, "opis":ko}).execute()
                        st.rerun()

        with tab_warn:
            st.write("### 🚨 Produkty na wyczerpaniu (poniżej 5 sztuk)")
            low_stock = df[df['liczba'] < 5]
            if not low_stock.empty:
                st.error("Wykryto braki!")
                st.table(low_stock[['nazwa_prod', 'liczba', 'nazwa_kat']])
            else:
                st.success("Wszystkie stany magazynowe w normie.")

except Exception as e:
    st.error(f"Skonfiguruj połączenie z bazą Supabase: {e}")
