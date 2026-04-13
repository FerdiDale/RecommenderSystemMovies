from datetime import datetime

def build_critique_query(selected_movie_year, selected_genres, selected_tags, recency_option):

    query = """
    PREFIX dbo: <http://dbpedia.org/ontology/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

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

    if recency_option == "Più recente":
        query += f"""
        FILTER (?releaseYear >= {selected_movie_year})
        """

    elif recency_option == "Meno recente":
        query += f"""
        FILTER (?releaseYear < {selected_movie_year})
        """

    query += "\n}"

    return query