#!/data/data/com.termux/files/home/.local/bin/python
"""get_trending_py_repos.py – Get Trending Py Repos utilities.

This module provides functionality for get trending py repos."""
from __future__ import annotations
import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
import requests
from bs4 import BeautifulSoup
BASE_URL = 'https://github.com/trending/python'
TIMEFRAMES = ['daily', 'weekly', 'monthly']
OUTPUT_DIR = Path('trending_repos')

@dataclass
class Repo:
    """Repo – Repo."""
    name: str
    url: str
    description: str
    stars: str
    language: str
    timeframe: str

def fetch_trending(timeframe: str) -> list[Repo]:
    """fetch_trending – fetch trending.

Args:
    timeframe: Description of timeframe.

Returns:
    list[Repo]: Description of return value."""
    url = f'{BASE_URL}?since={timeframe}'
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    repos = []
    for article in soup.select('article.Box-row'):
        name = article.h2.text.strip().replace('\n', '').replace(' ', '')
        repo_url = 'https://github.com' + article.h2.a['href']
        description_tag = article.find('p')
        description = description_tag.text.strip() if description_tag else ''
        language_tag = article.find('span', itemprop='programmingLanguage')
        language = language_tag.text.strip() if language_tag else ''
        stars_tag = article.select_one("a[href$='stargazers']")
        stars = stars_tag.text.strip() if stars_tag else '0'
        repos.append(Repo(name=name, url=repo_url, description=description, stars=stars, language=language, timeframe=timeframe))
    return repos

def save_csv(repos: list[Repo], path: Path) -> None:
    """save_csv – save csv.

Args:
    repos: Description of repos.
    path: Description of path."""
    with path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=Repo.__annotations__.keys())
        writer.writeheader()
        for repo in repos:
            writer.writerow(asdict(repo))

def save_json(repos: list[Repo], path: Path) -> None:
    """save_json – save json.

Args:
    repos: Description of repos.
    path: Description of path."""
    path.write_text(json.dumps([asdict(r) for r in repos], indent=2), encoding='utf-8')

def main() -> None:
    """main – main."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    all_repos: list[Repo] = []
    for timeframe in TIMEFRAMES:
        repos = fetch_trending(timeframe)
        all_repos.extend(repos)
        save_csv(repos, OUTPUT_DIR / f'python_trending_{timeframe}.csv')
        save_json(repos, OUTPUT_DIR / f'python_trending_{timeframe}.json')
    print(f'Saved {len(all_repos)} repos to {OUTPUT_DIR.resolve()}')
if __name__ == '__main__':
    raise SystemExit(main())
