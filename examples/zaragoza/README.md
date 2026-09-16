# Zaragoza Regulated Parking Example (Zona 1)

This example demonstrates how to model urban regulatory zones using the **Base Zoning Ontology (`edintzone`)**. It specifically focuses on **Zona 1** of the regulated parking system in Zaragoza, Spain, managed by the company *Z+M UTE*.

## Context

In many cities, parking regulations are not defined by administrative boundaries (like districts or neighborhoods) but by functional clusters of streets. 

In Zaragoza, **Zona 1** is split into two distinct functional types:
1.  **ESRO (Blue Zone / Rotation):** Aimed at high turnover, limited to 2 hours.
2.  **ESRE (Orange Zone / Residents):** Prioritizes residents but allows rotation.

## Data Source

The data used in this example is based on the official street-list definition for "Zona 1" provided by the service operator:
*   **Source:** [Z+M UTE - Zonas Reguladas (Zona 1)](http://www.zmute.com/zonas-reguladas/zona-1)
*   **Regulation:** [Ordenanza de Movilidad Urbana](https://www.zaragoza.es/sede/servicio/normativa/13296#tit3-capitulo4)
  
## Semantic Mapping

The example transforms the flat list of streets from the website into a linked data structure using the following logic:

### 1. Regulatory Classes
-   **ESRO** is mapped to `edintzone:ShortTermParkingZone`.
-   **ESRE** is mapped to `edintzone:ResidentialParkingZone`.

### 2. Composition and Relationships
-   **`edintzone:composedOf`**: Connects the `RegulatedZone` to individual streets (`esadm:Via`). This shows how a functional zone is built from a collection of urban elements.
-   **`edintzone:locatedIn`**: Links the zone to the city (`esadm:Municipio`), in this case, the DBPedia resource for Zaragoza.
-   **`edintzone:managedBy`**: Identifies the organization (`org:Organization`) responsible for the operation (Z+M UTE).

### 3. Metadata and Legal Context
-   **`edintzone:scheduleDescription`**: Provides a human-readable string of the operating hours.
-   **`edintzone:legalReference`**: Links to the official municipal ordinance that gives the zone its legal standing.


### Example Query (SPARQL)
*Which streets belong to a Short Term Parking Zone in Zaragoza?*

```sparql
PREFIX edintzone: <https://edint.es/def/zona-regulatoria#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?streetLabel WHERE {
  ?zone a edintzone:ShortTermParkingZone ;
        edintzone:locatedIn <http://dbpedia.org/resource/Zaragoza> ;
        edintzone:composedOf ?street .
  ?street rdfs:label ?streetLabel .
}
```