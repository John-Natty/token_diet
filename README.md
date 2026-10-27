# token-diet

Boîte à outils pour comprendre et réduire le contexte inutile envoyé à un agent de
code, en vérifiant que la qualité tient. Stdlib uniquement. Aucune clé API.

Un agent reexpédie tout son contexte à chaque tour : historique, instructions,
schémas d'outils, fichiers lus. C'est là que part la facture, en boucle, sans
production. token-diet mesure ce gaspillage et le réduit — sans promettre plus
que ce qu'il peut prouver.

## La promesse

> Comprendre et réduire le contexte inutile, en vérifiant que la qualité reste
> la même.

Le chiffre qui compte est **le coût d'une tâche correctement terminée**, pas le
minimum de tokens par réponse.

## Deux niveaux de confiance

**Prouvé par arithmétique** — aucune mesure nécessaire, ce sont des
multiplicateurs tarifaires :

- Astra coûte 5× Sol par token, en entrée comme en sortie
- au-delà de 272k tokens d'entrée, la requête entière double de tarif
- l'entrée en cache coûte ~10 % de l'entrée fraîche
- une écriture en cache coûte plus cher qu'une entrée fraîche

**À mesurer** — ce sont des hypothèses, pas des règles. Voir `docs/TESTED.md` :
zéro prose, noms courts, ne pas relire, dialecte compressé.

## Installation

    git clone https://github.com/<toi>/token-diet
    cd token-diet
    pip install -e .          # optionnel
    pip install -e '.[exact]' # tiktoken, pour un comptage non estimé
    pytest -q                 # 24 tests

## Commandes

| Commande | Effet |
|---|---|
| `tkn audit [chemin]` | Constats mesurables, en lecture seule |
| `tkn count <fichiers>` | Tokens, avec réinjection ou simulation de croissance |
| `tkn compress <fichier>` | Signatures seules, préfixées par leur numéro de ligne |
| `tkn index [chemin]` | Génère `INDEX.md` |
| `tkn bench start/end/report/snapshot/compare` | Mesure par tâche |
| `tkn proxy` | Proxy en **observation par défaut** |
| `tkn report` | Usage journalisé |
| `tkn rates` | Tarifs chargés, avec leur source |
| `tkn init [chemin]` | Installe un profil (`equilibre` ou `strict`) |

## Démarrage

    tkn init .                          # profil equilibre par defaut
    tkn audit .                         # voir ce qui fuit
    tkn index .                         # carte de symboles

Mesurer une technique :

    tkn bench start --label refactor-auth --model gpt-6.1-sol
    # ... tu executes la tache ...
    tkn bench end --tests pass
    tkn bench snapshot apres.json

Le proxy, d'abord en observation :

    tkn proxy --port 8787
    export OPENAI_BASE_URL=http://127.0.0.1:8787/v1
    tkn report --stats          # ce qu'il AURAIT coupe

Puis `--mode actif` quand les chiffres te convainquent.

## Principes

- **Tout est mesuré.** Pas de technique retenue sans avant/après.
- **Rien d'installé de force.** Le proxy n'est actif que sur demande.
- **Rien de silencieux.** Une troncature laisse un marqueur, un tarif inconnu
  affiche `?`, une empreinte de test non évaluée est comptée à part.
- **Zéro dépendance obligatoire.**

## Licence

MIT