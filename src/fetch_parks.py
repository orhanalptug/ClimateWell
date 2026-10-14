import json
import requests


# --------------------------------------------------
# Overpass sunucuları
# Biri çalışmazsa diğerine geçeceğiz.
# --------------------------------------------------

OVERPASS_URLS = [
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass-api.de/api/interpreter"
]


# --------------------------------------------------
# Çankaya ve çevresini kapsayan yaklaşık bbox
# south, west, north, east
# --------------------------------------------------

SOUTH = 39.80
WEST = 32.70
NORTH = 40.00
EAST = 33.05


# --------------------------------------------------
# OpenStreetMap sorgusu
#
# leisure=park etiketi taşıyan polygon/way kayıtlarını alıyoruz.
# --------------------------------------------------

query = f"""
[out:json][timeout:90];

way["leisure"="park"](
    {SOUTH},
    {WEST},
    {NORTH},
    {EAST}
);

out geom;
"""


headers = {
    "User-Agent": "ClimateWell/1.0 Educational Project",
    "Accept": "application/json"
}


# --------------------------------------------------
# Çalışan Overpass sunucusunu bul
# --------------------------------------------------

data = None

for url in OVERPASS_URLS:

    print("Deneniyor:", url)

    try:
        response = requests.get(
            url,
            params={"data": query},
            headers=headers,
            timeout=120
        )

        print("HTTP durum kodu:", response.status_code)

        response.raise_for_status()

        data = response.json()

        print("Başarılı sunucu:", url)
        break

    except requests.RequestException as error:
        print("Bu sunucu başarısız oldu:")
        print(error)
        print()


if data is None:
    raise RuntimeError(
        "Hiçbir Overpass sunucusundan veri alınamadı."
    )


# --------------------------------------------------
# OSM kayıtlarını GeoJSON'a dönüştür
# --------------------------------------------------

features = []


for element in data.get("elements", []):

    geometry = element.get("geometry")

    if not geometry:
        continue


    coordinates = []

    for point in geometry:

        coordinates.append(
            [
                point["lon"],
                point["lat"]
            ]
        )


    # Polygon için en az 3 nokta gerekli
    if len(coordinates) < 3:
        continue


    # Polygon kapalı değilse ilk noktayı sona ekle
    if coordinates[0] != coordinates[-1]:
        coordinates.append(coordinates[0])


    tags = element.get("tags", {})


    feature = {
        "type": "Feature",

        "properties": {
            "osm_id": element["id"],
            "osm_type": element["type"],
            "name": tags.get("name"),
            "leisure": tags.get("leisure")
        },

        "geometry": {
            "type": "Polygon",
            "coordinates": [
                coordinates
            ]
        }
    }


    features.append(feature)


# --------------------------------------------------
# GeoJSON oluştur
# --------------------------------------------------

output = {
    "type": "FeatureCollection",
    "features": features
}


# --------------------------------------------------
# Dosyaya kaydet
# --------------------------------------------------

OUTPUT_FILE = "data/raw/cankaya_parks.geojson"


with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        output,
        file,
        ensure_ascii=False,
        indent=2
    )


# --------------------------------------------------
# Sonuç
# --------------------------------------------------

print()
print("-----------------------------------")
print("Bulunan park sayısı:", len(features))
print("Dosya oluşturuldu:", OUTPUT_FILE)
print("-----------------------------------")


print("\nİlk park örnekleri:")

for feature in features[:20]:

    print(
        feature["properties"]["osm_id"],
        "|",
        feature["properties"]["name"]
    )