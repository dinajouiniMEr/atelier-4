"""Toutes vos evaluations cote a cote : la recherche, puis la reponse. FOURNI.

    python comparer.py
"""
import glob
import json


def charger(motif):
    out = []
    for chemin in sorted(glob.glob(motif)):
        with open(chemin, encoding="utf-8") as f:
            out.append(json.load(f))
    return out


if __name__ == "__main__":
    recherches = charger("resultats/recherche__*.json")
    reponses = charger("resultats/reponses__*.json")
    if not recherches and not reponses:
        raise SystemExit("aucun resultat : lancez d'abord evaluer_recherche.py")
    print(f"{'RECHERCHE':<14}{'Recall@1':>10}{'Recall@3':>10}{'Recall@5':>10}{'MRR':>8}")
    for r in recherches:
        print(f"{r['modele']:<14}{r['recall@1']:>10.3f}{r['recall@3']:>10.3f}"
              f"{r['recall@5']:>10.3f}{r['mrr']:>8.3f}")
    print(f"\n{'REPONSE':<22}{'justes':>8}{'refus a tort':>14}{'refus corrects':>16}"
          f"{'sources inv.':>14}{'latence':>9}")
    for r in sorted(reponses, key=lambda x: -x["exactitude"]):
        print(f"{r['etiquette']:<22}{r['exactitude']:>8.3f}{r['refus_a_tort']:>14.3f}"
              f"{r['refus_corrects']:>16.3f}{r['sources_inventees']:>14}{r['latence_s']:>8.2f}s")
    print("\n1 question sur 36 = 2,8 points ; 1 question hors base sur 8 = 12,5 points.")
