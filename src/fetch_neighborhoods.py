import json
from collections import Counter

import requests


URL = (
    "https://planaski.ankara.bel.tr/webgis/rest/services/"
    "deprem/ilceMahalleRapor/MapServer/2/query"
)

TARGET_NEIGHBORHOODS = [
    "AYRANCI",
    "KAVAKLIDERE",
    "BALGAT",
    "ÇİĞDEM",
    "YILDIZEVLER",
    "BİRLİK",
    "BEYTEPE",
    "ALACAATLI"
]


params = {
    "where": "1=1",
    "outFields": "OBJECTID,AD,KIMLIKNO,ILCEID",
    "returnGeometry": "true",
    "outSR": "4326",
    "f": "geojson"
}


headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/152.0.0.0 Safari/537.36"
    ),
    "Referer": "https://planaski.ankara.bel.tr/"
}


response = requests.get(
    URL,
    params=params,
    headers=headers,
    timeout=30
)

response.raise_for_status()

data = response.json()


# --------------------------------------------------
# 1. Önce sadece istediğimiz mahalle adlarını buluyoruz
# --------------------------------------------------

candidate_features = []

for feature in data["features"]:
    properties = feature["properties"]

    neighborhood_name = properties.get("AD")

    if (
        neighborhood_name
        and neighborhood_name.strip().upper() in TARGET_NEIGHBORHOODS
    ):
        candidate_features.append(feature)


print("İsim eşleşmesi bulunan kayıt sayısı:", len(candidate_features))


# --------------------------------------------------
# 2. Bu kayıtların ILCEID değerlerini sayıyoruz
# --------------------------------------------------

ilce_ids = []

for feature in candidate_features:
    ilce_id = feature["properties"].get("ILCEID")

    if ilce_id is not None:
        ilce_ids.append(str(ilce_id))


id_counts = Counter(ilce_ids)

print("\nBulunan ILCEID değerleri:")

for ilce_id, count in id_counts.items():
    print(ilce_id, "->", count, "kayıt")


# --------------------------------------------------
# 3. En çok tekrar eden ILCEID'yi seçiyoruz
# --------------------------------------------------

if not id_counts:
    raise ValueError("Hiç ILCEID bulunamadı.")


cankaya_ilce_id = id_counts.most_common(1)[0][0]

print("\nSeçilen Çankaya ILCEID:")
print(cankaya_ilce_id)


# --------------------------------------------------
# 4. Sadece bu ILCEID'ye ait mahalleleri bırakıyoruz
# --------------------------------------------------

selected_features = []

for feature in candidate_features:
    properties = feature["properties"]

    if str(properties.get("ILCEID")) == cankaya_ilce_id:
        selected_features.append(feature)


# --------------------------------------------------
# 5. GeoJSON dosyasını oluşturuyoruz
# --------------------------------------------------

output = {
    "type": "FeatureCollection",
    "features": selected_features
}


with open(
    "data/raw/cankaya_neighborhoods.geojson",
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
# 6. Sonucu gösteriyoruz
# --------------------------------------------------

print("\nBulunan Çankaya mahalle sayısı:", len(selected_features))
print("--------------------------------")

for feature in selected_features:
    properties = feature["properties"]

    print(
        "Mahalle:",
        properties["AD"],
        "| KIMLIKNO:",
        properties["KIMLIKNO"]
    )