"""Rediger la reponse a partir des passages retrouves (le « G » de RAG).

    python generation.py "Combien coute la resiliation ?"
"""
import json
import os
import sys

from groq import Groq

client = Groq(api_key=os.environ.get("GROQ_API_KEY", ""))
MODELE_TEXTE = "qwen/qwen3.8-27b"

CONSIGNE_RAG = """Tu es l'assistant du service client de l'operateur Fibrelune.
Reponds a la question du client en utilisant UNIQUEMENT les passages fournis.
- Cite les identifiants des passages que tu as utilises (par exemple "P07").
- Si les passages ne permettent pas de repondre, mets "suffisant" a false et
  reponds "Information insuffisante". Ne devine jamais un montant, un delai ou une demarche.
- Reponds en francais, en deux phrases au plus, en reprenant les chiffres exacts.
Reponds uniquement par un objet JSON :
{"reponse": "...", "sources": ["P.."], "suffisant": true}"""

CONSIGNE_SANS = """Tu es l'assistant du service client de l'operateur Fibrelune.
Reponds a la question du client en francais, en deux phrases au plus.
Si tu ne connais pas la reponse, mets "suffisant" a false.
Reponds uniquement par un objet JSON :
{"reponse": "...", "sources": [], "suffisant": true}"""


# ---------------------------------------------------------------- fourni
def formater_passages(passages):
    """[P18] Mot de passe oublie : Depuis la page de connexion ..."""
    return "\n\n".join(f"[{p['id']}] {p['titre']} : {p['texte']}" for p in passages)


def lire_reponse(brut):
    """Le JSON du modele -> un dictionnaire verifie. Une reponse illisible est "invalide"."""
    try:
        d = json.loads(brut)
        return {"reponse": str(d.get("reponse", "")),
                "sources": [str(s).strip("[] ") for s in d.get("sources", []) or []],
                "suffisant": bool(d.get("suffisant", True)), "invalide": False}
    except (json.JSONDecodeError, AttributeError, TypeError):
        return {"reponse": "", "sources": [], "suffisant": False, "invalide": True}


# ---------------------------------------------------------------- a ecrire
def repondre(question, passages, modele=MODELE_TEXTE):
    """Avec des passages : consigne RAG. Sans passage : le modele repond de memoire."""
    if passages:
        consigne = CONSIGNE_RAG
        contenu = (f"Passages :\n{formater_passages(passages)}\n\n"
                   f"Question du client : {question}")
    else:
        consigne, contenu = CONSIGNE_SANS, f"Question du client : {question}"
    reponse = client.chat.completions.create(
        model=modele, temperature=0.0,
        response_format={"type": "json_object"},
        messages=[{"role": "system", "content": consigne},
                  {"role": "user", "content": contenu}])
    return lire_reponse(reponse.choices[0].message.content)



if __name__ == "__main__":
    from embeddings import charger_passages, index_passages
    from recherche import rechercher
    if len(sys.argv) < 2:
        sys.exit('usage : python generation.py "question"')
    passages = charger_passages()
    trouves = rechercher(sys.argv[1], passages, index_passages(passages))
    print("passages retrouves :", " ".join(p["id"] for p in trouves))
    print(json.dumps(repondre(sys.argv[1], trouves), ensure_ascii=False, indent=2))
