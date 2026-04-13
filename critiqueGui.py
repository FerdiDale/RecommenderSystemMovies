import streamlit as st
from critiqueQuery import build_critique_query


def critiqueGui():

    st.write("🔵 DEBUG: ENTRO IN critiqueGui()")

    # sicurezza
    if "movie_chosen_attrs" not in st.session_state:
        st.error("❌ movie_chosen_attrs mancante in session_state")
        return

    movie = st.session_state.movie_chosen_attrs

    st.title("🎯 Personalizza la tua ricerca")

    st.subheader(f'Scegli le tue preferenze rispetto a "{movie["title"]}"')

    # -----------------------
    # RECENCY
    # -----------------------
    recency_option = st.radio(
        "Anno di uscita",
        ["Più recente", "Meno recente"],
        key="critique_recency"
    )

    st.write("🟡 DEBUG recency:", recency_option)

    # -----------------------
    # GENRES
    # -----------------------
    genres = list(movie.get("genre", []))
    selected_genres = st.multiselect(
        "Generi",
        genres,
        default=genres,
        key="critique_genres"
    )

    st.write("🟡 DEBUG genres:", selected_genres)

    # -----------------------
    # TAGS
    # -----------------------
    tags = list(movie.get("tag", []))
    selected_tags = st.multiselect(
        "Tag",
        tags,
        default=tags,
        key="critique_tags"
    )

    st.write("🟡 DEBUG tags:", selected_tags)

    st.divider()

    # =========================================================
    # FIX: BUTTON SENZA STATE PERSISTENTE
    # =========================================================

    if st.button("🔍 Effettua ricerca", key="critique_button"):

        st.write("🟢 DEBUG: BUTTON PREMUTO")

        critique_query = build_critique_query(
            movie["releaseYear"],
            selected_genres,
            selected_tags,
            recency_option
        )

        print(critique_query)

        st.write("🟢 DEBUG query creata")
        st.code(critique_query[:500], language="sparql")

        # aggiorna stato globale
        st.session_state.movie_query = critique_query

        # IMPORTANTISSIMO: reset navigazione
        del st.session_state["critique_phase"]

        st.rerun()