import pandas as pd # Dodaj na górze pliku

# --- NOWA OPCJA W MENU ---
menu = st.sidebar.radio("Menu", ["Produkty", "Kategorie", "Analityka"])

if menu == "Analityka":
    st.header("📊 Analiza Magazynu")
    
    # Pobranie danych
    prod_resp = get_data("produkty")
    kat_resp = get_data("kategorie")
    
    if prod_resp.data and kat_resp.data:
        df_prod = pd.DataFrame(prod_resp.data)
        df_kat = pd.DataFrame(kat_resp.data)
        
        # Łączenie danych, aby mieć nazwy kategorii zamiast ID
        df = df_prod.merge(df_kat, left_on="kategoria_id", right_on="id", suffixes=('_prod', '_kat'))
        
        # --- WSKAŹNIKI KLUCZOWE (METRICS) ---
        col1, col2, col3 = st.columns(3)
        total_value = (df['cena'] * df['liczba']).sum()
        col1.metric("Łączna wartość magazynu", f"{total_value:,.2f} zł")
        col2.metric("Liczba produktów", len(df))
        col3.metric("Średnia cena produktu", f"{df['cena'].mean():,.2f} zł")
        
        st.divider()
        
        # --- WYKRESY ---
        c1, c2 = st.columns(2)
        
        with c1:
            st.subheader("Ilość produktów w magazynie")
            # Wykres słupkowy: Nazwa vs Liczba
            st.bar_chart(data=df, x="nazwa_prod", y="liczba", color="#FF4B4B")
            
        with c2:
            st.subheader("Wartość produktów wg kategorii")
            # Obliczamy wartość (cena * liczba) dla każdej kategorii
            df['wartosc_calkowita'] = df['cena'] * df['liczba']
            kat_stats = df.groupby('nazwa_kat')['wartosc_calkowita'].sum()
            st.area_chart(kat_stats) # Możesz też użyć st.bar_chart
            
    else:
        st.warning("Za mało danych, aby wygenerować wykresy. Dodaj produkty i kategorie.")
