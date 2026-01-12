import streamlit as st
from supabase import create_client, Client

# --- KONFIGURACJA ---
# Dane pobierane z Settings -> Secrets w Streamlit Cloud
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Błąd konfiguracji sekretów. Sprawdź ustawienia w Streamlit Cloud.")
    st.stop()

st.set_page_config(page_title="System Magazynowy", layout="centered")
st.title("📦 Zarządzanie Produktami")

tab1, tab2, tab3 = st.tabs(["➕ Dodaj Produkt", "📂 Dodaj Kategorię", "📋 Lista"])

# --- TAB 2: DODAWANIE KATEGORII ---
with tab2:
    st.header("Dodaj nową kategorię")
    with st.form("form_kat", clear_on_submit=True):
        nazwa_kat = st.text_input("Nazwa kategorii (wymagane)")
        opis_kat = st.text_area("Opis (opcjonalnie)")
        submit_kat = st.form_submit_button("Zapisz kategorię")

        if submit_kat:
            if nazwa_kat:
                # Nazwa tabeli: Kategorie (zgodnie z obrazkiem)
                data = {"nazwa": nazwa_kat, "opis": opis_kat}
                try:
                    supabase.table("Kategorie").insert(data).execute()
                    st.success(f"Dodano kategorię: {nazwa_kat}")
                except Exception as e:
                    st.error(f"Błąd zapisu: {e}")
            else:
                st.warning("Musisz podać nazwę kategorii.")

# --- TAB 1: DODAWANIE PRODUKTU ---
with tab1:
    st.header("Dodaj nowy produkt")
    
    # Pobieranie kategorii do listy rozwijanej
    try:
        kat_res = supabase.table("Kategorie").select("id, nazwa").execute()
        kategorie = {item['nazwa']: item['id'] for item in kat_res.data}
    except Exception:
        kategorie = {}
        st.error("Nie udało się pobrać kategorii. Sprawdź reguły RLS.")

    with st.form("form_prod", clear_on_submit=True):
        nazwa_prod = st.text_input("Nazwa produktu")
        liczba = st.number_input("Ilość (liczba)", min_value=0, step=1)
        cena = st.number_input("Cena (numeric)", min_value=0.0, format="%.2f")
        
        kat_nazwa = st.selectbox("Wybierz kategorię", options=list(kategorie.keys()))
        
        submit_prod = st.form_submit_button("Zapisz produkt")

        if submit_prod:
            if nazwa_prod and kat_nazwa:
                payload = {
                    "nazwa": nazwa_prod,
                    "liczba": liczba,
                    "cena": cena,
                    "kategoria_id": kategorie[kat_nazwa]
                }
                try:
                    supabase.table("produkty").insert(payload).execute()
                    st.success(f"Dodano produkt: {nazwa_prod}")
                except Exception as e:
                    st.error(f"Błąd: {e}")
            else:
                st.warning("Uzupełnij nazwę i wybierz kategorię.")

# --- TAB 3: PODGLĄD ---
with tab3:
    st.header("Aktualny stan magazynu")
    if st.button("Odśwież dane"):
        # Pobieranie produktów wraz z nazwą kategorii (tzw. join)
        res = supabase.table("produkty").select("nazwa, liczba, cena, Kategorie(nazwa)").execute()
        if res.data:
            st.table(res.data)
        else:
            st.info("Brak danych w bazie.")
