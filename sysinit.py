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
        o = Literal(Decimal(o_val))
    else:
        o = Literal(o_val)
    p = URIRef(predicateStr)
    graph.add((s,p,o))

# Grafo input costruito dai file Turtle ottenuti da DBPedia
g = Graph()
DBO = Namespace('http://dbpedia.org/ontology/')
g.bind('dbo', DBO)
g.bind('dbp', Namespace('http://dbpedia.org/property/'))
g.parse("db_dump_1.ttl",format='ttl')
g.parse("db_dump_2.ttl",format='ttl')

# Grafo output, arricchimento di g (con ridefinizione delle label)
gOut = Graph()
gOut.bind('dbo', DBO)
gOut.bind('dbp', Namespace('http://dbpedia.org/property/'))

moviesFile = open("MovieLensSmall/movies.csv", encoding="utf8")
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
        genreList = genresString.split('|')
        movieName, movieYear = getCleanDataFromLabel(movieLongName)
        if (movieName == "Pocahontas"):
            print(movieId)

            # Ora che ho raccolto tutti i dati locali, per ogni film cerco su dbpedia i dati,
            # provando come label il nome pulito e anche una versione alternativa con anno incluso
            startq1 = """
                PREFIX dbo: <http://dbpedia.org/ontology/>
                PREFIX dbp: <http://dbpedia.org/property/>
                SELECT DISTINCT ?movie ?description ?director ?runtime ?starring 
                WHERE {
                ?movie rdfs:label ?title .
                OPTIONAL { ?movie dbo:description ?description . }
                OPTIONAL { ?movie dbo:director ?director . }
                OPTIONAL { ?movie dbo:runtime ?runtime . }
                OPTIONAL { ?movie dbo:starring ?starring . }
                """
                
            #(Rimpiazzo ' e " che altrimenti causano problemi di compilazione nella query)
            endq1 = """
                FILTER (STR(?title) = "{moviename} ({movieyear})" || STR(?title) = "{moviename}")
                """.format(moviename=movieName.replace("'","\\'").replace('"','\\"'), movieyear=movieYear)
            q1 = startq1 + endq1 + "}"

            resultRows = g.query(q1)

    #     # Se il film è stato trovato salvo l'URI del film prendendolo dalla prima riga ricavata
    #     # altrimenti invento un URI (Tanto per ritrovare i film utilizzerò le label pulite ottenute in precedenza)
            if resultRows:
                for row in resultRows:
                    currMovieURI = row.movie
                    addToGraphFromRow(currMovieURI, row.director, DBO.director, gOut)
                    addToGraphFromRow(currMovieURI, row.starring, DBO.starring, gOut)
                    addToGraphFromRow(currMovieURI, row.runtime, DBO.runtime, gOut)
                    addToGraphFromRow(currMovieURI, row.description, DBO.description, gOut)
            else:
                # URI inventato fatto da nome pulito del film + anno tra parentesi con gli spazi sostituiti con underscore
                currMovieURI = URIRef("http://dbpedia.org/resource/"+movieName.replace(' ','_')+'_('+str(movieYear)+')/')
    #     # Aggiungo i dati presi dal csv  
            addToGraphNewProperty(currMovieURI, movieName, RDFS.label, gOut)
            addToGraphNewProperty(currMovieURI, movieYear, DBO.releaseYear, gOut)
            for genre in genreList:
                if (genre != "(no genres listed)"):
                    addToGraphNewProperty(currMovieURI, genre, DBO.genre, gOut)
            for tag in tags[str(movieId)]:
                addToGraphNewProperty(currMovieURI, tag, DBO.tag, gOut)
            nRatings = 0
            sumRatings = 0
            for rating in ratings[str(movieId)]:
                nRatings += 1
                sumRatings += rating
                addToGraphNewProperty(currMovieURI, rating, DBO.rating, gOut)
            print(sumRatings/nRatings)
            print(statistics.mean(ratings[str(movieId)]))

    gOut.serialize(destination="output.ttl", format="turtle")

finally:
    moviesFile.close()
        

        

