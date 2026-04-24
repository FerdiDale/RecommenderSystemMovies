import streamlit as st
from critiqueQuery import build_critique_query

DEBUG = False
DEBUG2 = False

# Utility per pulire i nomi dei registi (es. da URI a nome leggibile)
def clean_director_name(uri):
    return uri.split("/")[-1].replace("_", " ")

def critiqueGui():
    if DEBUG:
        st.write("🔵 DEBUG: ENTRO IN critiqueGui()")

    # sicurezza
    if "movie_chosen_attrs" not in st.session_state:
        st.error("❌ movie_chosen_attrs mancante in session_state")
        return

    movie = st.session_state.movie_chosen_attrs

    # Recupero il tipo del campo director per debug
    if DEBUG2:
        st.write("🎬 DIRECTOR DEBUG")
        st.write("value:", movie.get("director"))

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

    if DEBUG:
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

    
    if DEBUG:
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

    if DEBUG:
        st.write("🟡 DEBUG tags:", selected_tags)

    st.divider()

    # -----------------------
    # DIRECTORS
    # -----------------------
    directors_raw = list(movie.get("director") or [])

    directors = [clean_director_name(d) for d in directors_raw]

    selected_directors = st.multiselect(
        "Registi",
        directors,
        default=directors,
        key="critique_directors"
    )

    if DEBUG2:
        st.write("🎬 directors raw:", movie.get("director"))
        st.write("🎬 directors list:", directors)

    # -----------------------
    # ACTORS
    # -----------------------
    actors_raw = list(movie.get("starring") or [])

    actors = [clean_director_name(a) for a in actors_raw]

    selected_actors = st.multiselect(
        "Attori",
        actors,
        default=actors,
        key="critique_actors"
    )

    if DEBUG2:
        st.write("🎭 actors raw:", actors_raw)
        st.write("🎭 actors list:", actors)
        st.write("🎭 selected actors:", selected_actors)

    # -----------------------
    # RUNTIME
    # -----------------------
    runtime_option = st.radio(
       "Durata del film",
       ["Più lungo", "Più breve", "Simile"],
       key="critique_runtime"
    )

    if DEBUG2:
       st.write("⏱ runtime option:", runtime_option)

    # =========================================================
    # FIX: BUTTON SENZA STATE PERSISTENTE
    # =========================================================

    if st.button("🔍 Effettua ricerca", key="critique_button"):

        
        if DEBUG:
            st.write("🟢 DEBUG: BUTTON PREMUTO")

        critique_query = build_critique_query(
            movie["releaseYear"],
            selected_genres,
            selected_tags,
            recency_option,
            selected_directors,
            selected_actors,
            runtime_option,
            movie["runtime"]
        )

        print(critique_query)

        
        if DEBUG:
            st.write("🟢 DEBUG query creata")
        st.code(critique_query[:500], language="sparql")

        # aggiorna stato globale
        st.session_state.movie_query = critique_query

        # IMPORTANTISSIMO: reset navigazione
        del st.session_state["critique_phase"]

        st.rerun()