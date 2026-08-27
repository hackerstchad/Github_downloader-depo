# GITHUB-REPO-DOWNLOADER

> **Téléchargeur avancé de repositories GitHub** — télécharge tous les projets d'un utilisateur ou d'une organisation en une seule fois, avec barre de progression et style hacker.

## Description

`GITHUB-REPO-DOWNLOADER` est un outil Python avancé qui permet de télécharger automatiquement **tous les repositories publics** d'un utilisateur GitHub à partir d'une simple URL de profil.

Exemple :

```bash
https://github.com/hackerstchad
```

Le script détecte automatiquement le nom d'utilisateur, récupère la liste des repos via l'API GitHub, puis télécharge chaque repo sous forme d'archive `.zip` avec une barre de progression stylisée.

## Fonctionnalités

- Détection automatique du nom d'utilisateur depuis une URL GitHub
- Récupération de tous les repositories publics via l'API GitHub
- Téléchargement parallèle ou séquentiel
- Barre de progression `tqdm`
- Style hacker avec couleurs, bannière ASCII, effet typewriter
- Résumé final (succès / échecs / taille totale)
- Gestion des erreurs et reprises

## Installation

```bash
pip install -r requirements.txt
```

## Utilisation

```bash
python github_downloader.py
```

Puis entrez l'URL du profil GitHub :

```
https://github.com/hackerstchad
```

Les repositories seront téléchargés dans le dossier `downloads/<username>/`.

## Configuration

Vous pouvez modifier les variables en haut de `github_downloader.py` :

```python
DOWNLOAD_DIR = "downloads"
USE_PARALLEL = True
MAX_WORKERS = 4
GITHUB_API_URL = "https://api.github.com"
```

## Note

L'API GitHub a une limite de requêtes non authentifiées (60 par heure). Pour plus de repos, ajoutez un token GitHub dans le fichier `.env` :

```bash
GITHUB_TOKEN=votre_token_ici
```

## Avertissement

Ce script est destiné à télécharger vos propres repositories publics ou ceux sous licence ouverte. Respectez les conditions d'utilisation de GitHub.

---

**GITHUB-REPO-DOWNLOADER** — stylé, rapide, efficace.
