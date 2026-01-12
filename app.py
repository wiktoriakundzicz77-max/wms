import streamlit as st
from supabase import create_client, Client

# --- INICJALIZACJA POŁĄCZENIA ---
def init_connection():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error("Błąd: Nie znaleziono kluczy w st.secrets!")
        st.stop()

supabase = init_connection()

st.set_page_config(page_title="Magazyn WMS", layout="centered")
st.title("📦 System Magazynowy (Supabase)")

tab1, tab2, tab3 = st.tabs(["➕ Dodaj Produkt", "📂 Dodaj Kategorię", "📋 Lista"])

# --- TABELA: KATEGORIE ---
with tab2:
    st.header("Nowa kategoria")
    with st.form("form_kat", clear_on_submit=True):
        nazwa_k = st.text_input("Nazwa kategorii")
        opis_k = st.text_area("Opis")
        submit_k = st.form_submit_button("Zapisz kategorię")

        if submit_k:
            if nazwa_k:
                try:
                    # Używamy małych liter: "kategorie"
                    supabase.table("kategorie").insert({"nazwa": nazwa_k, "opis": opis_k}).execute()
                    st.success(f"Dodano kategorię: {nazwa_k}")
                except Exception as e:
                    st.error(f"Błąd zapisu: {e}")
            else:
                st.warning("Podaj nazwę kategorii!")

# --- TABELA: PRODUKTY ---
with tab1:
    st.header("Nowy produkt")
    
    # Pobieranie listy kategorii do wyboru (małe litery)
    try:
        res_kat = supabase.table("kategorie").select("id, nazwa").execute()
        kategorie_dict = {item['nazwa']: item['id'] for item in res_kat.data}
        lista_nazw = list(kategorie_dict.keys())
    except Exception:
        lista_nazw = []
        st.error("Nie udało się pobrać kategorii z bazy.")

    if lista_nazw:
        with st.form("form_prod", clear_on_submit=True):
            p_nazwa = st.text_input("Nazwa produktu")
            p_liczba = st.number_input("Ilość", min_value=0, step=1)
            p_cena = st.number_input("Cena", min_value=0.0, format="%.2f")
            p_kat_wybrana = st.selectbox("Wybierz kategorię", options=lista_nazw)
            
            submit_p = st.form_submit_button("Zapisz produkt")

            if submit_p:
                if p_nazwa:
                    payload = {
                        "nazwa": p_nazwa,
                        "liczba": p_liczba,
                        "cena": p_cena,
                        "kategoria_id": kategorie_dict[p_kat_wybrana]
                    }
                    try:
                        # Używamy małych liter: "produkty"
                        supabase.table("produkty").insert(payload).execute()
                        st.success(f"Produkt {p_nazwa} dodany!")
                    except Exception as e:
                        st.error(f"Błąd zapisu produktu: {e}")
                else:
                    st.warning("Nazwa produktu jest wymagana.")
    else:
        st.info("Najpierw dodaj kategorię w odpowiedniej zakładce.")

# --- TABELA: PODGLĄD ---
with tab3:
    st.header("Aktualne stany")
    if st.button("Odśwież dane"):
        try:
            # Join z kategorią (małe litery: "kategorie(nazwa)")
            res = supabase.table("produkty").select("nazwa, liczba, cena, kategorie(nazwa)").execute()
            
            if res.data:
                # Czyszczenie danych do ładnej tabeli
                display_data = []
                for row in res.data:
                    display_data.append({
                        "Produkt": row['nazwa'],
                        "Ilość": row['liczba'],
                        "Cena": f"{row['cena']} zł",
                        "Kategoria": row['kategorie']['nazwa'] if row['kategorie'] else "Brak"
                    })
                st.dataframe(display_data, use_container_width=True)
            else:
                st.info("Baza danych jest pusta.")
        except Exception as e:
            st.error(f"Błąd podczas pobierania listy: {e}")
