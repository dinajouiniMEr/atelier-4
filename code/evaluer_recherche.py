"""Mesure la recherche SEULE, sans aucun appel a un LLM. FOURNI.

    python evaluer_recherche.py minilm
    python evaluer_recherche.py mpnet

Tout tourne en local : aucune cle, aucun quota, quelques secondes.
"""
import csv
import json
import sys
import time
from pathlib import Path

from embeddings import charger_passages, encoder, index_passages
from metriques import mrr, recall_at_k
from recherche import chercher


def charger_questions(chemin="../data/questions.csv"):
    with open(chemin, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main(modele):
    passages = charger_passages()
    questions = [q for q in charger_questions() if q["repondable"] == "1"]
    debut = time.time()
    index = index_passages(passages, modele)
    vecteurs = encoder([q["question"] for q in questions], modele)
    trouves, meilleurs_scores = [], []
    for v in vecteurs:
        positions, scores = chercher(v, index, k=5)
        trouves.append([passages[i]["id"] for i in positions])
        meilleurs_scores.append(round(scores[0], 3))
    duree = time.time() - debut
    attendus = [q["passages"].split("|") for q in questions]

    print(f"\n=== recherche : {modele} ({len(questions)} questions, {len(passages)} passages) ===")
    resume = {"modele": modele, "ids": [q["id"] for q in questions], "trouves": trouves,
              "attendus": attendus, "duree_s": round(duree, 1)}
    for k in (1, 3, 5):
        resume[f"recall@{k}"] = recall_at_k(attendus, trouves, k)
        print(f"Recall@{k} : {resume[f'recall@{k}']:.3f}")
    resume["mrr"] = mrr(attendus, trouves)
    print(f"MRR      : {resume['mrr']:.3f}")
    print(f"duree    : {duree:.1f} s (index compris)")

    print("\nQuestions dont le bon passage n'est PAS dans les 3 premiers")
    for q, a, t in zip(questions, attendus, trouves):
        if not set(a) & set(t[:3]):
            print(f"  {q['id']}  attendu {'/'.join(a)}  trouve {' '.join(t[:3])}   {q['question'][:60]}")

    Path("resultats").mkdir(exist_ok=True)
    chemin = Path("resultats") / f"recherche__{modele}.json"
    chemin.write_text(json.dumps(resume, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nresultat enregistre dans {chemin}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "minilm")
