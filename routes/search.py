from flask import Blueprint, jsonify
from rdflib import Graph
from config import query_dbpedia  # Importamos la función de consulta a DBpedia

# Conexion a la ontología local
ONT_FILE = "computadora.owl"  # Ruta a tu archivo .owl
g = Graph()
g.parse(ONT_FILE, format="xml")

# Crear un Blueprint para el endpoint Search
semantic_search = Blueprint("search", __name__)

@semantic_search.route("/<string:term>", methods=["GET"])  # Usar un parámetro en la URL
def handle_search(term):
    """
    Endpoint para buscar un término semántico en la ontología local y DBpedia.
    """
    try:
        # Limpiar el término de búsqueda
        search_term = term.strip()
        if not search_term:
            return jsonify({"error": "Search term is required"}), 400

        # Crear la consulta SPARQL para la ontología local
        local_query = f"""
        SELECT ?subject ?label ?comment ?type ?predicate ?object
        WHERE {{
            {{
                ?subject rdfs:label ?label . 
                FILTER(CONTAINS(LCASE(?label), LCASE("{search_term}")))
            }} UNION {{
                ?subject ?predicate ?object . 
                FILTER(CONTAINS(LCASE(STR(?object)), LCASE("{search_term}")))

            }} OPTIONAL {{
                ?subject rdfs:comment ?comment . 
            }} OPTIONAL {{
                ?subject rdf:type ?type . 
            }}
        }}
        LIMIT 20
        """

        # Ejecutar la consulta en la ontología local
        local_results = g.query(local_query)
        local_output = []
        for row in local_results:
            local_output.append({
                "subject": str(row["subject"]),
                "label": str(row["label"]) if row.get("label") else None,
                "comment": str(row["comment"]) if row.get("comment") else None,
                "type": str(row["type"]) if row.get("type") else None,
                "predicate": str(row["predicate"]) if row.get("predicate") else None,
                "object": str(row["object"]) if row.get("object") else None
            })

        # Consultar a DBpedia
        dbpedia_results = query_dbpedia(search_term)

        # Combinar resultados y retornarlos
        return jsonify({
            "local_results": local_output,
            "dbpedia_results": dbpedia_results
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
