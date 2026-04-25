import csv
import sys
import requests
import json
import pandas as pd
from rdflib import Graph, URIRef, Literal, Namespace, RDFS, XSD
from decimal import Decimal
import statistics
import time
import math
import cooccurrenceMatrix as cm
import similarityFunctions as simFuncs
import numpy as np
import streamlit as st

# !!! APPROCCIO SCARTATO, TENUTO SOLO IN CASO PER LA DOCUMENTAZIONE !!!

# qBaseAttributes = """
#     PREFIX dbo: <http://dbpedia.org/ontology/>
#     PREFIX dbp: <http://dbpedia.org/property/>
#     SELECT ?title ?description ?runtime ?avgRating ?releaseYear
#             WHERE {{
#             <{movieUriV}> rdfs:label ?title .
#             OPTIONAL {{ <{movieUriV}> dbo:description ?description . }}
#             OPTIONAL {{ <{movieUriV}> dbo:runtime ?runtime . }}
#             OPTIONAL {{ <{movieUriV}> dbo:avgRating ?avgRating . }}
#             OPTIONAL {{ <{movieUriV}> dbo:releaseYear ?releaseYear . }}
#             }}
#     """

# qStarring = """
#         PREFIX dbo: <http://dbpedia.org/ontology/>
#         PREFIX dbp: <http://dbpedia.org/property/>
#         SELECT ?starring
#                 WHERE {{
#                 <{movieUriV}> dbo:starring ?starring .
#                 }}
#         """

# qTags = """
#         PREFIX dbo: <http://dbpedia.org/ontology/>
#         PREFIX dbp: <http://dbpedia.org/property/>
#         SELECT ?tag
#                 WHERE {{
#                 <{movieUriV}> dbo:tag ?tag .
#                 }}
#         """

# qGenres = """
#         PREFIX dbo: <http://dbpedia.org/ontology/>
#         PREFIX dbp: <http://dbpedia.org/property/>
#         SELECT ?genre
#                 WHERE {{
#                 <{movieUriV}> dbo:genre ?genre .
#                 }}
#         """

# qDirectors = """
#         PREFIX dbo: <http://dbpedia.org/ontology/>
#         PREFIX dbp: <http://dbpedia.org/property/>
#         SELECT ?director
#                 WHERE {{
#                 <{movieUriV}> dbo:director ?director .
#                 }}
#         """

# def retrieveAttributesOfMovie(movieUri, graph, dict):
#     dict[str(movieUri)] = {}
#     dict[str(movieUri)]["director"] = []
#     dict[str(movieUri)]["genre"] = []
#     dict[str(movieUri)]["tag"] = []
#     dict[str(movieUri)]["starring"] = []

#     for row in graph.query(qBaseAttributes.format(movieUriV = movieUri)):
#         dict[str(movieUri)]["title"] = str(row.title)
#         dict[str(movieUri)]["description"] = str(row.description) if row.description is not None else None
#         dict[str(movieUri)]["runtime"] = float(row.runtime) if row.runtime is not None else None
#         try: #Alcuni anni non erano presenti nel csv e questo ha portato a parsing scorretto
#             dict[str(movieUri)]["releaseYear"] = int(row.releaseYear) if row.releaseYear is not None else None
#         except:
#             dict[str(movieUri)]["releaseYear"] = None
#         dict[str(movieUri)]["avgRating"] = float(row.avgRating) if row.avgRating is not None else None
        
#     for row in graph.query(qStarring.format(movieUriV = movieUri)):
#         dict[str(movieUri)]["starring"].append(str(row.starring))
        
#     for row in graph.query(qDirectors.format(movieUriV = movieUri)):
#         dict[str(movieUri)]["director"].append(str(row.director))
        
#     for row in graph.query(qTags.format(movieUriV = movieUri)):
#         dict[str(movieUri)]["tag"].append(str(row.tag))
        
#     for row in graph.query(qGenres.format(movieUriV = movieUri)):
#         dict[str(movieUri)]["genre"].append(str(row.genre))

# def createDictionaryFromQuery(queryString, graph, label):
#     retDict = {}
#     timeS = time.time()
#     print(timeS)
#     results = graph.query(queryString)
#     for row in results:
#         retrieveAttributesOfMovie(row.movie, graph, retDict)
#     timeE = time.time()
#     print(timeE)
#     elapsedTime = timeE-timeS
#     print("Query con riga breve " + label + ", elapsed time: " + str(elapsedTime))
#     return retDict

