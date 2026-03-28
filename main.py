import pandas as pd
import numpy as np

# 1. Carica dataset
df = pd.read_csv("MovieLensSmall/movies.csv")


# 2. Estrai generi
df['genres'] = df['genres'].apply(lambda x: x.split('|'))

# 3. Lista generi unici
all_genres = sorted(set(g for genres in df['genres'] for g in genres))

# 4. Inizializza matrice NxN
n = len(all_genres)
V = np.zeros((n, n), dtype=int)

# 5. Costruisci matrice di co-occorrenza
for movie_genres in df['genres']:
    for i, g1 in enumerate(all_genres):
        if g1 in movie_genres:
            for j, g2 in enumerate(all_genres):
                if g2 in movie_genres:
                    V[i, j] += 1

# 6. Stampa matrice con nomi dei generi
print("Generi:", all_genres)
print("Matrice co-occorrenza V:\n", V)

# Trasforma matrice in DataFrame con etichette
V_df = pd.DataFrame(V, index=all_genres, columns=all_genres)

# Salva in Excel
V_df.to_excel("cooccorrenza_generi.xlsx")

print("Matrice salvata in 'cooccorrenza_generi.xlsx'")