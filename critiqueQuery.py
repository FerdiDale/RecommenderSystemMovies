from datetime import datetime

# Aggiunta XSD per cast del runtime a intero
# Necessario per confrontare correttamente la durata dei film
# (DBpedia spesso salva runtime come stringa)

#in def build_critique_query() aggiungere selected_actors e runtime_option come parametri e togliere i commenti relativi al runtime
def build_critique_query(selected_movie_year, selected_genres, selected_tags, recency_option, selected_directors, selected_actors, runtime_option, selected_movie_runtime):

    query = """
    PREFIX dbo: <http://dbpedia.org/ontology/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

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
    """

    # GENRE FILTER
    if selected_genres:
        genre_filter = " || ".join([f"?genre = \"{g}\"" for g in selected_genres])
        query += f"""
        FILTER ({genre_filter})
        """

    # TAG FILTER
    if selected_tags:
        tag_filter = " || ".join([f"?tag = \"{t}\"" for t in selected_tags])
        query += f"""
        FILTER ({tag_filter})
        """

    # DIRECTOR FILTER
    if selected_directors:
        director_filter = " || ".join([
            f'CONTAINS(STR(?director), "{d.replace(" ", "_")}")'
            for d in selected_directors
        ])

        query += f"""
        FILTER ({director_filter})
        """

    # ACTORS FILTER
    if selected_actors:
        actor_filter = " || ".join([
            f'CONTAINS(STR(?starring), "{a.replace(" ", "_")}")'
            for a in selected_actors
        ])

        query += f"""
        FILTER ({actor_filter})
        """
    
    # RUNTIME FILTER
    if runtime_option == "Più lungo":
       query += f"""
       FILTER (xsd:integer(?runtime) >= {selected_movie_runtime})
       """

    elif runtime_option == "Più breve":
       query += f"""
       FILTER (xsd:integer(?runtime) <= {selected_movie_runtime})
       """
    
    elif runtime_option == "Nessuna preferenza":
        pass

    if recency_option == "Più recente":
        query += f"""
        FILTER (?releaseYear >= {selected_movie_year})
        """

    elif recency_option == "Meno recente":
        query += f"""
        FILTER (?releaseYear <= {selected_movie_year})
        """
    elif recency_option == "Nessuna preferenza":
        pass

    query += "\n}"

    print(query)

    return query