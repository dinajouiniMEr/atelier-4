"""Verifie recall_at_k() et mrr(), sans reseau ni quota.

    python test_metriques.py
"""
from metriques import faits_presents, mrr, recall_at_k

attendus = [["P18"], ["P10"], ["P03"], ["P27", "P29"]]
trouves = [["P18", "P19", "P22"],      # rang 1
           ["P11", "P10", "P12"],      # rang 2
           ["P01", "P02", "P04"],      # absent
           ["P28", "P30", "P29"]]      # rang 3 (un des deux attendus)
try:
    cas = [("recall_at_k(k=1)", recall_at_k(attendus, trouves, 1), 0.25),
           ("recall_at_k(k=3)", recall_at_k(attendus, trouves, 3), 0.75),
           ("mrr", mrr(attendus, trouves), (1 + 1 / 2 + 0 + 1 / 3) / 4)]
except NotImplementedError as e:
    raise SystemExit(str(e))
ok = 0
for nom, obtenu, attendu in cas:
    if abs(obtenu - attendu) < 1e-9:
        ok += 1
    else:
        print(f"ECHEC  {nom} : attendu {attendu:.3f}, obtenu {obtenu:.3f}")
# les faits attendus (fourni) : quelques cas pour comprendre
assert faits_presents("49 euros", "Des frais de 49 € s'appliquent.")
assert faits_presents("24 heures|24 h", "Votre ligne revient sous 24h.")
assert faits_presents("30 %;12 mois", "Une réduction de 30% pendant 12 mois.")
assert not faits_presents("30 %;12 mois", "Une réduction de 30 %.")
print(f"{ok}/3 tests reussis")
