import streamlit as st
from supabase import create_client, Client
import pandas as pd

# --- INICJALIZACJA POŁĄCZENIA ---
def init_connection():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error("Błąd konfiguracji kluczy w Secrets!")
        st.stop()

supabase = init_connection()

st.set_page_config(page_title="WMS PRO", layout="wide")
st.title("📊 Panel Zarządzania i Analizy Magazynu")

# Zakładki
tab_dash, tab_manage, tab_add = st.tabs(["📈 Dashboard", "🛠️ Zarządzanie Produktami", "📂 Nowa Kategoria"])

# --- TAB 1: DASHBOARD (WYKRESY I STATYSTYKI) ---
with tab_dash:
    st.header("Statystyki ogólne")
    try:
        res = supabase.table("produkty").select("nazwa, liczba, cena, kategorie(nazwa)").execute()
        if res.data:
            df = pd.DataFrame([
                {
                    "Produkt": r['nazwa'],
                    "Ilość": r['liczba'],
                    "Cena": r['cena'],
                    "Kategoria": r['kategorie']['nazwa'] if r['kategorie'] else "Brak",
                    "Wartość": r['liczba'] * r['cena']
                } for r in res.data
            ])

            # Metryki
            c1, c2, c3 = st.columns(3)
            c1.metric("Unikalne produkty", len(df))
            c2.metric("Suma wszystkich sztuk", int(df["Ilość"].sum()))
            c3.metric("Łączna wartość netto", f"{df['Wartość'].sum():,.2f} zł")

            st.divider()

            # Wykresy
            col_l, col_r = st.columns(2)
            with col_l:
                st.subheader("Stan magazynowy wg kategorii")
                cat_chart = df.groupby("Kategoria")["Ilość"].sum()
                st.bar_chart(cat_chart)
            
            with col_r:
                st.subheader("Udział wartościowy produktów")
                st.line_chart(df.set_index("Produkt")["Wartość"])

            st.subheader("Pełna lista produktów")
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Brak danych do wyświetlenia wykresów.")
    except Exception as e:
        st.error(f"Błąd dashboardu: {e}")

# --- TAB 2: ZARZĄDZANIE (DODAWANIE I USUWANIE) ---
with tab_manage:
    col_add, col_del = st.columns([2, 1])

    with col_add:
        st.header("Dodaj nowy produkt")
        try:
            kat_res = supabase.table("kategorie").select("id, nazwa").execute()
            kategorie_map = {k['nazwa']: k['id'] for k in kat_res.data}
            
            with st.form("add_product_form", clear_on_submit=True):
                p_nazwa = st.text_input("Nazwa produktu")
                p_ilosc = st.number_input("Ilość", min_value=0, step=1)
                p_cena = st.number_input("Cena (zł)", min_value=0.0, format="%.2f")
                p_kat = st.selectbox("Kategoria", options=list(kategorie_map.keys()))
                
                if st.form_submit_button("Dodaj produkt"):
                    if p_nazwa:
                        new_item = {
                            "nazwa": p_nazwa, 
                            "liczba": p_ilosc, 
                            "cena": p_cena, 
                            "kategoria_id": kategorie_map[p_kat]
                        }
                        supabase.table("produkty").insert(new_item).execute()
                        st.success(f"Dodano: {p_nazwa}")
                        st.rerun()
        except:
            st.warning("Najpierw dodaj kategorię!")

    with col_del:
        st.header("Usuń produkt")
        try:
            prod_res = supabase.table("produkty").select("id, nazwa").execute()
            if prod_res.data:
                produkty_do_usuniecia = {p['nazwa']: p['id'] for p in prod_res.data}
                wybrany_do_usuniecia = st.selectbox("Wybierz produkt do usunięcia", options=list(produkty_do_usuniecia.keys()))
                
                if st.button("❌ Usuń trwale", type="primary"):
                    target_id = produkty_do_usuniecia[wybrany_do_usuniecia]
                    supabase.table("produkty").delete().eq("id", target_id).execute()
                    st.warning(f"Usunięto: {wybrany_do_usuniecia}")
                    st.rerun()
            else:
                st.write("Brak produktów do usunięcia.")
        except Exception as e:
            st.error(f"Błąd usuwania: {e}")

# --- TAB 3: NOWA KATEGORIA ---
with tab_add:
    st.header("Dodawanie kategorii")
    with st.form("add_cat_form", clear_on_submit=True):
        nowa_kat = st.text_input("Nazwa nowej kategorii")
        opis_kat = st.text_area("Krótki opis")
        if st.form_submit_button("Zapisz kategorię"):
            if nowa_kat:
                supabase.table("kategorie").insert({"nazwa": nowa_kat, "opis": opis_kat}).execute()
                st.success("Kategoria dodana!")
                st.rerun()
