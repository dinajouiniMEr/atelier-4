"""Decoupe les procedures en passages, un passage par titre « ## ». FOURNI.

    python decoupage.py          # ecrit ../data/passages.csv

Chaque passage garde sa provenance : le fichier et le titre de la section.
C'est ce qui permettra de CITER la source d'une reponse.
"""
import csv
from pathlib import Path

DOSSIER = Path("../data/procedures")
SORTIE = Path("../data/passages.csv")


def decouper(chemin):
    """Renvoie les sections d'un fichier markdown : [(titre, texte), ...]."""
    sections, titre, lignes = [], None, []
    for ligne in chemin.read_text(encoding="utf-8").splitlines():
        if ligne.startswith("## "):
            if titre:
                sections.append((titre, " ".join(lignes).strip()))
            titre, lignes = ligne[3:].strip(), []
        elif titre and ligne.strip():
            lignes.append(ligne.strip())
    if titre:
        sections.append((titre, " ".join(lignes).strip()))
    return sections


def main():
    passages = []
    for chemin in sorted(DOSSIER.glob("*.md")):
        for titre, texte in decouper(chemin):
            passages.append({"id": f"P{len(passages) + 1:02d}", "source": chemin.name,
                             "titre": titre, "texte": texte})
    with open(SORTIE, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["id", "source", "titre", "texte"])
        w.writeheader()
        w.writerows(passages)
    print(f"{len(passages)} passages ecrits dans {SORTIE}")


if __name__ == "__main__":
    main()
