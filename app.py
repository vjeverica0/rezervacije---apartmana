import streamlit as st
import gspread
import pandas as pd

st.title("Evidencija rezervacija apartmana")

klijent = gspread.service_account_from_dict(
    dict(st.secrets["gcp_service_account"])
)
tablica = klijent.open("Rezervacija apartmana")
radni_list = tablica.worksheet("rezervacije")

podaci = radni_list.get_all_records()
rezervacije = pd.DataFrame(podaci)

st.subheader("Sve rezervacije")
st.dataframe(rezervacije, hide_index=True)

st.subheader("Dodaj novu rezervaciju")

with st.form("nova_rezervacija", clear_on_submit=True):
    gost = st.text_input("Ime i prezime gosta")

    apartman = st.selectbox(
        "Apartman",
        [
            "Studio 1",
            "Studio 2",
            "Deluxe 3",
            "Sea View 4",
            "Standard 5",
            "Superior 6",
            "Standard 7"
        ]
    )

    dolazak = st.date_input("Datum dolaska")
    odlazak = st.date_input("Datum odlaska")

    cijena = st.number_input(
        "Cijena po noći (€)",
        min_value=1.0,
        value=80.0,
        step=5.0
    )

    spremi = st.form_submit_button("Spremi rezervaciju")


    if spremi:
        if not gost.strip():
            st.warning("Unesi ime i prezime gosta.")

        elif odlazak <= dolazak:
            st.warning("Datum odlaska mora biti nakon datuma dolaska.")

        else:
            broj_nocenja = (odlazak - dolazak).days
            ukupno = round(broj_nocenja * cijena, 2)

            radni_list.append_row([
                gost.strip(),
                apartman,
                dolazak.isoformat(),
                odlazak.isoformat(),
                broj_nocenja,
                cijena,
                ukupno
            ])

            st.rerun()

st.subheader("Pretraživanje i filtriranje")

if rezervacije.empty:
    st.info("Nema rezervacija za pretraživanje.")

else:
    trazeni_gost = st.text_input("Pretraži po imenu gosta")

    trazeni_apartman = st.selectbox(
        "Filtriraj po apartmanu",
        ["Svi"] + sorted(rezervacije["Apartman"].unique().tolist())
    )

    filtrirane = rezervacije.copy()

    if trazeni_gost.strip():
        filtrirane = filtrirane[
            filtrirane["Gost"].str.contains(
                trazeni_gost.strip(),
                case=False,
                na=False,
                regex=False
            )
        ]

    if trazeni_apartman != "Svi":
        filtrirane = filtrirane[
            filtrirane["Apartman"] == trazeni_apartman
        ]

    if filtrirane.empty:
        st.info("Nema rezervacija koje odgovaraju pretrazi.")

    else:
        st.dataframe(filtrirane, hide_index=True)

st.subheader("Brisanje rezervacije")

if rezervacije.empty:
    st.info("Nema rezervacija za brisanje.")

else:
    def opis_rezervacije(indeks):
        redak = rezervacije.iloc[indeks]
        return (
            f"{redak['Gost']} | {redak['Apartman']} | "
            f"{redak['Dolazak']} – {redak['Odlazak']}"
        )

    odabrani_indeks = st.selectbox(
        "Odaberi rezervaciju za brisanje",
        options=range(len(rezervacije)),
        format_func=opis_rezervacije,
        index=None,
        placeholder="Odaberi rezervaciju"
    )

    potvrda = st.checkbox("Potvrđujem brisanje odabrane rezervacije")

    if st.button("Obriši rezervaciju"):
        if odabrani_indeks is None:
            st.warning("Najprije odaberi rezervaciju.")

        elif not potvrda:
            st.warning("Označi potvrdu brisanja.")

        else:
            redak_u_tablici = odabrani_indeks + 2
            radni_list.delete_rows(redak_u_tablici)
            st.rerun()

st.subheader("Tri rezervacije s najvećim iznosom")

if rezervacije.empty:
    st.info("Nema rezervacija za sortiranje.")

else:
    rezervacije["Ukupno"] = pd.to_numeric(
        rezervacije["Ukupno"],
        errors="coerce"
    )

    najbolje = rezervacije.sort_values(
        "Ukupno",
        ascending=False
    ).head(3)

    st.dataframe(najbolje, hide_index=True)
    