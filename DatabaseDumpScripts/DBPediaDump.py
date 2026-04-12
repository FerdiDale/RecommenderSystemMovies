import csv
import sys
import requests
import json
import pandas as pd
from rdflib import Graph, URIRef, Literal, Namespace, RDFS
from decimal import Decimal
import itertools

def query(q, epr, f='application/json'):
    try:
        params = {'query': q}
        resp = requests.get(epr, params=params, headers={'Accept': f})
        return resp.text
    except Exception as e:
        print(e, file=sys.stdout)
        raise

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
  
def addToGraphFromRow(row, subjectKey, objectKey, predicateStr, graph):
    s = URIRef(row[subjectKey]['value'])
    try:   
        o_val = row[objectKey]['value']
    # Se questo campo è assente in dbpedia non aggiungiamo la tripla
    except:
        return
    isfloat = False
    if o_val.isdigit():
        o_val = int(o_val)
    else:
        try:
            o_val = float(o_val)
            isfloat = True
        except:
            pass    
    if row[objectKey]['type'] == 'uri':
        o = URIRef(o_val)
    else:
        if (isfloat):
            o = Literal(Decimal(o_val))
        else:
            o = Literal(o_val)
    p = URIRef(predicateStr)
    graph.add((s,p,o))

def addToGraphNewProperty(subjectUri, objectString, predicateStr, graph):
    s = subjectUri 
    o_val = objectString
    isfloat = False
    if o_val.isdigit():
        o_val = int(o_val)
    else:
        try:
            o_val = float(o_val)
            isfloat = True
        except:
            pass    
    if (isfloat):
        o = Literal(Decimal(o_val))
    else:
        o = Literal(o_val)
    p = URIRef(predicateStr)
    graph.add((s,p,o))

g = Graph()
DBO = Namespace('http://dbpedia.org/ontology/')
g.bind('dbo', DBO)
g.bind('dbp', Namespace('http://dbpedia.org/property/'))
moviesFile = open("MovieLensSmall/movies.csv", encoding="utf8")
try:
    startq1 = """
            PREFIX dbo: <http://dbpedia.org/ontology/>
            PREFIX dbp: <http://dbpedia.org/property/>
            SELECT DISTINCT ?movie ?title ?description ?director MIN(?runtime) AS ?minruntime ?starring 
            WHERE {
            ?movie a dbo:Film ;
            rdfs:label ?title .
            OPTIONAL { ?movie dbo:description ?description . }
            OPTIONAL { ?movie dbo:director ?director . }
            OPTIONAL { ?movie dbo:runtime ?runtime . }
            OPTIONAL { ?movie dbo:starring ?starring . }
            """
            
    filterString = "FILTER ("

    endq1 = """
            FILTER(LANG(?description) = "en")
            }
            """
            
    moviecsvreader = csv.reader(moviesFile, delimiter=",")
    next(moviecsvreader, None)

    counter = 0
    moviesTotNumber = 9742 # In tutto sono 9742 film nel csv
    startingIteration = True

    while (counter < moviesTotNumber):
        if startingIteration:
            iteratorSlice = itertools.islice(moviecsvreader, counter, counter+50)
        else:
            iteratorSlice = itertools.islice(moviecsvreader, 50)
        filterString = "FILTER ("
        for movieId, movieLongName, genresString in iteratorSlice: # Non riesce a reggere una richiesta e una risposta su più di 50 elementi
            counter+=1
            movieName, movieYear = getCleanDataFromLabel(movieLongName)


            # Ora che ho raccolto tutti i dati locali, per ogni film cerco su dbpedia i dati,
            # provando come label il nome pulito e anche una versione alternativa con anno incluso
            #(Rimpiazzo ' e " che altrimenti causano problemi di compilazione nella query)
            filterString += "STR(?title) = \"{moviename} ({movieyear})\" || STR(?title) = \"{moviename}\" || ".format(moviename=movieName.replace("'","\\'").replace('"','\\"'), movieyear=movieYear)
            # Se il film è stato trovato salvo l'URI del film prendendolo dalla prima riga ricavata
            # altrimenti invento un URI (Tanto per ritrovare i film utilizzerò le label pulite ottenute in precedenza)
        
        if (startingIteration):
            startingIteration = False

        filterString = filterString.rstrip().rstrip('|').rstrip('|')
        filterString += " )"
                
        q1 = startq1 + filterString + endq1
        
        results = json.loads(query(q1, "http://dbpedia.org/sparql"))

        resultRows = results['results']['bindings']
        if resultRows:
            for row in (resultRows):
                print(row)
                print("\n")
                addToGraphFromRow(row, 'movie', 'title', RDFS.label, g)
                addToGraphFromRow(row, 'movie', 'director', DBO.director, g)
                addToGraphFromRow(row, 'movie', 'starring', DBO.starring, g)
                addToGraphFromRow(row, 'movie', 'minruntime', DBO.runtime, g)
                addToGraphFromRow(row, 'movie', 'description', DBO.description, g)

        g.serialize(destination="basedb"+str(counter)+".ttl", format="turtle")

finally:
    moviesFile.close()
        

        

