import streamlit as st
from supabase import create_client, Client
import pandas as pd

# --- POŁĄCZENIE ---
def init_connection():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error("Błąd konfiguracji kluczy w Secrets!")
        st.stop()

supabase = init_connection()

st.set_page_config(page_title="WMS Dashboard", layout="wide")
st.title("📊 Panel Zarządzania Magazynem")

# Zakładki
tab_dash, tab_prod, tab_kat = st.tabs(["📈 Dashboard & Raporty", "➕ Produkty", "📂 Kategorie"])

# --- TAB 1: DASHBOARD & TABELE ---
with tab_dash:
    st.header("Statystyki Magazynowe")
    
    try:
        # Pobieranie danych z joinem (małe litery zgodnie z Twoim schematem)
        res = supabase.table("produkty").select("nazwa, liczba, cena, kategorie(nazwa)").execute()
        
        if res.data:
            # Konwersja do DataFrame dla łatwiejszej analizy
            df = pd.DataFrame([
                {
                    "Produkt": r['nazwa'],
                    "Ilość": r['liczba'],
                    "Cena jedn.": r['cena'],
                    "Kategoria": r['kategorie']['nazwa'] if r['kategorie'] else "Brak",
                    "Wartość": r['liczba'] * r['cena']
                } for r in res.data
            ])

            # --- SEKCOJA METRYK ---
            col1, col2, col3 = st.columns(3)
            col1.metric("Liczba produktów", len(df))
            col2.metric("Suma sztuk", int(df["Ilość"].sum()))
            col3.metric("Wartość magazynu", f"{df['Wartość'].sum():,.2f} zł")

            st.divider()

            # --- WYKRESY ---
            col_left, col_right = st.columns(2)
            
            with col_left:
                st.subheader("Ilość produktów wg kategorii")
                # Grupowanie danych do wykresu
                chart_data = df.groupby("Kategoria")["Ilość"].sum()
                st.bar_chart(chart_data)

            with col_right:
                st.subheader("Wartość produktów (zł)")
                chart_value = df.set_index("Produkt")["Wartość"]
                st.area_chart(chart_value)

            st.divider()

            # --- TABELA INTERAKTYWNA ---
            st.subheader("Szczegółowa lista produktów")
            st.dataframe(df, use_container_width=True, hide_index=True)
            
        else:
            st.info("Baza danych jest pusta. Dodaj kategorie i produkty.")
            
    except Exception as e:
        st.error(f"Błąd ładowania dashboardu: {e}")

# --- TAB 2: DODAWANIE PRODUKTU ---
with tab_prod:
    st.header("Dodaj nowy produkt")
    # Pobieranie kategorii do selectboxa
    kat_res = supabase.table("kategorie").select("id, nazwa").execute()
    kategorie = {k['nazwa']: k['id'] for k in kat_res.data}
    
    with st.form("new_product"):
        nazwa = st.text_input("Nazwa produktu")
        ilosc = st.number_input("Ilość", min_value=0)
        cena = st.number_input("Cena", min_value=0.0)
        kat = st.selectbox("Kategoria", options=list(kategorie.keys()))
        
        if st.form_submit_button("Dodaj produkt"):
            payload = {"nazwa": nazwa, "liczba": ilosc, "cena": cena, "kategoria_id": kategorie[kat]}
            supabase.table("produkty").insert(payload).execute()
            st.success("Produkt dodany!")
            st.rerun()

# --- TAB 3: DODAWANIE KATEGORII ---
with tab_kat:
    st.header("Nowa kategoria")
    with st.form("new_cat"):
        nazwa_k = st.text_input("Nazwa kategorii")
        opis_k = st.text_area("Opis")
        if st.form_submit_button("Zapisz"):
            supabase.table("kategorie").insert({"nazwa": nazwa_k, "opis": opis_k}).execute()
            st.success("Kategoria zapisana!")
            st.rerun()
