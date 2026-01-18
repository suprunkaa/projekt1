import streamlit as st
from supabase import create_client, Client
import pandas as pd

# 1. Inicjalizacja połączenia
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Błąd połączenia z Supabase. Sprawdź plik secrets.toml lub ustawienia w chmurze.")
    st.stop()

st.set_page_config(page_title="Magazyn Pro", layout="wide", initial_sidebar_state="expanded")

# --- STYLE CSS DLA WYGLĄDU ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- BOCZNY PANEL ---
st.sidebar.title("🎮 Panel Sterowania")
menu = st.sidebar.radio("Przejdź do:", ["📦 Produkty", "📂 Kategorie", "📊 Analityka"])

# --- FUNKCJE ---
def get_data(table_name):
    return supabase.table(table_name).select("*").execute()

def delete_row(table_name, row_id):
    supabase.table(table_name).delete().eq("id", row_id).execute()
    st.toast(f"Usunięto z {table_name}!")
    st.rerun()

# --- LOGIKA APLIKACJI ---

if menu == "📂 Kategorie":
    st.header("Zarządzanie Kategoriami")
    
    with st.expander("➕ Dodaj nową kategorię"):
        with st.form("form_kat"):
            nazwa = st.text_input("Nazwa")
            opis = st.text_area("Opis")
            if st.form_submit_button("Zapisz"):
                supabase.table("kategorie").insert({"nazwa": nazwa, "opis": opis}).execute()
                st.rerun()

    data = get_data("kategorie")
    if data.data:
        df_kat = pd.DataFrame(data.data)
        st.dataframe(df_kat, use_container_width=True)
        
        to_del = st.selectbox("Usuń kategorię (wybierz ID)", df_kat['id'])
        if st.button("Usuń kategorię"):
            delete_row("kategorie", to_del)

elif menu == "📦 Produkty":
    st.header("Lista Produktów")
    
    # Pobieranie kategorii do formularza
    kat_resp = get_data("kategorie").data
    kat_dict = {k['nazwa']: k['id'] for k in kat_resp}

    with st.expander("➕ Dodaj produkt"):
        if not kat_dict:
            st.warning("Najpierw dodaj kategorię!")
        else:
            with st.form("form_prod"):
                col_a, col_b = st.columns(2)
                nazwa = col_a.text_input("Nazwa produktu")
                kat_wybrana = col_b.selectbox("Kategoria", list(kat_dict.keys()))
                liczba = col_a.number_input("Ilość", min_value=0)
                cena = col_b.number_input("Cena (zł)", min_value=0.0)
                if st.form_submit_button("Dodaj produkt"):
                    supabase.table("produkty").insert({
                        "nazwa": nazwa, "liczba": liczba, 
                        "cena": cena, "kategoria_id": kat_dict[kat_wybrana]
                    }).execute()
                    st.rerun()

    # Wyświetlanie z wyszukiwarką
    data_prod = get_data("produkty").data
    if data_prod:
        df_p = pd.DataFrame(data_prod)
        search = st.text_input("🔍 Szukaj produktu...")
        if search:
            df_p = df_p[df_p['nazwa'].str.contains(search, case=False)]
        
        st.dataframe(df_p, use_container_width=True)
        
        to_del_p = st.number_input("ID produktu do usunięcia", step=1)
        if st.button("Usuń produkt"):
            delete_row("produkty", to_del_p)

elif menu == "📊 Analityka":
    st.header("Analiza Stanów Magazynowych")
    
    prod_data = get_data("produkty").data
    kat_data = get_data("kategorie").data
    
    if prod_data and kat_data:
        df_p = pd.DataFrame(prod_data)
        df_k = pd.DataFrame(kat_data)
        df = df_p.merge(df_k, left_on="kategoria_id", right_on="id", suffixes=('_prod', '_kat'))
        
        # Wskaźniki
        m1, m2, m3 = st.columns(3)
        m1.metric("Wartość towaru", f"{(df['cena'] * df['liczba']).sum():,.2f} zł")
        m2.metric("Suma sztuk", int(df['liczba'].sum()))
        m3.metric("Liczba asortymentu", len(df))
        
        st.subheader("Ilość towaru per produkt")
        st.bar_chart(df.set_index('nazwa_prod')['liczba'])
        
        st.subheader("Wartość magazynu wg kategorii")
        df['total_val'] = df['cena'] * df['liczba']
        val_per_kat = df.groupby('nazwa_kat')['total_val'].sum()
        st.area_chart(val_per_kat)
    else:
        st.info("Brak danych do analizy.")
