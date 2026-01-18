import streamlit as st
from supabase import create_client, Client

# Konfiguracja połączenia z Supabase
# Streamlit pobierze te dane automatycznie z "Secrets" w chmurze lub z .streamlit/secrets.toml lokalnie
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Zarządzanie Magazynem", layout="wide")
st.title("📦 System Zarządzania Produktami")

# --- BOCZNY PANEL: NAWIGACJA ---
menu = st.sidebar.radio("Menu", ["Produkty", "Kategorie"])

# --- FUNKCJE POMOCNICZE ---
def get_data(table_name):
    return supabase.table(table_name).select("*").execute()

def delete_row(table_name, row_id):
    supabase.table(table_name).delete().eq("id", row_id).execute()
    st.success(f"Usunięto rekord o ID {row_id} z tabeli {table_name}")
    st.rerun()

# --- ZAKŁADKA: KATEGORIE ---
if menu == "Kategorie":
    st.header("📂 Zarządzanie Kategoriami")
    
    # Formularz dodawania
    with st.expander("➕ Dodaj nową kategorię"):
        with st.form("add_kategoria"):
            nazwa = st.text_input("Nazwa kategorii")
            opis = st.text_area("Opis")
            submitted = st.form_submit_button("Zapisz kategorię")
            
            if submitted and nazwa:
                supabase.table("Kategorie").insert({"nazwa": nazwa, "opis": opis}).execute()
                st.success("Dodano kategorię!")
                st.rerun()

    # Wyświetlanie i usuwanie
    data = get_data("Kategorie")
    if data.data:
        for item in data.data:
            col1, col2, col3 = st.columns([3, 5, 1])
            col1.write(f"**{item['nazwa']}**")
            col2.write(item['opis'])
            if col3.button("🗑️", key=f"del_kat_{item['id']}"):
                delete_row("Kategorie", item['id'])
    else:
        st.info("Brak kategorii w bazie.")

# --- ZAKŁADKA: PRODUKTY ---
elif menu == "Produkty":
    st.header("🛒 Zarządzanie Produktami")

    # Pobieranie kategorii do dropdowna
    kategorie_data = get_data("Kategorie").data
    kat_dict = {k['nazwa']: k['id'] for k in kategorie_data}

    # Formularz dodawania
    with st.expander("➕ Dodaj nowy produkt"):
        if not kat_dict:
            st.warning("Najpierw dodaj przynajmniej jedną kategorię!")
        else:
            with st.form("add_produkt"):
                nazwa = st.text_input("Nazwa produktu")
                liczba = st.number_input("Ilość (liczba)", min_value=0, step=1)
                cena = st.number_input("Cena", min_value=0.0, format="%.2f")
                kat_nazwa = st.selectbox("Kategoria", options=list(kat_dict.keys()))
                
                submitted = st.form_submit_button("Zapisz produkt")
                
                if submitted and nazwa:
                    new_prod = {
                        "nazwa": nazwa,
                        "liczba": liczba,
                        "cena": cena,
                        "kategoria_id": kat_dict[kat_nazwa]
                    }
                    supabase.table("produkty").insert(new_prod).execute()
                    st.success("Dodano produkt!")
                    st.rerun()

    # Wyświetlanie i usuwanie
    data = get_data("produkty")
    if data.data:
        st.table(data.data) # Prosty podgląd tabeli
        
        # Opcja usuwania po ID dla przejrzystości
        to_delete = st.selectbox("Wybierz ID produktu do usunięcia", [p['id'] for p in data.data])
        if st.button("Usuń wybrany produkt"):
            delete_row("produkty", to_delete)
    else:
        st.info("Brak produktów w bazie.")
