import streamlit as st
from supabase import create_client, Client
import pandas as pd

# --- POŁĄCZENIE Z BAZĄ ---
def init_connection():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error("Błąd konfiguracji Secrets! Sprawdź SUPABASE_URL i SUPABASE_KEY.")
        st.stop()

supabase = init_connection()

st.set_page_config(page_title="WMS Supabase", layout="wide")
st.title("📦 System Zarządzania Magazynem")

# Tworzenie zakładek
tab_view, tab_prod, tab_kat = st.tabs(["📋 Podgląd Magazynu", "➕ Dodaj Produkt", "📂 Dodaj Kategorię"])

# --- ZAKŁADKA: PODGLĄD (LISTA) ---
with tab_view:
    st.header("Aktualne stany")
    if st.button("Odśwież listę"):
        try:
            # Pobieramy produkty wraz z nazwą kategorii przez relację (join)
            # Uwaga: "Kategorie(nazwa)" zadziała tylko przy ustawionym Foreign Key w Supabase
            res = supabase.table("produkty").select("id, nazwa, liczba, cena, kategoria_id, Kategorie(nazwa)").execute()
            
            if res.data:
                # Spłaszczamy dane, aby nazwa kategorii była w jednej linii
                flat_data = []
                for item in res.data:
                    kat_name = item.get('Kategorie', {}).get('nazwa', 'Brak') if item.get('Kategorie') else "Niezdefiniowana"
                    flat_data.append({
                        "ID": item['id'],
                        "Nazwa": item['nazwa'],
                        "Ilość": item['liczba'],
                        "Cena": f"{item['cena']} zł",
                        "Kategoria": kat_name
                    })
                st.table(flat_data)
            else:
                st.info("Brak produktów w bazie.")
        except Exception as e:
            st.error(f"Nie udało się pobrać danych: {e}")

# --- ZAKŁADKA: DODAJ KATEGORIĘ ---
with tab_kat:
    st.header("Nowa kategoria")
    with st.form("form_kategorie", clear_on_submit=True):
        nazwa_k = st.text_input("Nazwa kategorii")
        opis_k = st.text_area("Opis")
        submit_k = st.form_submit_button("Dodaj do bazy")
        
        if submit_k:
            if nazwa_k:
                res_k = supabase.table("Kategorie").insert({"nazwa": nazwa_k, "opis": opis_k}).execute()
                st.success(f"Dodano kategorię: {nazwa_k}")
            else:
                st.warning("Nazwa jest wymagana.")

# --- ZAKŁADKA: DODAJ PRODUKT ---
with tab_prod:
    st.header("Nowy produkt")
    
    # Najpierw musimy pobrać dostępne kategorie do listy rozwijanej
    try:
        kat_query = supabase.table("Kategorie").select("id, nazwa").execute()
        dict_kategorii = {item['nazwa']: item['id'] for item in kat_query.data}
        opcje_kategorii = list(dict_kategorii.keys())
    except:
        opcje_kategorii = []
        st.error("Błąd pobierania kategorii. Czy tabele są puste?")

    if opcje_kategorii:
        with st.form("form_produkty", clear_on_submit=True):
            p_nazwa = st.text_input("Nazwa produktu")
            p_liczba = st.number_input("Ilość", min_value=0, step=1)
            p_cena = st.number_input("Cena", min_value=0.0, format="%.2f")
            p_kat_nazwa = st.selectbox("Kategoria", options=opcje_kategorii)
            
            submit_p = st.form_submit_button("Zapisz produkt")
            
            if submit_p:
                if p_nazwa:
                    payload = {
                        "nazwa": p_nazwa,
                        "liczba": p_liczba,
                        "cena": p_cena,
                        "kategoria_id": dict_kategorii[p_kat_nazwa]
                    }
                    try:
                        supabase.table("produkty").insert(payload).execute()
                        st.success(f"Produkt {p_nazwa} został zapisany.")
                    except Exception as e:
                        st.error(f"Błąd zapisu produktu: {e}")
                else:
                    st.warning("Podaj nazwę produktu.")
    else:
        st.info("Dodaj najpierw kategorię, aby móc przypisać do niej produkty.")
