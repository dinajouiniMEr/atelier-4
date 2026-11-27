# Fiche de décision — Atelier 4 (RAG Fibrelune)

Modèle de génération : `qwen/qwen3.8-27b` (Groq, `temperature=0.0`, JSON forcé).
36 questions avec réponse, 8 questions hors base. 1 question sur 36 = 2,8 points.

## 1. Embedding retenu

| Embedding | Taille | R@1 | R@3 | R@5 | MRR | Durée recherche |
|---|---|---:|---:|---:|---:|---:|
| MiniLM (384 dim.) | 220 Mo | 0.500 | 0.806 | 0.917 | 0.653 | 6,9 s |
| **mpnet (768 dim.)** | 1 Go | **0.611** | **0.917** | **0.917** | **0.750** | ~10 s (hors premier téléchargement) |

**Décision : mpnet.** Écart : 4 questions sur 36 en R@1 et R@3 (11,1 points), MRR +0,097.
Le coût est un modèle 4 à 5 fois plus gros (1 Go, premier chargement ~7 min ici) ; il est compensé par 4 réponses en plus et 4 refus à tort en moins. À R@5 les deux modèles sont à égalité : le gain de mpnet est surtout un meilleur **classement** des 3 premiers.

## 2. Apport du RAG

| Variante | Réponses justes (sur 36) | Refus à tort (sur 36) | Refus corrects (sur 8) | Sources inventées | JSON invalides | Latence moy. |
|---|---:|---:|---:|---:|---:|---:|
| Sans documents | 8/36 (0,222) | 14/36 (0,389) | 4/8 (0,500) | 0 | 0 | 0,95 s |
| RAG MiniLM, k=3 | 29/36 (0,806) | 7/36 (0,194) | **8/8 (1,000)** | 0 | 0 | 0,54 s |
| **RAG mpnet, k=3** | **33/36 (0,917)** | **3/36 (0,083)** | **8/8 (1,000)** | 0 | 0 | 0,86 s |
| RAG mpnet, k=1 | 22/36 (0,611) | 14/36 (0,389) | **8/8 (1,000)** | 0 | 0 | 0,64 s |

Le RAG apporte **+25 questions justes** (8 → 33, soit +69,4 points) et fait passer les refus corrects de 4/8 à 8/8.
Sans documents, le modèle invente des valeurs plausibles et fausses : Q21 « 24 heures » au lieu de 30 minutes, Q22 « 30 minutes » au lieu de 24 heures, Q06 « 30 jours » au lieu de 60. Avec RAG, ces questions sont justes.
**k=3 est gardé** : passer à k=1 coûte 11 questions (33 → 22). Le surcoût (~1 000 tokens/appel, pause 7,5 s) est acceptable.

## 3. Sécurité

- 8/8 questions hors base refusées avec RAG, contre 4/8 sans documents (Q37, Q38, Q42, Q43 avaient une réponse inventée sans RAG).
- Aucune source inventée (P99) et aucun JSON invalide dans les 4 variantes.
- Aucun refus à tort en RAG mpnet hors des 3 questions dont le passage est manquant : le modèle refuse parce que le contexte est insuffisant, pas par caprice.

## 4. Diagnostic — quel étage améliorer ?

`rag__mpnet__k3` (tableau 2 × 2, total 36) :

| | Réponse juste | Réponse fausse |
|---|---:|---:|
| Passage retrouvé | 33 (`ok`) | 0 (`generation`) |
| Passage absent | 0 (`chance`) | 3 (`recherche`) |

Avec MiniLM, le même tableau donne 29 `ok`, 0 `generation`, 7 `recherche`, 0 `chance`.

**Priorité : la recherche**, avec 3 échecs sur 36 (8,3 %) contre 0 échec de génération. Les 3 refus à tort sont exactement les 3 passages manquants : la consigne de refus fonctionne, mais elle ne peut pas compenser un passage absent.

Pistes :
1. **Q13 et Q14 (passage attendu P11 « Comment résilier »)** : la question dit « modem » alors que le passage dit « box », et P11 mélange trois faits (délai de 10 jours, restitution sous 30 jours, 90 euros). Son vecteur moyen est dilué. Piste : découper P11 en passages plus courts et enrichir le titre avec `modem / box non restituée / délai d'arrêt / 90 euros`.
2. **Q28 (passage attendu P25 « Accéder à ses données (RGPD) »)** : la question dit « tout ce que vous savez sur moi » et « sous quel délai », le passage dit « copie de toutes les données personnelles » et « répond dans un délai d'un mois ». Piste : ajouter ces synonymes au titre indexé, ou tester une recherche hybride mots-clés + embedding.
3. Génération : aucune piste urgente ici ; garder la consigne actuelle (citer les identifiants, `suffisant=false` et « Information insuffisante » si le contexte ne suffit pas).

## 5. Deux explications de recherche ratée (mpnet, k=3)

- **Q13** « Que se passe-t-il si je ne rends pas le modem… ? » → attendu P11, trouvés P08 (compensation après panne), P13 (rétractation), P27 (plus de connexion). Le mot « modem » n'apparaît pas dans la base : P11 parle de « box non restituée ». Le client ne dit pas non plus « résiliation », titre de P11, et le passage mêle trois sujets différents.
- **Q14** « Combien de jours après ma demande mon contrat s'arrête-t-il vraiment ? » → attendu P11, trouvés P05 (contester un montant : « 10 jours ouvrés »), P03 (« 30 jours après la relance »), P16 (période de facturation suivante). Les passages P05 et P03 contiennent des formulations de délais très proches de la question, ce qui les fait passer devant P11 (« prend effet 10 jours après la demande »), noyé dans un passage plus long.

## 6. Ajustement de la métrique (vérification manuelle)

Deux réponses étaient justes mais comptées fausses par correspondance littérale ; les formes légitimes ont été ajoutées à `data/questions.csv` avec `|` :
- Q15 : `justificatif|attestation de domicile` (la réponse RAG cite bien l'attestation demandée par P12).
- Q25 : `mot de passe|mots de passe` (variante plurielle).

Après correction et recalcul sur le cache des réponses : 33/36 pour mpnet k=3 (au lieu de 32) et 8/36 pour « sans documents » (au lieu de 7). Aucun appel Groq supplémentaire n'a été nécessaire.

## 7. Commandes utilisées

```
python -m pip install fastembed groq numpy
python embeddings.py                 # 384 nombres ; similarités 0,72 / -0,03 / -0,13
python embeddings.py mpnet
python test_recherche.py             # 3/3
python test_metriques.py             # 3/3
python test_diagnostic.py            # 4/4
python evaluer_recherche.py minilm
python evaluer_recherche.py mpnet
python evaluer_reponses.py sans
python evaluer_reponses.py rag minilm
python evaluer_reponses.py rag mpnet
python evaluer_reponses.py rag mpnet 1
python diagnostic.py rag__mpnet__k3
python comparer.py
```

Résultats JSON : `code/resultats/recherche__*.json` et `code/resultats/reponses__*.json`.
Réponses mises en cache : `data/reponses/*.json`.
