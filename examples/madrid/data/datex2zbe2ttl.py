#!/usr/bin/env python3
"""Generate examples/madrid/example_zbe.ttl from the DGT DATEX II dataset.

Source: the national ZBE publication from the DGT access point (NAP):
https://nap.dgt.es/datex2/v3/dgt/zbe/ControledZonePublication/Madrid.xml

That publication describes the Madrid low emission zone as a set of
``openlrPolygonCorners`` (WGS84 lat/lon pairs). This script keeps the
"Madrid (Madrid ZBE)" controlled zone and aggregates its polygons into a
single ``geo:wktLiteral`` so the example stays small and self-contained.

The publication is downloaded on demand (it is several MB) and is not
versioned in the repository.

Usage:
    python examples/madrid/data/datex2zbe2ttl.py
    python examples/madrid/data/datex2zbe2ttl.py --source /path/to/Madrid.xml
"""

import argparse
import math
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXAMPLE_DIR = HERE.parent
SOURCE_URL = "https://nap.dgt.es/datex2/v3/dgt/zbe/ControledZonePublication/Madrid.xml"
OUTPUT = EXAMPLE_DIR / "example_zbe.ttl"

ZONE_NAME = "Madrid (Madrid ZBE)"
TOLERANCE = 0.001  # Douglas-Peucker tolerance in degrees (~100 m)
SMALL_POLYGON_RATIO = 0.02  # tolerance is never larger than this share of a polygon
WKT_LINE_LENGTH = 96

PREFIXES = """@prefix : <http://example.org/resource/> .
@prefix edintzone: <https://edint.es/def/zona-regulatoria#> .
@prefix edintkos-rztype: <https://edint.es/kos/RegulatedZoneType/> .
@prefix esadm: <http://vocab.linkeddata.es/datosabiertos/def/sector-publico/territorio#> .
@prefix geo: <http://www.opengis.net/ont/geosparql#> .
@prefix sf: <http://www.opengis.net/ont/sf#> .
@prefix org: <http://www.w3.org/ns/org#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
"""

TEMPLATE = """{prefixes}
#################################################################
# Madrid Low Emission Zone (Zona de Bajas Emisiones)
#
# Source: DGT national ZBE dataset (DATEX II v3, ControlledZonePublication)
#         https://nap.dgt.es/datex2/v3/dgt/zbe/ControledZonePublication/Madrid.xml
# Geometry: "{zone_name}" controlled zone, aggregated from {polygon_count}
# openLR polygons and simplified (Douglas-Peucker, tolerance capped at ~100 m
# and reduced for small polygons). Coordinates are WGS84 (EPSG:4326).
#################################################################

:ZBE_Madrid
    a edintzone:RegulatedZone ;
    edintzone:hasRegulatedZoneType edintkos-rztype:LowEmissionZone ;
    rdfs:label "Zona de Bajas Emisiones de Madrid"@es ;
    rdfs:label "Madrid Low Emission Zone"@en ;
    rdfs:comment "Zona de acceso restringido para vehículos sin distintivo ambiental que cubre el ámbito interior de la M-30."@es ;
    edintzone:locatedIn :Municipio_Madrid ;
    edintzone:managedBy :Ayuntamiento_Madrid ;
    edintzone:startDate "2022-01-01"^^xsd:date ;
    edintzone:scheduleDescription "Restricciones permanentes de circulación para vehículos sin distintivo ambiental. Desde el 1 de enero de 2024 no hay franja horaria de libre circulación, salvo las exenciones previstas en la norma."@es ;
    edintzone:legalReference <https://www.madrid.es/portales/munimadrid/es/Inicio/Movilidad-y-transportes/Ordenanza-de-Movilidad-Sostenible/?vgnextfmt=default&vgnextoid=d73fff17a1151610VgnVCM1000001d4a900aRCRD&vgnextchannel=220e31d3b28fe410VgnVCM1000000b205a0aRCRD&idCapitulo=10613950> ;
    geo:hasGeometry :ZBE_Madrid_Geometry .

#################################################################
# Geometry (simplified, WGS84)
#################################################################

:ZBE_Madrid_Geometry
    a sf:Geometry ;
    geo:asWKT \"\"\"
    {wkt}\"\"\"^^geo:wktLiteral .

#################################################################
# Municipality (Minimal Instance)
#################################################################

:Municipio_Madrid
    a esadm:Municipio ;
    rdfs:label "Madrid"@es .

#################################################################
# Managing Organization
#################################################################

:Ayuntamiento_Madrid
    a org:Organization ;
    rdfs:label "Ayuntamiento de Madrid"@es .
"""


def local_name(tag):
    """Return the element name without its XML namespace."""
    return tag.rsplit("}", 1)[-1]


def iter_named(element, name):
    """Iterate over descendants named ``name``, ignoring namespaces."""
    for child in element.iter():
        if local_name(child.tag) == name:
            yield child


def find_text(element, name):
    """Return the stripped text of the first descendant named ``name``."""
    for child in iter_named(element, name):
        return (child.text or "").strip()
    return ""


