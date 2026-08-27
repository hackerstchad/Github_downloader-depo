#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GITHUB-REPO-DOWNLOADER
Téléchargeur avancé de repositories GitHub.
Télécharge tous les repos publics d'un utilisateur en une seule fois.
Style hacker, barre de progression, multithreading, gestion d'erreurs.
"""

import os
import sys
import re
import json
import time
import shutil
import zipfile
import threading
import concurrent.futures
from pathlib import Path
from urllib.parse import urlparse

import requests
from tqdm import tqdm

# --- Imports optionnels ---
try:
    import colorama
    from colorama import Fore, Style
    colorama.init()
except Exception:
    class _DummyColor:
        def __getattr__(self, name):
            return ""
    Fore = Style = _DummyColor()

try:
    import pyfiglet
except ImportError:
    pyfiglet = None

# --- Configuration ---
DOWNLOAD_DIR = "downloads"
USE_PARALLEL = True
MAX_WORKERS = 4
GITHUB_API_URL = "https://api.github.com"
TIMEOUT = 30

# Couleurs
GREEN = Fore.GREEN
CYAN = Fore.CYAN
YELLOW = Fore.YELLOW
RED = Fore.RED
MAGENTA = Fore.MAGENTA
BRIGHT = Style.BRIGHT
RESET = Style.RESET_ALL
BLUE = Fore.BLUE

# Token GitHub (optionnel)
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")


# --- Utilitaires d'affichage ---

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def print_banner():
    clear_screen()
    if pyfiglet:
        banner = pyfiglet.figlet_format("GITHUB-DL", font="slant")
    else:
        banner = """
  ____ _ _   _   _       ____  ____   ___  _  __
 / ___(_) |_| | | | ___ |  _ \|  _ \ / _ \| |/ /
| |  _| | __| |_| |/ _ \| | | | | | | | | | ' / 
| |_| | | |_|  _  | (_) | |_| | |_| | |_| | . \ 
 \____|_|\__|_| |_|\___/|____/|____/ \___/|_|\_\\
        """
    print(BRIGHT + CYAN + banner + RESET)
    print(MAGENTA + "    Téléchargeur avancé de repositories GitHub" + RESET)
    print(YELLOW + "    [ Tous les projets d'un utilisateur en un seul clic ]" + RESET)
    print()


def typewriter(text, delay=0.02, color=GREEN):
    for char in text:
        sys.stdout.write(color + char + RESET)
        sys.stdout.flush()
        time.sleep(delay)
    print()


def print_separator(char="=", length=70, color=CYAN):
    print(color + char * length + RESET)


def press_enter():
    input(YELLOW + "\nAppuyez sur Entrée pour continuer..." + RESET)


# --- Parsing de l'URL ---

def extract_username(url):
    """Extrait le nom d'utilisateur d'une URL GitHub."""
    url = url.strip().rstrip("/")
    parsed = urlparse(url)
    if parsed.netloc not in ("github.com", "www.github.com"):
        return None
    parts = [p for p in parsed.path.split("/") if p]
    if not parts:
        return None
    return parts[0]


def validate_username(username):
    """Vérifie que le nom d'utilisateur est valide."""
    if not username:
        return False
    pattern = r"^[a-zA-Z0-9](?:[a-zA-Z0-9]|-(?=[a-zA-Z0-9])){0,38}$"
    return bool(re.match(pattern, username))


# --- API GitHub ---

def get_headers():
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "GithubRepoDownloader/1.0"
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    return headers


def fetch_repositories(username):
    """Récupère tous les repositories publics d'un utilisateur."""
    repos = []
    page = 1
    per_page = 100
    typewriter(f"[ ... ] Récupération des repositories de {username}...", color=CYAN)

    while True:
        url = f"{GITHUB_API_URL}/users/{username}/repos"
        params = {"page": page, "per_page": per_page, "type": "owner", "sort": "updated"}
        try:
            response = requests.get(url, headers=get_headers(), params=params, timeout=TIMEOUT)
            response.raise_for_status()
            data = response.json()
            if not data:
                break
            repos.extend(data)
            page += 1
        except requests.exceptions.RequestException as e:
            typewriter(f"[ X ] Erreur API : {e}", color=RED)
            return None
        except Exception as e:
            typewriter(f"[ X ] Erreur inattendue : {e}", color=RED)
            return None

    return repos


