from datetime import datetime

def build_critique_query(base_query, selected_genres, selected_tags, recency_option):

    current_year = datetime.now().year
    threshold = current_year - 5

    query = base_query + "\n"

    query += """
    PREFIX dbo: <http://dbpedia.org/ontology/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    SELECT DISTINCT ?movie ?title ?year
    WHERE {
        ?movie rdfs:label ?title .
    """

    # GENRE FILTER
    if selected_genres:
        genre_filter = " || ".join([f"?genre = \"{g}\"" for g in selected_genres])
        query += f"""
        OPTIONAL {{ ?movie dbo:genre ?genre . }}
        FILTER ({genre_filter})
        """

    # TAG FILTER
    if selected_tags:
        tag_filter = " || ".join([f"?tag = \"{t}\"" for t in selected_tags])
        query += f"""
        OPTIONAL {{ ?movie dbo:tag ?tag . }}
        FILTER ({tag_filter})
        """

    # RECENCY
    query += """
        OPTIONAL { ?movie dbo:releaseYear ?year . }
    """

    if recency_option == "Più recente":
        query += f"""
        FILTER (?year >= {threshold})
        """

    elif recency_option == "Meno recente":
        query += f"""
        FILTER (?year < {threshold})
        """

    query += "\n}"

    return query