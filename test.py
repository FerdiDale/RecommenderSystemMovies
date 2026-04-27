import streamlit as st
import searchMovies
import cooccurrenceMatrix
import showSimilarMovies
import critiqueQuery
import pandas as pd
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

def pullSimilarMovies(query, targetUri, softmaxAlpha):

    movieDictionary, targetMovieTitle = showSimilarMovies.querySimilarities(query, targetUri, False, softmaxAlpha)
    if (len(movieDictionary) == 0):

        return 0, 0, 0, 0 # DA CAMBIARE?

    chosen_movie_uris, accuracy, diversity, serendipity, nResults = showSimilarMovies.pullKMovies(movieDictionary, 5, True)
    return accuracy, diversity, serendipity, nResults

def extractCritiqueFromAttributeList(attributeStrings, targetMovieUri, movieDictionary):
    critique = {}
    critique["genre"] = []
    critique["starring"] = []
    critique["director"] = []
    critique["tag"] = []
    for attr in attributeStrings:
        critique[attr] = movieDictionary[targetMovieUri][attr]

    return critiqueQuery.build_critique_query(0, critique["genre"], critique["tag"], "Nessuna preferenza", critique["director"], critique["starring"], "Nessuna preferenza", 0)

def main():
    #Inizializza le risorse comuni del sistema (Grafo, matrice delle cooccorrenze)
    counter = 0
    g, cooccurrenceMatrix = initSystem()
    searchMovies.setEnvironment(g)
    showSimilarMovies.setEnvironment(g, cooccurrenceMatrix)
    targetUriValues = ["http://dbpedia.org/resource/Interstellar_(film)", "http://dbpedia.org/resource/Toy_Story_2", "http://dbpedia.org/resource/Mean_Girls", "http://dbpedia.org/resource/The_Usual_Suspects", "http://dbpedia.org/resource/The_Shape_of_Water", "http://dbpedia.org/resource/Fantasia_(1940_film)", "http://dbpedia.org/resource/Shakespeare_in_Love", "http://dbpedia.org/resource/The_Shining_(film)", "http://dbpedia.org/resource/The_Avengers_(2012_film)", "http://dbpedia.org/resource/Harry_Potter_and_the_Philosopher's_Stone_(film)"]
    critiqueAttributesListValues = [[],["genre"],["tag"],["starring"],["director"],["genre", "tag"],["starring", "director"],["genre", "tag", "starring", "director"]]
    softmaxAlphaValues = [0.5, 1, 1.5]
    results = []
    for targetMovie in targetUriValues:

        # Devo salvare il film target a parte per evitare di perderne i dati (E' rimosso dai risultati per evitare di guastare le probabilità che siano scelti altri film)
        targetMovieDict = {}
        showSimilarMovies.addQueryContentToDictionary(showSimilarMovies.queryTargetMovie.format(targetUri = targetMovie), g, targetMovieDict, targetMovie)

        for alphaVal in softmaxAlphaValues:
            for critiqueList in critiqueAttributesListValues:
                #Caso della query senza critique
                if len(critiqueList) == 0:
                    movie_query = queryAllMovies
                else:
                    movie_query = extractCritiqueFromAttributeList(critiqueList, targetMovie, targetMovieDict)
                accuracy, diversity, serendipity, nResults = pullSimilarMovies(movie_query, targetMovie, alphaVal)
                results.append({
                    "movie_title": targetMovieDict[targetMovie]["title"],
                    "critique_attributes": critiqueList,
                    "softmaxAlpha": alphaVal,
                    "accuracy": accuracy,
                    "diversity": diversity,
                    "serendipity": serendipity,
                    "n_results": nResults
                })
        
        print("\n\n\n")
        print("FINE STUDIO PER FILM " + targetMovie)
        print("\n\n\n")

        df = pd.DataFrame(results)
        df.to_csv("results" + str(counter) + ".csv", sep=";", index=False)    
        counter+=1
    
    df = pd.DataFrame(results)
    df.to_csv("totresults.csv", sep=";", index=False)            


# Main
if __name__ == '__main__':
    main()