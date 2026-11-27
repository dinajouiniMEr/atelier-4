"""Verifie chercher() sur un petit index en 2 dimensions, sans modele ni quota.

    python test_recherche.py
"""
import numpy as np

from recherche import chercher

index = np.array([[1.0, 0.0], [0.0, 1.0], [0.6, 0.8], [-1.0, 0.0]])   # 4 passages
question = np.array([0.8, 0.6])
try:
    positions, scores = chercher(question, index, k=3)
except NotImplementedError as e:
    raise SystemExit(str(e))
ok = 0
if list(positions) == [2, 0, 1]:
    ok += 1
else:
    print(f"ECHEC  positions : attendu [2, 0, 1], obtenu {list(positions)}")
if np.allclose(scores, [0.96, 0.8, 0.6]):
    ok += 1
else:
    print(f"ECHEC  scores : attendu [0.96, 0.8, 0.6], obtenu {np.round(scores, 3)}")
if len(chercher(question, index, k=1)[0]) == 1:
    ok += 1
else:
    print("ECHEC  k=1 doit renvoyer un seul passage")
print(f"{ok}/3 tests reussis")
