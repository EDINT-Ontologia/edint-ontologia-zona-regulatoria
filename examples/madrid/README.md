# Madrid Regulated Zone Examples

![Madrid map](./mapa_madrid.png)

## Context

This examples set demonstrates how to model regulated zones of Madrid using the **Base Zoning Ontology (`edintzone`)**. It shows how real municipal regulations can be represented as linked data using GeoSPARQL geometries from GeoJSON or GIS data.

- **Servicio de Estacionamiento Regulado (SER)**: regulated parking zones.
- **Zona de Bajas Emisiones (ZBE)**: low emission zone.

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

## Low Emission Zone (ZBE)

The ZBE is modeled as a `edintzone:RegulatedZone` whose type is the SKOS
concept `edintkos-rztype:LowEmissionZone`, instead of a parking subclass. The
whole zone is a single `geo:wktLiteral` (a `MULTIPOLYGON`) kept inline in the
example, so the file is self-contained.

Source: [DGT national ZBE dataset](https://nap.dgt.es/datex2/v3/dgt/zbe/ControledZonePublication/Madrid.xml)
(DATEX II v3 `ControlledZonePublication`), which describes the controlled zone
as `openLR` polygons. `./data/datex2zbe2ttl.py` converts that publication into
`example_zbe.ttl`, aggregating the polygons of the *"Madrid (Madrid ZBE)"* zone
and simplifying them (~100 m tolerance) to keep the example readable.

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

### 3️⃣ Which low emission zone covers Madrid?

```sparql
PREFIX : <http://example.org/resource/>
PREFIX edintzone: <https://edint.es/def/zona-regulatoria#>
PREFIX edintkos-rztype: <https://edint.es/kos/RegulatedZoneType/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?zbe ?label WHERE {
  ?zbe a edintzone:RegulatedZone ;
       edintzone:hasRegulatedZoneType edintkos-rztype:LowEmissionZone ;
       edintzone:locatedIn :Municipio_Madrid ;
       rdfs:label ?label .
}
```

---

