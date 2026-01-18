import streamlit as st
from supabase import create_client, Client
import pandas as pd

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Magazyn Pro Dashboard", layout="wide")

# --- DODANIE TŁA I STYLIZACJA CSS ---
def add_bg_and_style():
    st.markdown(
        f"""
        <style>
        .stApp {{
            background: linear-gradient(rgba(255, 255, 255, 0.8), rgba(255, 255, 255, 0.8)), 
                        url("https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?q=80&w=2070&auto=format&fit=crop");
            background-size: cover;
        }}
        .main-card {{
            background-color: rgba(255, 255, 255, 0.9);
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
        }}
        h1, h2, h3 {{
            color: #1E3A8A;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

add_bg_and_style()

# --- POŁĄCZENIE Z SUPABASE ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- FUNKCJE POMOCNICZE ---
def get_data(table): return supabase.table(table).select("*").execute().data

# --- NAGŁÓWEK ---
st.title("📦 System Zarządzania Magazynem")
st.markdown("---")

# --- GŁÓWNY PANEL (DASHBOARD) ---
# Pobieranie danych na start
produkty_raw = get_data("produkty")
kategorie_raw = get_data("kategorie")

if produkty_raw and kategorie_raw:
    df_p = pd.DataFrame(produkty_raw)
    df_k = pd.DataFrame(kategorie_raw)
    df = df_p.merge(df_k, left_on="kategoria_id", right_on="id", suffixes=('_prod', '_kat'))

    # 1. SEKCOJA: WSKAŹNIKI (Metrics)
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.metric("Wartość Magazynu", f"{(df['cena'] * df['liczba']).sum():,.2f} zł")
    with m2: st.metric("Liczba Produktów", len(df))
    with m3: st.metric("Suma Sztuk", int(df['liczba'].sum()))
    with m4: st.metric("Liczba Kategorii", len(df_k))

    st.markdown("<div class='main-card'>", unsafe_allow_html=True)
    
    # 2. SEKCJA: WYKRESY
    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader("📊 Stan ilościowy produktów")
        st.bar_chart(df.set_index('nazwa_prod')['liczba'])
    with c2:
        st.subheader("🥧 Wartość wg kategorii")
        kat_val = df.groupby('nazwa_kat')['cena'].sum()
        st.area_chart(kat_val)
    
    st.markdown("</div>", unsafe_allow_html=True)

    # 3. SEKCJA: TABELA I OPERACJE
    st.subheader("📝 Rejestr Produktów")
    search = st.text_input("🔍 Szybkie szukanie...")
    display_df = df[df['nazwa_prod'].str.contains(search, case=False)] if search else df
    
    st.dataframe(display_df[['id_prod', 'nazwa_prod', 'liczba', 'cena', 'nazwa_kat']], use_container_width=True)

    # 4. SEKCJA: FORMULARZE (W dolnej części w kolumnach)
    st.divider()
    col_add_p, col_add_k, col_del = st.columns(3)

    with col_add_p:
        st.write("### ➕ Dodaj Produkt")
        with st.form("new_prod"):
            n = st.text_input("Nazwa")
            l = st.number_input("Ilość", min_value=0)
            c = st.number_input("Cena", min_value=0.0)
            k = st.selectbox("Kategoria", df_k['nazwa'].tolist())
            if st.form_submit_button("Dodaj"):
                k_id = int(df_k[df_k['nazwa'] == k]['id'].values[0])
                supabase.table("produkty").insert({"nazwa": n, "liczba": l, "cena": c, "kategoria_id": k_id}).execute()
                st.rerun()

    with col_add_k:
        st.write("### 📂 Nowa Kategoria")
        with st.form("new_kat"):
            kn = st.text_input("Nazwa kategorii")
            ko = st.text_input("Opis")
            if st.form_submit_button("Dodaj"):
                supabase.table("kategorie").insert({"nazwa": kn, "opis": ko}).execute()
                st.rerun()

    with col_del:
        st.write("### 🗑️ Usuwanie")
        type_to_del = st.radio("Co chcesz usunąć?", ["Produkt", "Kategorię"])
        id_to_del = st.number_input("Podaj ID do usunięcia", step=1)
        if st.button("Potwierdź usunięcie"):
            t_name = "produkty" if type_to_del == "Produkt" else "kategorie"
            supabase.table(t_name).delete().eq("id", id_to_del).execute()
            st.rerun()

else:
    st.info("Baza jest pusta. Dodaj pierwszą kategorię i produkt w panelu poniżej.")
    # Tutaj uproszczone formularze jeśli baza jest całkiem pusta...
