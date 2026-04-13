import streamlit as st
import searchMovies
import cooccurrenceMatrix
import showSimilarMovies
import critiqueGui
from rdflib import Graph, URIRef, Literal, Namespace, RDFS, XSD

queryAllMovies = """
    PREFIX dbo: <http://dbpedia.org/ontology/>
    PREFIX dbp: <http://dbpedia.org/property/>
    SELECT DISTINCT ?movie ?title ?description ?avgRating ?runtime ?releaseYear ?genre ?director ?starring ?tag
    WHERE {
        ?movie rdfs:label ?title .
        OPTIONAL { ?movie dbo:description ?description . }
        OPTIONAL { ?movie dbo:avgRating ?avgRating . }
        OPTIONAL { ?movie dbo:runtime ?runtime . }
        OPTIONAL { ?movie dbo:releaseYear ?releaseYear . }
        OPTIONAL { ?movie dbo:genre ?genre . }
        OPTIONAL { ?movie dbo:director ?director . }
        OPTIONAL { ?movie dbo:starring ?starring . }
        OPTIONAL { ?movie dbo:tag ?tag . }
        }    
    """

@st.cache_resource
def initSystem():
    # Grafo costruito dai file Turtle ottenuti da DBPedia, che arricchiamo
    g = Graph()
    DBO = Namespace('http://dbpedia.org/ontology/')
    g.bind('dbo', DBO)
    g.bind('dbp', Namespace('http://dbpedia.org/property/'))
    g.parse("rich_database.ttl",format='ttl')
    genreCooccurrenceMatrix = cooccurrenceMatrix.buildGenreCooccurrenceMatrix()
    return g, genreCooccurrenceMatrix

def searchMoviesGui():
    st.title("🎬 Autocomplete Film RDF")
    st.subheader("Cerca un film")

    user_input = st.text_input("Scrivi il titolo:", key="film_search")

    if user_input:
        results = searchMovies.autocomplete(user_input)

        if results:
            st.write("### Risultati")
            for r in results:
                # bottone per ogni film
                if st.button(r["title"]):
                    selected_uri = r["uri"]
                    # Variabile di stato che usiamo per segnalare il passaggio alla pagina delle similarità
                    st.session_state.movie_chosen=selected_uri 
                    st.rerun()

        else:
            st.warning("Nessun risultato trovato")

def showSimilarMoviesGui(query, targetUri, nerfedVersion):
    if "movie_index" not in st.session_state:
        st.session_state.movie_index = 0

    movieDictionary, targetMovieTitle = showSimilarMovies.querySimilarities(query, targetUri, nerfedVersion)
    if (len(movieDictionary) == 0):
        showSimilarMovies.show_empty_query()
    chosen_movie_uris = showSimilarMovies.pullKMovies(movieDictionary, 5)
    st.title("🎬 Movie Recommender")
    st.space("small")
    movie = movieDictionary[chosen_movie_uris[st.session_state.movie_index]]

    with st.container(border=True,horizontal_alignment="center"):
        with st.container(border=True, horizontal_alignment="center"):
            st.header(movie["title"],divider="grey")
            st.markdown(f"<p style='margin-top:-10px; font-size:22px;'>{movie['description']}</p>", unsafe_allow_html=True)

            col1, col2 = st.columns(2)

            with col1:
                if (movie["releaseYear"]):
                    st.write("**📅 Anno di rilascio:**", movie["releaseYear"])

                if (movie["runtime"]):
                    st.write(f"**⏱️​ Durata:** {int((movie['runtime'])/60)}min")

                if (movie["avgRating"]):
                    st.write("**⭐ Rating:**", movie["avgRating"])

                if (len(movie["genre"])!=0):
                    st.write("**🎭 Generi:**", ", ".join(movie["genre"]))


            with col2:
                if (len(movie["director"])!=0):
                    st.write("**🎬 Registi:**", ", ".join(movie["director"]))
                    
                if (len(movie["starring"])!=0):
                    st.write("**👥 Cast:**", ", ".join(movie["starring"]))
                
                if (len(movie["tag"])!=0):
                    st.write("**🏷️ Tag:**", ", ".join(movie["tag"]))

            st.divider()

            st.markdown(f"<p style='margin-top:-15px;'><strong>💭​ Rispetto a {targetMovieTitle}, ti consigliamo questo film perché:</strong> {', '.join(movie['similarityExplanation'])}</p>", unsafe_allow_html=True)

            st.markdown("<p style='margin-bottom:-5px;'><strong>🗯️​ Quanto te lo consigliamo?</strong> Più o meno... tanto così!</p>", unsafe_allow_html=True)
            st.progress(movie["similarityToTarget"] / 60)

        with st.container(horizontal=True, horizontal_alignment="distribute", vertical_alignment="center"):

                st.button("⬅️ Precedente", disabled=st.session_state.movie_index == 0, on_click=showSimilarMovies.prev_movie)

                st.write(f"{st.session_state.movie_index + 1} / {len(chosen_movie_uris)}")

                st.button("Successivo ➡️", disabled=st.session_state.movie_index == len(chosen_movie_uris)-1, on_click=showSimilarMovies.next_movie)


    col1, col2, = st.columns([1,1])

    with col1:
        if st.button('Questo film è proprio quello che cercavo!'):
            showSimilarMovies.show_dialog()

    with col2:
        if st.button('​Vorrei un film del genere, ma con qualche differenza...'):
            st.session_state.movie_chosen = chosen_movie_uris[st.session_state.movie_index]
            st.session_state.movie_chosen_attrs = movieDictionary[st.session_state.movie_chosen]
            st.session_state.critique_phase = "true"
            del st.session_state["movie_index"]
            st.rerun()


def main():
    #Inizializza le risorse comuni del sistema (Grafo, matrice delle cooccorrenze)

    g, cooccurrenceMatrix = initSystem()
    searchMovies.setEnvironment(g)
    showSimilarMovies.setEnvironment(g, cooccurrenceMatrix)
    # Se la variabile di stato movie_chosen è assente facciamo partire la ricerca
    if "movie_chosen" not in st.session_state:
        # Inizializziamo la query della richiesta di film a quella su tutto il catalogo
        st.session_state.movie_query = queryAllMovies
        searchMoviesGui()
    # Altrimenti facciamo partire i risultati di similarità
    else:
        # Se la variabile di stato critique_phase è assente mostriamo i risultati
        if "critique_phase" not in st.session_state:
            showSimilarMoviesGui(st.session_state.movie_query, st.session_state.movie_chosen, False)
        # Altrimenti mostriamo la schermata di critique
        else:
            # QUI VA CHIAMATA LA FUNZIONE DELLA GUI DELLA CRITIQUE
            # ALLA FINE DOVREBBE SETTARE LA VARIABILE DI STATO movie_query ALLA QUERY FORMATA DAI RISULTATI
            # I CONTENUTI IN BASE A CUI GENERARE LA SCHERMATA DI CRITIQUE SONO DENTRO QUESTO DICTIONARY CHE ORA STAMPO
            critiqueGui.critiqueGui()
            


# Main
if __name__ == '__main__':
    main()