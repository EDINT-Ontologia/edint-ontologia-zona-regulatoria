# Madrid Regulated Parking Example

![Madrid map](./mapa_madrid.png)

## Context

This examples set demonstrates how to model the **Servicio de Estacionamiento Regulado (SER)** of Madrid using the **Base Zoning Ontology (`edintzone`)**. It shows how a real municipal regulated parking system can be represented as linked data using GeoSPARQL geometries from GeoJSON or GIS data.

## Single polygon case

Here we define the Zone using a single closed polygon, that defines the whole regulated zone.

For converting GeoJSON to WKT we used a Python script, check it at `./data` folder.

Sources: [GeoJSON layer](https://sigma.madrid.es/hosted/rest/services/GEOPORTAL/SERVICIO_DE_ESTACIONAMIENTO_REGULADO/MapServer/14/query?where=1%3D1&outFields=*&outSR=4326&f=geojson)

## Multiple geometries case

At least 5 types of regulated parking is defined by the data available:

- Azul
- Verde
- Naranja
- Rojo
- Alta rotación

For simplicity, we define examples for Azul and Verde only.

The geometry of the zone is not limited to a polygon by the ontology, a zone could be defined as a collection of geometries, including not only polygons but also other types of features.

In this case, roads are defined as geometrical lines and the zone as the collection of those lines. This is practical for the case of Madrid as different 

Data processing for this case included importing the geometry into QGIS for initial exploration, exporting the required parts as CSV (including WKT for the objects already) and finally collecting the WKT with a Python script. Check the `./data` folder for details.

Sources: [SHP files](https://geoportal.madrid.es/fsdescargas/IDEAM_WBGEOPORTAL/MOVILIDAD/ZONA_SER/SHP_ZIP.zip)

## Example Query (SPARQL)

### 1️⃣ Which regulated parking zones exist in Madrid?

```sparql
PREFIX : <http://example.org/resource/>
PREFIX edintzone: <https://edint.es/def/zona-regulatoria#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?zone ?label WHERE {
  ?zone a edintzone:RegulatedParkingZone ;
        edintzone:locatedIn :Municipio_Madrid ;
        rdfs:label ?label .
}
```

---

### 2️⃣ Retrieve the WKT geometry of all Residential Parking Zones

```sparql
PREFIX : <http://example.org/resource/>
PREFIX edintzone: <https://edint.es/def/zona-regulatoria#>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>

SELECT ?zone ?wkt WHERE {
  ?zone a edintzone:ResidentialParkingZone ;
        geo:hasGeometry ?geom .
  ?geom geo:asWKT ?wkt .
}
```

---