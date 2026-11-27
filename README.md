# Atelier 4 — Répondre à partir des documents (RAG)

## AVANT la séance (chez vous : 1,2 Go à télécharger)

    python -m pip install fastembed groq numpy
    cd code
    python embeddings.py           # MiniLM, 220 Mo
    python embeddings.py mpnet     # mpnet, 1 Go

Les modèles restent dans ~/.cache/fastembed : ensuite tout tourne hors ligne.

## Contenu

    data/procedures/        8 procédures Fibrelune
    data/passages.csv       les 35 passages (id, source, titre, texte)
    data/questions.csv      44 questions : 36 avec réponse, 8 hors base

    code/embeddings.py          fourni — texte -> vecteur (fastembed, local)
    code/decoupage.py           fourni — procédures -> passages.csv
    code/evaluer_recherche.py   fourni — mesure la recherche seule
    code/evaluer_reponses.py    fourni — mesure la chaîne complète
    code/comparer.py            fourni — tableau de toutes vos évaluations
    code/test_*.py              vérifient votre code, sans quota

## Ce que vous allez écrire

    code/recherche.py    étape 2 — chercher()
    code/metriques.py    étape 3 — recall_at_k(), mrr()
    code/generation.py   étape 5 — repondre()
    code/diagnostic.py   étape 7 — diagnostic()

## Quotas

La recherche ne consomme rien. La génération utilise qwen/qwen3.8-27b sur Groq :
8 000 tokens/minute, d'où 7,5 s de pause entre deux questions en mode RAG.
Les réponses sont gardées en cache dans data/reponses/.
