import pandas as pd
import numpy as np
import math

def genreSimilarity(genre1, genre2, cooccurrence_df):
    vector1 = cooccurrence_df[genre1].to_numpy()
    vector2 = cooccurrence_df[genre2].to_numpy()
    # Cosine similarity tra le righe associate ai generi nella matrice delle co-occorrenze
    return np.dot(vector1,vector2)/(np.linalg.norm(vector1)*np.linalg.norm(vector2))

def genreListSimilarity(genreList1, genreList2, cooccurrence_df):
    # Se uno dei due film non ha generi associati, ritorniamo un valore nullo
    if (len(genreList1) == 0 or len(genreList2) == 0):
        return 0

    # Definiamo la similarità di un genere myGenre ad un insieme di generi Target come
    # il massimo della similarità tra myGenre e uno dei generi contenuti in Target
    # La similarità dei generi un film al target sarà quindi la media delle similarità dei generi all'insieme di generi del film target, in [0,1]

    similaritySum = 0
    for genre1 in genreList1:
        currGenreSimilarity = 0
        for genre2 in genreList2:
            currGenreSimilarity = max(currGenreSimilarity, genreSimilarity(genre1, genre2, cooccurrence_df))
        similaritySum += currGenreSimilarity
    return similaritySum/len(genreList1)

def jaccardSimilarity(set1, set2, presenceBoost):
    # Se uno dei due film non ha attributi associati, ritorniamo un valore nullo
    if (len(set1)==0 or len(set2)==0):
        return 0
    
    union = set1 | set2
    intersection = set1 & set2
    #Se c'è almeno un elemento in comune, partiamo con un boost preso in input, per dare maggiore valore alla similarità
    return presenceBoost * (len(intersection)>0) + (1 - presenceBoost) * len(intersection)/len(union)

def exponentialDecaySimilarity(value1, value2, alpha):
    if (value1 is None or value2 is None):
        return 0
    return math.exp(-alpha*abs(value1-value2))