import streamlit as st
from supabase import create_client, Client

# --- KONFIGURACJA POŁĄCZENIA ---
# Zastąp te wartości swoimi danymi z Supabase (Settings -> API)
SUPABASE_URL = "https://huapjqfvngnrolkfwyzh.supabase.co"
SUPABASE_KEY = "sb_publishable_IMQ1fHUsVHVvnaHuTY3Q0g_pMuC5s-X"

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_connection()

st.title("📦 Zarządzanie Magazynem")

# Tworzymy zakładki dla lepszej przejrzystości
tab1, tab2 = st.tabs(["Dodaj Kategorię", "Dodaj Produkt"])

# --- TAB 1: DODAWANIE KATEGORII ---
with tab1:
    st.header("Nowa Kategoria")
    with st.form("form_kategoria", clear_on_submit=True):
        nazwa_kat = st.text_input("Nazwa kategorii")
        opis_kat = st.text_area("Opis")
        
        submit_kat = st.form_submit_button("Zapisz kategorię")
        
        if submit_kat:
            if nazwa_kat:
                data = {"nazwa": nazwa_kat, "opis": opis_kat}
                response = supabase.table("Kategoria").insert(data).execute()
                st.success(f"Dodano kategorię: {nazwa_kat}")
            else:
                st.error("Nazwa kategorii jest wymagana!")

# --- TAB 2: DODAWANIE PRODUKTU ---
with tab2:
    st.header("Nowy Produkt")
    
    # Pobieramy aktualne kategorie, aby przypisać produkt do ID
    kategorie_query = supabase.table("Kategoria").select("id, nazwa").execute()
    kategorie_dict = {item['nazwa']: item['id'] for item in kategorie_query.data}
    
    with st.form("form_produkt", clear_on_submit=True):
        nazwa_prod = st.text_input("Nazwa produktu")
        liczba = st.number_input("Ilość (liczba)", min_value=0, step=1)
        cena = st.number_input("Cena", min_value=0.0, format="%.2f")
        wybrana_kat_nazwa = st.selectbox("Wybierz kategorię", options=list(kategorie_dict.keys()))
        
        submit_prod = st.form_submit_button("Zapisz produkt")
        
        if submit_prod:
            if nazwa_prod and wybrana_kat_nazwa:
                data_prod = {
                    "nazwa": nazwa_prod,
                    "liczba": liczba,
                    "cena": cena,
                    "kategoria_id": kategorie_dict[wybrana_kat_nazwa]
                }
                response = supabase.table("Produkty").insert(data_prod).execute()
                st.success(f"Dodano produkt: {nazwa_prod}")
            else:
                st.error("Wypełnij wymagane pola!")

# --- PODGLĄD DANYCH ---
st.divider()
if st.checkbox("Pokaż listę produktów"):
    res = supabase.table("Produkty").select("nazwa, liczba, cena, Kategoria(nazwa)").execute()
    st.table(res.data)