def perpendicular_distance(point, start, end):
    """Perpendicular distance from ``point`` to the segment start-end."""
    (x, y), (x1, y1), (x2, y2) = point, start, end
    dx, dy = x2 - x1, y2 - y1
    if dx == 0 and dy == 0:
        return math.hypot(x - x1, y - y1)
    t = ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    return math.hypot(x - (x1 + t * dx), y - (y1 + t * dy))


def polygon_tolerance(ring, max_tolerance):
    """Scale the tolerance down for small polygons.

    A fixed ~100 m tolerance is fine for the big rings but flattens the small
    exclaves, so the tolerance is capped at a share of the polygon diagonal.
    """
    longitudes = [point[0] for point in ring]
    latitudes = [point[1] for point in ring]
    diagonal = math.hypot(
        max(longitudes) - min(longitudes), max(latitudes) - min(latitudes)
    )
    return min(max_tolerance, diagonal * SMALL_POLYGON_RATIO)


def simplify(ring, tolerance):
    """Simplify a closed ring using the Douglas-Peucker algorithm.

    The duplicated closing vertex is dropped before simplifying (the
    algorithm works on open polylines) and restored afterwards.
    """
    open_ring = ring[:-1] if ring[0] == ring[-1] else ring
    simplified = (
        _douglas_peucker(open_ring, tolerance) if len(open_ring) > 4 else open_ring
    )
    if len(simplified) < 3:
        simplified = open_ring
    return simplified + [simplified[0]]


def _douglas_peucker(points, tolerance):
    """Simplify an open polyline using the Douglas-Peucker algorithm."""
    if len(points) < 3:
        return list(points)
    start, end = points[0], points[-1]
    index, max_distance = 0, 0.0
    for i in range(1, len(points) - 1):
        distance = perpendicular_distance(points[i], start, end)
        if distance > max_distance:
            index, max_distance = i, distance
    if max_distance > tolerance:
        left = _douglas_peucker(points[: index + 1], tolerance)
        right = _douglas_peucker(points[index:], tolerance)
        return left[:-1] + right
    return [start, end]


def extract_polygons(xml_root, zone_name, tolerance):
    """Return the simplified rings of ``zone_name`` as (lon, lat) lists."""
    for zone in iter_named(xml_root, "controlledZone"):
        name = "".join(find_text(child, "value") for child in iter_named(zone, "name"))
        if name != zone_name:
            continue
        rings = []
        for corners in iter_named(zone, "openlrPolygonCorners"):
            points = []
            for coords in iter_named(corners, "openlrCoordinates"):
                latitude = find_text(coords, "latitude")
                longitude = find_text(coords, "longitude")
                if latitude and longitude:
                    points.append((float(longitude), float(latitude)))
            if len(points) < 3:
                continue
            ring = points if points[0] == points[-1] else points + [points[0]]
            rings.append(simplify(ring, polygon_tolerance(ring, tolerance)))
        return rings
    raise ValueError(f"Zone {zone_name!r} not found in the DATEX II source")


def format_wkt(rings, line_length):
    """Wrap a MULTIPOLYGON WKT, breaking lines only after a comma.

    Breaking after commas keeps every ``lon lat`` pair on a single line.
    """
    polygons = ", ".join(
        "(" + ", ".join(f"{lon:.5f} {lat:.5f}" for lon, lat in ring) + ")"
        for ring in rings
    )
    pieces = f"MULTIPOLYGON ({polygons})".split(", ")
    lines, current = [], ""
    for index, piece in enumerate(pieces):
        if current and len(current) + len(piece) > line_length:
            lines.append(current.rstrip())
            current = piece
        else:
            current += piece
        if index < len(pieces) - 1:
            current += ", "
    if current.strip():
        lines.append(current.rstrip())
    return "\n    ".join(lines)


def load_source(local_path):
    """Parse the DATEX II publication, downloading it when needed."""
    if local_path:
        print(f"Reading {local_path}")
        return ET.parse(local_path).getroot()
    print(f"Downloading {SOURCE_URL}")
    with urllib.request.urlopen(SOURCE_URL) as response:
        return ET.fromstring(response.read())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        help="Local DATEX II XML file (downloaded from the DGT URL by default)",
    )
    parser.add_argument(
        "--tolerance",
        type=float,
        default=TOLERANCE,
        help=f"Douglas-Peucker tolerance in degrees (default {TOLERANCE})",
    )
    args = parser.parse_args()

    xml_root = load_source(args.source)
    rings = extract_polygons(xml_root, ZONE_NAME, args.tolerance)
    OUTPUT.write_text(
        TEMPLATE.format(
            prefixes=PREFIXES,
            zone_name=ZONE_NAME,
            polygon_count=len(rings),
            wkt=format_wkt(rings, WKT_LINE_LENGTH),
        ),
        encoding="utf-8",
    )
    print(f"Wrote {OUTPUT} ({OUTPUT.stat().st_size} bytes, {len(rings)} polygons)")


if __name__ == "__main__":
    main()
