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
- pour l'API au-delà de 272k tokens d'entrée : ×2 sur entrée, cache et
  écriture de cache, ×1,5 sur sortie
- selon le modèle, l'entrée en cache coûte 5 à 10 % de l'entrée fraîche
- une écriture en cache coûte plus cher qu'une entrée fraîche

**À mesurer** — ce sont des hypothèses, pas des règles. Voir `docs/TESTED.md` :
zéro prose, noms courts, ne pas relire, dialecte compressé.

## Installation

    git clone https://github.com/John-Natty/token_diet.git
    cd token_diet
    python3 -m pip install -e '.[dev]'
    python3 -m pytest -q

Pour un comptage exact, installe aussi l'extra optionnel `exact` :

    python3 -m pip install -e '.[exact]'

## Commandes

| Commande | Effet |
|---|---|
| `tkn audit [chemin]` | Constats mesurables, en lecture seule (`--check` pour bloquer) |
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

    tkn bench start --label refactor-auth --model gpt-6-sol
    # ... tu executes la tache ...
    tkn bench end --tests pass
    tkn bench snapshot apres.json

Le proxy démarre en observation avec `tkn proxy --port 8787`. Ce mode ne
réduit pas les requêtes transmises : il journalise seulement ce qu'une
réécriture aurait changé. Le mode actif applique la réécriture et doit être
explicitement activé :

    tkn proxy --port 8787 --mode actif

Vérifie que ton client Codex route réellement ses requêtes vers le proxy.
Ne présume pas que `OPENAI_BASE_URL` est pris en charge par chaque version ou
configuration de Codex. Pour Codex CLI, un fournisseur explicite dans
`config.toml` permet de définir `base_url` et `wire_api`; vérifie le trafic
reçu par Token Diet avant de comparer les résultats.

## Benchmarks réels

Compare des sessions indépendantes repartant du même commit, avec le même
modèle, le même niveau d'effort, les mêmes outils et le même prompt. Répète
chaque condition au moins trois fois et alterne leur ordre. Consigne les
tokens entrée, sortie et cache, la durée, les tests, les reprises et la preuve
que le mode actif a réellement modifié une requête. Calcule le coût moyen par
tâche correctement terminée seulement avec des coûts réellement mesurés.

Les caractères supprimés et l'estimation `caractères / 4` ne sont pas des
économies facturées. La première série réelle avec `gpt-6-sol` en effort
`medium` n'a pas montré de baisse des tokens consommés. Les données de coût
facturé sont indisponibles. Le protocole et les résultats sont dans
[`docs/BENCHMARKS.md`](docs/BENCHMARKS.md).

## Principes

- **Tout est mesuré.** Pas de technique retenue sans avant/après.
- **Rien d'installé de force.** Le proxy n'est actif que sur demande.
- **Rien de silencieux.** Une troncature laisse un marqueur, un tarif inconnu
  affiche `?`, une empreinte de test non évaluée est comptée à part.
- **Zéro dépendance obligatoire.**

## Licence

MIT
