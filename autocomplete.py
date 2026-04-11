import rdflib

#  carica il grafo RDF
g = rdflib.Graph()
g.parse("rich_database.ttl", format="turtle")

print("Numero di triple:", len(g))


# funzione di autocomplete
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

    # CONVERSIONE IN LISTA DI DIZIONARI
    return [
        {
            "title": str(row.title),
            "uri": str(row.film)
        }
        for row in results
    ]


# TEST AUTOCOMPLETE
print("\nAUTOCOMPLETE TEST:")

results = autocomplete("Toy")

for r in results:
    print(r["title"], "→", r["uri"])

# AUTOCOMPLETE INPUT
print("\n--- AUTOCOMPLETE INPUT ---")

while True:
    user_input = input("Cerca film (o 'exit'): ")

    if user_input.lower() == "exit":
        break

    results = autocomplete(user_input)

    print("\nRisultati:")
    for r in results:
        print(r["title"], "→", r["uri"])
    print("\n")