# q1 = """
#     PREFIX dbo: <http://dbpedia.org/ontology/>
#     PREFIX dbp: <http://dbpedia.org/property/>
#     SELECT DISTINCT ?movie
#     WHERE {
#         ?movie rdfs:label ?title .
#     }
#     """
#     #Separa la query nei vari attributi

# q2 = """
#     PREFIX dbo: <http://dbpedia.org/ontology/>
#     PREFIX dbp: <http://dbpedia.org/property/>
#     SELECT DISTINCT ?movie
#     WHERE {
#         ?movie rdfs:label "Pocahontas (1995)" .
#     }
#     """
#     #Separa la query nei vari attributi

# q2Ext = """
#     PREFIX dbo: <http://dbpedia.org/ontology/>
#     PREFIX dbp: <http://dbpedia.org/property/>
#     SELECT DISTINCT ?movie ?title ?description ?avgRating ?runtime ?releaseYear ?genre ?director ?starring ?tag
#     WHERE {
#         ?movie rdfs:label "Pocahontas (1995)" .
#         OPTIONAL { ?movie dbo:description ?description . }
#         OPTIONAL { ?movie dbo:avgRating ?avgRating . }
#         OPTIONAL { ?movie dbo:runtime ?runtime . }
#         OPTIONAL { ?movie dbo:releaseYear ?releaseYear . }
#         OPTIONAL { ?movie dbo:genre ?genre . }
#         OPTIONAL { ?movie dbo:director ?director . }
#         OPTIONAL { ?movie dbo:starring ?starring . }
#         OPTIONAL { ?movie dbo:tag ?tag . }
#         }    
#     """


# !!! - !!!

SIMILARITY_WEIGHTS_SUM = 12

def computeAverageSimilarityToTarget(movieDictionary, chosenMovieUris):
    sum = 0
    for uri in chosenMovieUris:
        sum += movieDictionary[uri]["similarityToTargetWithoutRating"]/SIMILARITY_WEIGHTS_SUM
    return sum/len(chosenMovieUris)

def computeIntraListDiversity(movieDictionary, chosenMoviesUris):
    sum = 0
    n = len(chosenMoviesUris)
    for i in range(n):
        for j in range(n):
            if i != j:
                sum+=1-computeSimilarityToTarget(movieDictionary, chosenMoviesUris[i], chosenMoviesUris[j])/SIMILARITY_WEIGHTS_SUM
    return sum/(n*(n-1))

def computeSerendipity(chosenMovieUris, topUris):
    diff = set(chosenMovieUris) - set(topUris)
    return len(diff)/len(chosenMovieUris)

def setEnvironment(graph, genreMatrix):
    global g
    global genreCooccurrenceMatrix
    g = graph
    genreCooccurrenceMatrix = genreMatrix

def computeSoftmaxDenominator(movieDictionary, alpha):
    totalSum = 0
    for movieData in movieDictionary.values():
        totalSum += math.exp(alpha*movieData["similarityToTarget"])
    return totalSum

def fillArmProbability(movieDictionary, alpha, softmaxDenominator):
    for movieData in movieDictionary.values():
        movieData["armProbability"] = math.exp(alpha*movieData["similarityToTarget"])/softmaxDenominator

def getRecommendationExplanation(index, myMovie, targetMovie):
    match index:
        case 0: # Genere
            return "è di un genere simile"

        case 1: # Registi
            directorIntersection = myMovie["director"] & targetMovie["director"]
            result = []
            for actorUri in directorIntersection:
                rIndex = actorUri.rfind('/')
                result.append(actorUri[rIndex+1:].replace('_', ' '))
            return "è diretto da registi in comune (" + " ,".join(result) + ")"

        case 2: # Attori
            starringIntersection = myMovie["starring"] & targetMovie["starring"]
            result = []
            for actorUri in starringIntersection:
                rIndex = actorUri.rfind('/')
                result.append(actorUri[rIndex+1:].replace('_', ' '))
            return "presenta degli attori in comune (" + " ,".join(result) + ")"

        case 3: # Anno
            return "è uscito nello stesso periodo"

        case 4: # Durata
            return "ha una durata simile"

        case 5: # Tag
            tagIntersection = myMovie["tag"] & targetMovie["tag"]
            return "è stato taggato analogamente (" + " ,".join(tagIntersection) + ")"
        

