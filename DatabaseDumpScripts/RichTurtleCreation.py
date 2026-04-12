import csv
import sys
import requests
import json
import pandas as pd
from rdflib import Graph, URIRef, Literal, Namespace, RDFS, XSD
from decimal import Decimal
import statistics

def getCleanDataFromLabel(longName):
    #Rimuovo le virgolette se ci sono
    movieName=str(movieLongName).strip('"')
    #Isolo l'anno di pubblicazione
    rYear = movieName.rfind(')')
    lYear = movieName.rfind('(')
    movieYear = movieName[lYear+1:rYear]
    #Rimuovo l'anno dal nome
    movieName = movieName[:lYear]
    #Rimuovo eventuali altre parentesi contenenti il titolo tradotto
    lTranslation = movieName.find('(')
    movieName = movieName[:lTranslation]
    #Anticipo l'articolo posto dopo la virgola (se c'è una virgola)
    commaIndex = movieName.rfind(',')
    if commaIndex != -1:
        movieName = movieName[commaIndex+1:]+" "+movieName[:commaIndex]
    #Pulisco da spazi
    movieName = movieName.strip()
    return movieName, movieYear
  
def addToGraphFromRow(subjectUri, objectValue, predicateStr, graph):
    s = subjectUri
    o_val = objectValue
    # Se questo campo è assente nell'estrazione di DBPedia non aggiungiamo la tripla
    if o_val is None:
        return
    p = URIRef(predicateStr)
    graph.add((s,p,o_val))

def removeFromGraph(subjectUri, objectValue, predicateStr, graph):
    s = subjectUri
    o_val = objectValue
    # Se questo campo è assente nell'estrazione di DBPedia non aggiungiamo la tripla
    if o_val is None:
        return
    p = URIRef(predicateStr)
    graph.remove((s,p,o_val))

def cleanAllLabels(graph, newgraph):
    # Rimuovo tutte le vecchie label
    queryLabels = """
                SELECT DISTINCT ?movie ?title
                WHERE {
                ?movie rdfs:label ?title .
                }
                """
    for row in graph.query(queryLabels):
        removeFromGraph(row.movie, row.title, RDFS.label, graph)

    for row in newgraph.query(queryLabels):
        addToGraphFromRow(row.movie, row.title, RDFS.label, graph)

def addToGraphNewProperty(subjectUri, objectString, predicateStr, graph):
    s = subjectUri 
    o_val = objectString
    if isinstance(o_val, str):
        if o_val.isdigit():
            o_val = int(o_val)
        else:
            try:
                o_val = float(o_val)
            except:
                pass

    if (isinstance(o_val,float)):
        o = Literal(Decimal(o_val).quantize(Decimal("0.01")))
    else:
        o = Literal(o_val)
    p = URIRef(predicateStr)
    graph.add((s,p,o))

# Grafo costruito dai file Turtle ottenuti da DBPedia, che arricchiamo
g = Graph()
DBO = Namespace('http://dbpedia.org/ontology/')
g.bind('dbo', DBO)
g.bind('dbp', Namespace('http://dbpedia.org/property/'))
g.parse("db_dump_1.ttl",format='ttl')
g.parse("db_dump_2.ttl",format='ttl')

gLabels = Graph()
gLabels.bind('dbo', DBO)
gLabels.bind('dbp', Namespace('http://dbpedia.org/property/'))

moviesFile = open("MovieLensSmall/movies.csv", encoding="utf8")
counter = 0
try:
    moviecsvreader = csv.reader(moviesFile, delimiter=",")
    # Scorro tutti gli elementi del csv princiaple per costruire le strutture contenenti tag e ratings
    tags = {}
    ratings = {}
    next(moviecsvreader, None)
    for movieId, movieLongName, genresString in moviecsvreader:
        tags[str(movieId)] = []
        ratings[str(movieId)] = []

    # Ricavo la lista di tag
    with open("MovieLensSmall/tags.csv", encoding="utf8") as tagsfile:
        tagsreader = csv.reader(tagsfile, delimiter=",")
        
        next(tagsreader, None)
        for userId, movieId, tag, timestamp in tagsreader:
            tags[str(movieId)].append(str(tag).strip())

    # Ricavo la lista di ratings
    with open("MovieLensSmall/ratings.csv", encoding="utf8") as ratingsfile:
        ratingsreader = csv.reader(ratingsfile, delimiter=",")

        next(ratingsreader, None)
        for userId, movieId, rating, timestamp in ratingsreader:
            ratings[str(movieId)].append(float(str(rating).strip()))

    # Riporto il puntatore all'inizio del file per rileggere i film
    moviesFile.seek(0)
    next(moviecsvreader, None)
    for movieId, movieLongName, genresString in moviecsvreader:
        counter += 1
        genreList = genresString.split('|')
        movieName, movieYear = getCleanDataFromLabel(movieLongName)

        print(movieId)

        # Ora che ho raccolto tutti i dati locali, per ogni film cerco su dbpedia i dati,
        # provando come label il nome pulito e anche una versione alternativa con anno incluso
        startq1 = """
            PREFIX dbo: <http://dbpedia.org/ontology/>
            PREFIX dbp: <http://dbpedia.org/property/>
            SELECT DISTINCT ?movie ?title
            WHERE {
            ?movie rdfs:label ?title .
            """
            
        endq1 = """
            FILTER (STR(?title) = \"\"\"{moviename} ({movieyear})\"\"\" || STR(?title) = \"\"\"{moviename}\"\"\")
            """.format(moviename=movieName, movieyear=movieYear)
        q1 = startq1 + endq1 + "}"

        resultRows = g.query(q1)

        # Se il film è stato trovato salvo l'URI del film prendendolo dalla prima riga ricavata
        # altrimenti invento un URI (Tanto per ritrovare i film utilizzerò le label pulite ottenute in precedenza)
        if resultRows:
            for row in resultRows:
                currMovieURI = row.movie
        else:
            # URI inventato fatto di caratteri safe
            currMovieURI = URIRef("http://dbpedia.org/resource/movieuri"+str(counter)+'/')
            
        # La label la aggiungo in un grafo a parte, per poi alla fine fare pulizia di tutte le label ed aggiungere solo quelle pulite
        # Questo perché DBPedia soffre di dati sporchi sulle label, che contagiano il risultato desiderato delle query
        addToGraphNewProperty(currMovieURI, movieName + " (" + str(movieYear) + ")", RDFS.label, gLabels) 
        # Aggiungo i dati presi dal csv  
        addToGraphNewProperty(currMovieURI, movieYear, DBO.releaseYear, g) # anno
        for genre in genreList:
            if (genre != "(no genres listed)"):
                addToGraphNewProperty(currMovieURI, genre, DBO.genre, g) # generi se presenti
        for tag in tags[str(movieId)]:
            addToGraphNewProperty(currMovieURI, tag, DBO.tag, g) # tag se presenti
        if (ratings[str(movieId)]):
            avgRating = statistics.mean(ratings[str(movieId)])
            addToGraphNewProperty(currMovieURI, round(avgRating,2), DBO.avgRating, g) # rating medio se presenti ratings

        if (counter % 1000 == 0):
            g.serialize(destination="output.ttl", format="turtle")
    
    cleanAllLabels(g, gLabels)
    g.serialize(destination="output.ttl", format="turtle")
        

finally:
    moviesFile.close()
        

        

