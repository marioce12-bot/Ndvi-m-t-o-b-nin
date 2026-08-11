# Plateforme NDVI Benin

Application de generation automatisee de cartes NDVI et Percent of Mean pour le Benin a partir des produits eVIIRS 375 m de USGS FEWS NET.

## Etat du projet

- Etape 0 : exploration de la source USGS terminee.
- Etape 1 : squelette du monorepo et worker FastAPI minimal.

Le rapport de validation de la source se trouve dans `ETAPE-0-USGS.md`.

## Demarrage du worker

Prerequis : Python 3.12.

```powershell
Set-Location worker
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Le health check est alors disponible sur `http://127.0.0.1:8000/health`.