def get_user_info(username):
    """Récupère les informations publiques d'un utilisateur."""
    url = f"{GITHUB_API_URL}/users/{username}"
    try:
        response = requests.get(url, headers=get_headers(), timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        typewriter(f"[ ! ] Impossible de récupérer les infos utilisateur : {e}", color=YELLOW)
        return {}


# --- Téléchargement ---

def format_size(size_bytes):
    """Formate une taille en bytes en unités lisibles."""
    if size_bytes == 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB"]
    idx = 0
    while size_bytes >= 1024 and idx < len(units) - 1:
        size_bytes /= 1024
        idx += 1
    return f"{size_bytes:.2f} {units[idx]}"


def download_repo(repo, output_dir, position=0):
    """Télécharge un repository sous forme d'archive zip."""
    repo_name = repo.get("name", "unknown")
    owner = repo.get("owner", {}).get("login", "unknown")
    default_branch = repo.get("default_branch", "main")
    zip_url = f"https://github.com/{owner}/{repo_name}/archive/refs/heads/{default_branch}.zip"
    output_path = output_dir / f"{repo_name}.zip"

    try:
        with requests.get(zip_url, stream=True, timeout=TIMEOUT) as response:
            response.raise_for_status()
            total_size = int(response.headers.get("content-length", 0))
            block_size = 8192
            progress_bar = tqdm(
                total=total_size,
                unit="B",
                unit_scale=True,
                desc=f"{repo_name[:25]:<25}",
                position=position,
                leave=False,
                ncols=80,
                bar_format="{desc} |{bar:30}| {percentage:3.0f}% {n_fmt}/{total_fmt}"
            )
            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=block_size):
                    if chunk:
                        f.write(chunk)
                        progress_bar.update(len(chunk))
            progress_bar.close()
            file_size = output_path.stat().st_size
            return {"repo": repo_name, "status": "success", "size": file_size, "path": str(output_path)}
    except Exception as e:
        return {"repo": repo_name, "status": "failed", "error": str(e), "size": 0}


def download_all_repos(repos, output_dir):
    """Télécharge tous les repos avec ou sans parallélisme."""
    output_dir.mkdir(parents=True, exist_ok=True)
    results = []

    print_separator()
    typewriter(f"[ ... ] Téléchargement de {len(repos)} repository/repositories...", color=CYAN)
    print()

    if USE_PARALLEL and len(repos) > 1:
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {executor.submit(download_repo, repo, output_dir, 0): repo for repo in repos}
            for future in tqdm(concurrent.futures.as_completed(futures), total=len(repos), desc="Global", ncols=80, bar_format="{desc} |{bar:30}| {percentage:3.0f}% {n_fmt}/{total_fmt}"):
                results.append(future.result())
    else:
        for i, repo in enumerate(repos):
            results.append(download_repo(repo, output_dir, i))

    return results


# --- Extraction optionnelle ---

def extract_archives(output_dir):
    """Extrait toutes les archives zip téléchargées."""
    typewriter("[ ... ] Extraction des archives...", color=CYAN)
    extracted = 0
    failed = 0
    for zip_file in output_dir.glob("*.zip"):
        try:
            with zipfile.ZipFile(zip_file, "r") as z:
                z.extractall(output_dir)
            extracted += 1
        except Exception as e:
            typewriter(f"[ ! ] Extraction échouée pour {zip_file.name} : {e}", color=YELLOW)
            failed += 1
    typewriter(f"[ OK ] {extracted} archive(s) extraite(s), {failed} échec(s).", color=GREEN)


# --- Résumé ---

def print_summary(results, username, output_dir):
    success = [r for r in results if r["status"] == "success"]
    failed = [r for r in results if r["status"] == "failed"]
    total_size = sum(r.get("size", 0) for r in success)

    print_separator()
    print(BRIGHT + CYAN + "RÉSUMÉ DU TÉLÉCHARGEMENT".center(70) + RESET)
    print_separator()
    print(GREEN + f"  Utilisateur     : {username}" + RESET)
    print(GREEN + f"  Dossier cible   : {output_dir}" + RESET)
    print(GREEN + f"  Repos trouvés   : {len(results)}" + RESET)
    print(GREEN + f"  Téléchargés     : {len(success)}" + RESET)
    print(RED + f"  Échecs          : {len(failed)}" + RESET)
    print(YELLOW + f"  Taille totale   : {format_size(total_size)}" + RESET)

    if failed:
        print()
        print(RED + "  Échecs :" + RESET)
        for r in failed:
            print(RED + f"    - {r['repo']} : {r['error']}" + RESET)
    print_separator()