def computeSimilarityToTarget(movieDictionary, movieUri, targetMovieUri):
    myMovie = movieDictionary[movieUri]
    targetMovie = movieDictionary[targetMovieUri]

    # Genere | Registi | Attori | Anno | Durata | Tag
    similarityWeights = [3, 2.5, 2, 1, 0.5, 3]

    genreSim = simFuncs.genreListSimilarity(myMovie["genre"], targetMovie["genre"], genreCooccurrenceMatrix)
    starringSim = simFuncs.jaccardSimilarity(myMovie["starring"], targetMovie["starring"], 0.5)
    directorSim = simFuncs.jaccardSimilarity(myMovie["director"], targetMovie["director"], 0.5)
    yearSim = simFuncs.exponentialDecaySimilarity(myMovie["releaseYear"], targetMovie["releaseYear"], 0.15)
    runtimeSim = simFuncs.exponentialDecaySimilarity(myMovie["runtime"], targetMovie["runtime"], (1.0/1050.0))
    tagSim = simFuncs.jaccardSimilarity(myMovie["tag"], targetMovie["tag"], 0.5)
    similarityValues = [genreSim, directorSim, starringSim, yearSim, runtimeSim, tagSim]

    myMovie["similarityExplanation"] = []
    top3SimIndexes = sorted([0, 1, 2, 3, 4, 5], key=lambda i:similarityValues[i], reverse=True)[0:3]
    for i in top3SimIndexes:
        if (similarityValues[i] != 0): # Anche se questo è uno dei 3 valori id similarità più alto, se è nullo non lo consideriamo
            myMovie["similarityExplanation"].append(getRecommendationExplanation(i, myMovie, targetMovie))
    return np.dot(similarityWeights, similarityValues)

def retrieveAttributesOfMovie(row, retDict, targetMovieUri):
    
    movieUriString = str(row.movie)
    # Se nel dizionario NON c'è già una chiave per il film associato a questa riga, devo creare un nuovo dizionario per il film
    if (movieUriString not in retDict):
        retDict[movieUriString] = {}
        retDict[movieUriString]["director"] = set()
        retDict[movieUriString]["genre"] = set()
        retDict[movieUriString]["tag"] = set()
        retDict[movieUriString]["starring"] = set()

    retDict[movieUriString]["title"] = str(row.title)
    retDict[movieUriString]["description"] = str(row.description) if row.description is not None else None
    retDict[movieUriString]["runtime"] = float(row.runtime) if row.runtime is not None else None

    try: #Alcuni anni non erano presenti nel csv e questo ha portato a parsing scorretto
        retDict[movieUriString]["releaseYear"] = int(row.releaseYear) if row.releaseYear is not None else None
    except:
        retDict[movieUriString]["releaseYear"] = None
        
    # Se il film è unrated, lo consideriamo pari ad essere votato 0 (Sarà spinto in fondo nell'ordinamento dei risultati)
    retDict[movieUriString]["avgRating"] = float(row.avgRating) if row.avgRating is not None else 0
    if row.genre is not None:
        retDict[movieUriString]["genre"].add(str(row.genre))
    if row.director is not None:
        retDict[movieUriString]["director"].add(str(row.director))
    if row.tag is not None:
        retDict[movieUriString]["tag"].add(str(row.tag))
    if row.starring is not None:
        retDict[movieUriString]["starring"].add(str(row.starring))

    # Anche se alla riga attuale i dati del film non sono ancora completi, la similarità sarà sovrascritta nelle prossime iterazioni
    # A fine addQueryContentToDictionary() la similarity risulterà calcolata correttamente
    similarityToTarget = computeSimilarityToTarget(retDict, movieUriString, targetMovieUri)
    retDict[movieUriString]["similarityToTargetWithoutRating"] = similarityToTarget
    retDict[movieUriString]["similarityToTarget"] = similarityToTarget*retDict[movieUriString]["avgRating"]

def addQueryContentToDictionary(queryString, graph, retDict, targetMovieUri):
    results = graph.query(queryString)
    for row in results:
        retrieveAttributesOfMovie(row, retDict, targetMovieUri)

