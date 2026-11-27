"""Quel etage a echoue ? La recherche ou la generation ?

    python diagnostic.py rag__minilm__k3

Sans appel reseau : on relit resultats/reponses__<etiquette>.json.
"""
import json
import sys


# ---------------------------------------------------------------- a ecrire
def diagnostic(trouves, justes):
    """Range chaque question dans une des quatre cases et renvoie leurs positions.

      "ok"         : bon passage retrouve, reponse juste
      "generation" : bon passage retrouve, reponse fausse   <- reparer la consigne / le modele
      "recherche"  : bon passage absent, reponse fausse     <- reparer la recherche
      "chance"     : bon passage absent, reponse juste      <- le modele savait, ou a devine
    """
    cases = {"ok": [], "generation": [], "recherche": [], "chance": []}
    for i, (trouve, juste) in enumerate(zip(trouves, justes)):
        if trouve and juste:
            cases["ok"].append(i)
        elif trouve:
            cases["generation"].append(i)
        elif juste:
            cases["chance"].append(i)
        else:
            cases["recherche"].append(i)
    return cases


# ---------------------------------------------------------------- fourni
def afficher(resume):
    idx = [i for i, ok in enumerate(resume["repondable"]) if ok]
    trouves = [resume["trouves"][i] for i in idx]
    justes = [resume["justes"][i] for i in idx]
    cases = diagnostic(trouves, justes)
    print(f"\n{resume['etiquette']} : {len(idx)} questions qui ont une reponse")
    print(f"\n{'':<20}{'reponse juste':>15}{'reponse fausse':>16}")
    print(f"{'passage retrouve':<20}{len(cases['ok']):>15}{len(cases['generation']):>16}")
    print(f"{'passage absent':<20}{len(cases['chance']):>15}{len(cases['recherche']):>16}")
    for nom in ("generation", "recherche"):
        print(f"\nEchecs de la {nom} :")
        for c in cases[nom]:
            i = idx[c]
            print(f"  {resume['ids'][i]}  contexte {' '.join(resume['contexte'][i]) or '-'}"
                  f"  ->  {resume['reponses'][i][:80]}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage : python diagnostic.py rag__minilm__k3")
    with open(f"resultats/reponses__{sys.argv[1]}.json", encoding="utf-8") as f:
        afficher(json.load(f))
