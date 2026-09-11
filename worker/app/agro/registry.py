"""Canonical RESA station registry and initialization data."""

from __future__ import annotations

from .models import Station

CUSTOM_DEPARTMENT = "Stations personnalisées"

DEPARTMENTS = {
    "Alibori": ["Alfakoara", "Banikoara", "Bodjecali", "Founougo", "Guéné", "Kandi", "Karimama", "Malanville", "Ségbana"],
    "Borgou": ["Alafiarou", "Bembèrèkè", "Bétérou", "Ina", "Kalalé", "Nikki", "Okpara", "Parakou", "Tchaourou", "Alafiarou Nouveau", "Tourou", "Sanson", "Tchaourou-Centre"],
    "Atacora": ["Birni", "Boukoumbé", "Dassari", "Kérou", "Kouandé", "Matéri", "Natitingou", "Porga", "Tanguiéta", "Péhunco"],
    "Donga": ["Bassila", "Djougou", "Copargo", "Partago", "Pénessoulou", "Sémèrè"],
    "Collines": ["Agouna", "Aklampa", "Bantè", "Dassa-Zoumè", "Gouka", "Kpataba", "Kokoro", "Ouessè", "Pira", "Savalou", "Savè", "Tchetti", "Toui", "Glazoué", "Atchakpa", "Igbo-Iroko", "Sokponta", "Agouagon", "Monkpa", "Ouessè Nouveau", "Gobaix", "Djidja-centre"],
    "Zou": ["Abomey", "Agbangnizoun", "Bohicon", "Ouinhi", "Zagnanado", "Zakpota", "Sagon", "Damè"],
    "Couffo": ["Aplahoué", "Dogbo-Tota", "Klouékanmey", "Lonkly", "Atomey", "Voly"],
    "Mono": ["Athiémé", "Bopa", "Comè", "Grand-Popo", "Houin-Agamè", "Kpinnou", "Lokossa", "Adohoun", "Dédékpoè", "Labavè", "Sèhomi"],
    "Atlantique": ["Allada", "Niaouli", "Ouidah-Nord", "Ouidah-Ville", "Sékou", "Toffo", "Soava Ounmè"],
    "Littoral": ["Cotonou", "Agonkanmey", "Cotonou-Aéro", "Cotonou-Commiss.", "Cotonou-Ville", "Cotonou-Port", "Cotonou-Akpakpa"],
    "Oueme": ["Adjohoun", "Avrankou", "Bonou", "Dangbo", "Ouando", "Porto-Novo", "Sèmè-Cocotier", "Tchaada"],
    "Plateau": ["Kétou", "Pobè", "Sakété", "Effehoute", "Kétou-Centre"],
}

PRINCIPAL = {"Kandi": "Alibori", "Parakou": "Borgou", "Natitingou": "Atacora", "Savè": "Collines", "Bohicon": "Zou", "Cotonou": "Littoral"}

# Chaque département sans station principale ETP utilise l'ETP de la station
# principale RESA du référentiel ci-dessous (couverture complète des 12
# départements, en remplacement des rattachements station par station).
ETP_DEPARTMENT_SOURCE = {
    "Alibori": "Kandi",
    "Borgou": "Parakou",
    "Atacora": "Natitingou",
    "Donga": "Natitingou",
    "Collines": "Savè",
    "Zou": "Bohicon",
    "Couffo": "Bohicon",
    "Mono": "Cotonou",
    "Atlantique": "Cotonou",
    "Littoral": "Cotonou",
    "Oueme": "Cotonou",
    "Plateau": "Cotonou",
}

H10_BY_STATION = {"cotonou": 124.0, "bohicon": 125.0, "savè": 125.0, "parakou": 126.0, "natitingou": 126.0, "kandi": 127.0}


def station_id(name: str) -> str:
    return name.casefold().replace(" ", "-").replace(".", "")


def canonical_stations() -> list[Station]:
    stations = []
    for department, names in DEPARTMENTS.items():
        etp_source = ETP_DEPARTMENT_SOURCE.get(department)
        for name in names:
            principal = name in PRINCIPAL
            etp_station_id = None if principal or not etp_source else station_id(etp_source)
            stations.append(Station(station_id(name), name, department, name, principal, etp_station_id))
    return stations


def station_documents() -> list[dict[str, object]]:
    return [{"id": station.id, "name": station.name, "department": station.department, "locality": station.locality, "principal": station.principal, "etp_station_id": station.etp_station_id} for station in canonical_stations()]