@st.cache_resource
def querySimilarities(query, targetMovieUri, nerfedVersion):
    movieDictionary = {}
    myMovieUri1 = "http://dbpedia.org/resource/The_Dark_Knight_Rises"
    myMovieUri2 = "http://dbpedia.org/resource/A_Goofy_Movie"
    myMovieUri3 = "http://dbpedia.org/resource/Pocahontas_II:_Journey_to_a_New_World"
    myMovieUri4 = "http://dbpedia.org/resource/Point_Break"
    myMovieUri5 = "http://dbpedia.org/resource/Public_Enemies_(2009_film)"
    alpha = 1
    # Dobbiamo riempire prima i dati riguardanti il target, in modo da poter calcolare man mano la similarità
    addQueryContentToDictionary(queryTargetMovie.format(targetUri = targetMovieUri), g, movieDictionary, targetMovieUri)
    if nerfedVersion:
        addQueryContentToDictionary(queryTargetMovie.format(targetUri = myMovieUri1), g, movieDictionary, targetMovieUri)
        addQueryContentToDictionary(queryTargetMovie.format(targetUri = myMovieUri2), g, movieDictionary, targetMovieUri)
        addQueryContentToDictionary(queryTargetMovie.format(targetUri = myMovieUri3), g, movieDictionary, targetMovieUri)
        addQueryContentToDictionary(queryTargetMovie.format(targetUri = myMovieUri4), g, movieDictionary, targetMovieUri)
        addQueryContentToDictionary(queryTargetMovie.format(targetUri = myMovieUri5), g, movieDictionary, targetMovieUri)
    else:
        addQueryContentToDictionary(query, g, movieDictionary, targetMovieUri)
    targetMovieTitle = movieDictionary[targetMovieUri]["title"]
    movieDictionary.pop(targetMovieUri)
    softmaxDenominator = computeSoftmaxDenominator(movieDictionary, alpha)
    fillArmProbability(movieDictionary, alpha, softmaxDenominator)
    print("QUERY SIMILARITIES")
    return movieDictionary, targetMovieTitle

@st.cache_resource
def pullKMovies(movieDictionary, k):
    movie_uris = list(movieDictionary.keys())
    weights = [movieDictionary[m]["armProbability"] for m in movie_uris]
    best_movie_uris = sorted(movie_uris, key=lambda uri:movieDictionary[uri]["similarityToTarget"], reverse=True)[:k]
    chosen_movie_uris = sorted(np.random.choice(movie_uris, p=weights, size=min(k, len(movie_uris)), replace=False), key=lambda uri:movieDictionary[uri]["similarityToTarget"], reverse=True)
    print("Sono stati scelti in ordine: " + str([movieDictionary[m]["title"] for m in chosen_movie_uris]))
    print("I migliori sono in ordine: " + str([movieDictionary[m]["title"] for m in best_movie_uris]))

    print ("ACCURACY: " + str(computeAverageSimilarityToTarget(movieDictionary, chosen_movie_uris)))
    print("DIVERSITY: " + str(computeIntraListDiversity(movieDictionary, chosen_movie_uris)))
    print("SERENDIPITY: " + str(computeSerendipity(chosen_movie_uris, best_movie_uris)))
    return chosen_movie_uris


queryTargetMovie = """
    PREFIX dbo: <http://dbpedia.org/ontology/>
    PREFIX dbp: <http://dbpedia.org/property/>
    SELECT DISTINCT ?movie ?title ?description ?avgRating ?runtime ?releaseYear ?genre ?director ?starring ?tag
    WHERE {{
        <{targetUri}> rdfs:label ?title .
        ?movie rdfs:label ?title .
        OPTIONAL {{ <{targetUri}> dbo:description ?description . }}
        OPTIONAL {{ <{targetUri}> dbo:avgRating ?avgRating . }}
        OPTIONAL {{ <{targetUri}> dbo:runtime ?runtime . }}
        OPTIONAL {{ <{targetUri}> dbo:releaseYear ?releaseYear . }}
        OPTIONAL {{ <{targetUri}> dbo:genre ?genre . }}
        OPTIONAL {{ <{targetUri}> dbo:director ?director . }}
        OPTIONAL {{ <{targetUri}> dbo:starring ?starring . }}
        OPTIONAL {{ <{targetUri}> dbo:tag ?tag . }}
        }}    
    """

def next_movie():
    st.session_state.movie_index = int(st.session_state.movie_index)+1

def prev_movie():
    st.session_state.movie_index = int(st.session_state.movie_index)-1

@st.dialog("Successo!")
def show_dialog():
    st.write("Speriamo il film consigliato ti piaccia! 😃​")
    if st.button("Torna all'inizio"):
        del st.session_state["movie_index"]
        del st.session_state["movie_chosen"]
        st.rerun()

@st.dialog("Peccato!")
def show_empty_query():
    st.write("La tua ricerca era troppo specifica! 😢​​")
    if st.button("Torna all'inizio"):
        del st.session_state["movie_index"]
        del st.session_state["movie_chosen"]
        st.rerun()