# --- Menu ---

def show_menu():
    print(BRIGHT + CYAN + """
    ╔══════════════════════════════════════════════════════╗
    ║              MENU GITHUB-REPO-DOWNLOADER             ║
    ╠══════════════════════════════════════════════════════╣
    ║  [1] Télécharger tous les repos d'un utilisateur     ║
    ║  [2] Extraire les archives zip                       ║
    ║  [3] Voir le dossier de téléchargement               ║
    ║  [4] À propos                                        ║
    ║  [5] Quitter                                         ║
    ╚══════════════════════════════════════════════════════╝
    """ + RESET)


def ask_url():
    url = input(CYAN + "\n[ ? ] Entrez l'URL du profil GitHub : " + RESET).strip()
    username = extract_username(url)
    if not username or not validate_username(username):
        typewriter("[ X ] URL invalide. Exemple : https://github.com/hackerstchad", color=RED)
        return None
    return username


def about():
    print(BRIGHT + CYAN + "À PROPOS".center(70) + RESET)
    print_separator()
    print(YELLOW + """
GITHUB-REPO-DOWNLOADER est un outil Python avancé permettant de
télécharger automatiquement tous les repositories publics d'un
utilisateur GitHub à partir de son URL de profil.

Fonctionnalités :
  • Détection automatique du username
  • Récupération via l'API GitHub
  • Téléchargement avec barre de progression
  • Multithreading optionnel
  • Extraction automatique des zip
  • Résumé détaillé
""" + RESET)


def main():
    current_username = None
    current_output_dir = None

    while True:
        print_banner()
        show_menu()
        choice = input(GREEN + "\n[ > ] Votre choix : " + RESET).strip()

        if choice == "1":
            username = ask_url()
            if not username:
                press_enter()
                continue
            current_username = username
            current_output_dir = Path(DOWNLOAD_DIR) / username

            user_info = get_user_info(username)
            public_repos = user_info.get("public_repos", "?")
            typewriter(f"[ OK ] Utilisateur trouvé : {username} ({public_repos} repos publics)", color=GREEN)

            repos = fetch_repositories(username)
            if repos is None:
                press_enter()
                continue
            if not repos:
                typewriter("[ ! ] Aucun repository public trouvé.", color=YELLOW)
                press_enter()
                continue

            results = download_all_repos(repos, current_output_dir)
            print_summary(results, username, current_output_dir)

            extract_choice = input(CYAN + "\n[ ? ] Voulez-vous extraire les archives ? (o/n) : " + RESET).strip().lower()
            if extract_choice in ("o", "oui", "y", "yes"):
                extract_archives(current_output_dir)

            press_enter()

        elif choice == "2":
            if not current_output_dir or not current_output_dir.exists():
                typewriter("[ ! ] Aucun dossier de téléchargement actif. Téléchargez d'abord.", color=YELLOW)
                press_enter()
                continue
            extract_archives(current_output_dir)
            press_enter()

        elif choice == "3":
            if not current_output_dir:
                typewriter(f"[ INFO ] Dossier par défaut : {Path(DOWNLOAD_DIR).absolute()}", color=CYAN)
            else:
                typewriter(f"[ INFO ] Dossier actuel : {current_output_dir.absolute()}", color=CYAN)
            press_enter()

        elif choice == "4":
            about()
            press_enter()

        elif choice == "5":
            typewriter("[ ... ] Fermeture du téléchargeur...", color=YELLOW)
            print(BRIGHT + CYAN + "\n[ AU REVOIR ] GITHUB-REPO-DOWNLOADER s'est déconnecté." + RESET)
            break

        else:
            typewriter("[ X ] Option invalide.", color=RED)
            press_enter()


if __name__ == "__main__":
    main()
