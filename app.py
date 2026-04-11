import streamlit as st
import rdflib
from pathlib import Path


# 1. CARICAMENTO GRAFO RDF

@st.cache_resource
def load_graph():
    BASE_DIR = Path(__file__).resolve().parent
    TTL_FILE = BASE_DIR / "rich_database.ttl"

    g = rdflib.Graph()
    g.parse(str(TTL_FILE), format="turtle")
    return g


g = load_graph()

st.title("🎬 Autocomplete Film RDF")


# 2. AUTOCOMPLETE (SPARQL)

def autocomplete(prefix):
    query = f"""
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    SELECT DISTINCT ?film ?title
    WHERE {{
        ?film rdfs:label ?title .
        FILTER regex(str(?title), "^{prefix}", "i")
    }}
    LIMIT 10
    """

    results = g.query(query)

    return [
        {
            "title": str(row.title),
            "uri": str(row.film)
        }
        for row in results
    ]


# 3. UI STREAMLIT

st.subheader("Cerca un film")

user_input = st.text_input("Scrivi il titolo:", key="film_search")

if user_input:
    results = autocomplete(user_input)

    if results:
        st.write("### Risultati")

        for r in results:
            # bottone per ogni film
            if st.button(r["title"]):
                # CONNETTI QUA
                selected_uri = r["uri"]

                st.success(f"Hai selezionato: {r['title']}")

                # placeholder per integrazione futura
                # CONNETTI QUA: passare selected_uri al modulo successivo

                # log interno (non visibile all’utente)
                print("URI selezionato:", selected_uri)

    else:
        st.warning("Nessun risultato trovato")