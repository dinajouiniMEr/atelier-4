"""Evalue la chaine complete : question -> (recherche) -> generation -> reponse. FOURNI.

    python evaluer_reponses.py sans              # le modele seul, sans document
    python evaluer_reponses.py rag minilm        # RAG, 3 passages
    python evaluer_reponses.py rag minilm 1      # RAG, 1 seul passage

Les reponses sont gardees en cache : relancer ne coute rien.
"""
import json
import sys
import time
from pathlib import Path

from groq import RateLimitError

from embeddings import charger_passages, encoder, index_passages
from evaluer_recherche import charger_questions
from generation import MODELE_TEXTE, repondre
from metriques import faits_presents
from recherche import chercher

PAUSE = {"sans": 3.0, "rag": 7.5}    # 8 000 tokens / minute : ~1 000 tokens par appel RAG


def repondre_avec_cache(cache, cle, question, contexte):
    if cle in cache:
        return cache[cle]
    for tentative in range(4):
        try:
            debut = time.time()
            r = repondre(question, contexte)
            r["latence_s"] = round(time.time() - debut, 2)
            break
        except RateLimitError:
            attente = 20 * (tentative + 1)
            print(f"\n  quota atteint, pause de {attente} s")
            time.sleep(attente)
    else:
        raise RuntimeError("quota toujours atteint apres 4 tentatives")
    cache[cle] = r
    return r


def main(mode, embedding="minilm", k=3):
    etiquette = "sans" if mode == "sans" else f"rag__{embedding}__k{k}"
    passages = charger_passages()
    questions = charger_questions()
    fichier_cache = Path("../data/reponses") / f"{etiquette}.json"
    cache = json.loads(fichier_cache.read_text(encoding="utf-8")) if fichier_cache.exists() else {}

    contextes = [[] for _ in questions]
    if mode == "rag":
        index = index_passages(passages, embedding)
        for i, v in enumerate(encoder([q["question"] for q in questions], embedding)):
            positions, _ = chercher(v, index, k)
            contextes[i] = [passages[p] for p in positions]

    reponses = []
    for i, (q, ctx) in enumerate(zip(questions, contextes), 1):
        cle = f"{MODELE_TEXTE}|{q['id']}|{','.join(p['id'] for p in ctx)}"
        deja = cle in cache
        reponses.append(repondre_avec_cache(cache, cle, q["question"], ctx))
        if not deja:
            fichier_cache.parent.mkdir(exist_ok=True)
            fichier_cache.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
            time.sleep(PAUSE[mode])
        print(f"\r{i}/{len(questions)} questions", end="", flush=True)
    print()

    rep = [q["repondable"] == "1" for q in questions]
    justes = [r["suffisant"] and faits_presents(q["faits"], r["reponse"]) if ok else False
              for q, r, ok in zip(questions, reponses, rep)]
    trouves = [bool(set(q["passages"].split("|")) & {p["id"] for p in ctx}) if ok else False
               for q, ctx, ok in zip(questions, contextes, rep)]
    n_rep, n_hors = sum(rep), len(rep) - sum(rep)
    refus = [not r["suffisant"] for r in reponses]
    inventees = sum(1 for r, ctx in zip(reponses, contextes)
                    if set(r["sources"]) - {p["id"] for p in ctx})
    resume = {
        "etiquette": etiquette, "mode": mode, "embedding": embedding if mode == "rag" else "-",
        "k": k if mode == "rag" else 0, "modele": MODELE_TEXTE,
        "exactitude": sum(justes) / n_rep,
        "refus_a_tort": sum(f for f, ok in zip(refus, rep) if ok) / n_rep,
        "refus_corrects": sum(f for f, ok in zip(refus, rep) if not ok) / n_hors,
        "sources_inventees": inventees, "invalides": sum(r["invalide"] for r in reponses),
        "latence_s": round(sum(r["latence_s"] for r in reponses) / len(reponses), 2),
        "ids": [q["id"] for q in questions], "repondable": rep, "justes": justes,
        "trouves": trouves, "reponses": [r["reponse"] for r in reponses],
        "sources": [r["sources"] for r in reponses],
        "contexte": [[p["id"] for p in ctx] for ctx in contextes],
    }
    print(f"\n=== {etiquette} -> {MODELE_TEXTE} ===")
    print(f"reponses justes        : {resume['exactitude']:.3f}  ({sum(justes)}/{n_rep} questions avec reponse)")
    print(f"refus a tort           : {resume['refus_a_tort']:.3f}")
    print(f"refus corrects         : {resume['refus_corrects']:.3f}  (sur {n_hors} questions hors base)")
    print(f"sources inventees      : {inventees}      invalides : {resume['invalides']}")
    print(f"latence moyenne        : {resume['latence_s']:.2f} s")

    print("\nReponses fausses sur des questions qui ont une reponse")
    for q, r, ok, j in zip(questions, reponses, rep, justes):
        if ok and not j:
            print(f"  {q['id']}  attendu : {q['faits']}\n        recu    : {r['reponse'][:110]}")
    print("\nQuestions hors base auxquelles le modele a repondu quand meme")
    for q, r, ok in zip(questions, reponses, rep):
        if not ok and r["suffisant"]:
            print(f"  {q['id']}  {q['question'][:45]}  ->  {r['reponse'][:70]}")

    Path("resultats").mkdir(exist_ok=True)
    chemin = Path("resultats") / f"reponses__{etiquette}.json"
    chemin.write_text(json.dumps(resume, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nresultat enregistre dans {chemin}")


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ("sans", "rag"):
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "minilm",
         int(sys.argv[3]) if len(sys.argv) > 3 else 3)
