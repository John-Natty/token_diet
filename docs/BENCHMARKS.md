# Benchmarks réels

## Protocole

Trois tâches externes ont été exécutées chacune trois fois en baseline et
trois fois avec Token Diet actif. Chaque session Codex était neuve
(`--ephemeral --ignore-user-config`) et travaillait dans un clone indépendant
du même commit initial. Le prompt, les outils, le modèle `gpt-6-sol` et
l'effort `medium` étaient identiques dans les deux conditions. CLI :
`codex-cli 0.162.0-alpha.17.2`. L'ordre par tâche était baseline/actif,
actif/baseline, puis baseline/actif.

La baseline utilisait le fournisseur Codex normal. Pour l'actif, un
fournisseur explicite routait l'API Responses vers le proxy local, lui-même
connecté à `https://chatgpt.com/backend-api/codex`. Le proxy était démarré
avec `--mode actif --limit 1000`; chaque run retenu possède au moins une
réécriture non nulle dans `proxy_stats.jsonl`. Le mode `observe`, qui transmet
le corps inchangé, n'a pas été utilisé comme condition optimisée. Les bundles
Git et les prompts figurent dans [`benchmarks/`](../benchmarks/README.md).

Les tokens proviennent de l'événement Codex `turn.completed`, la durée du
temps écoulé autour de la commande et les tests du clone ainsi que de la
suite d'acceptation figée. Le cache est une partie des tokens d'entrée. Les
crédits ou coûts réellement facturés ne sont pas exposés par ces sessions
authentifiées ChatGPT. Aucune conversion tarifaire n'est appliquée.

## Tâches et commits initiaux

| ID | Tâche | Commit initial | Tests avant tâche |
|---|---|---|---|
| A | Corriger les calculs facture, remise, TVA et arrondis | `66ac2ffc67e0a1086e8ce16a65c4c592dfe67d26` | 5 réussis, 1 échec volontaire |
| B | Refactoriser les imports et exports de commandes CSV | `21197a7aefa882dc7b5e0b0e7d3d7f12d3ef57fe` | 3 réussis |
| C | Ajouter filtre et pagination à GET /tasks | `3a84583d9d1528d042817ab3c09f29449172b50f` | 2 réussis; 9 critères d'acceptation en échec |

## Résultats bruts retenus

`B` signifie baseline et `O` proxy actif. Toutes les lignes ci-dessous ont
réussi les tests du clone et la suite d'acceptation figée : 6 tests pour A,
3 pour B, 11 pour C. La colonne `T/F/E` donne le nombre de commandes de test,
de ces commandes en échec pendant le travail, puis d'événements de modification
de fichiers. Elle décrit les tentatives et révisions observables; elle ne
mesure pas les corrections internes du modèle. `Blocs/car.` donne les blocs
tronqués et caractères retirés dans les requêtes par le proxy, pas des tokens
ni des économies facturées. Le coût facturé est indisponible pour chaque ligne.

| Run | Entrée | Cache inclus | Sortie | Durée (s) | T/F/E | Blocs/car. |
|---|---:|---:|---:|---:|---:|---:|
| A6-B1 | 114 745 | 109 056 | 2 667 | 60,9 | 2/1/1 | 0/0 |
| A6-B2 | 121 781 | 108 928 | 1 810 | 44,1 | 3/2/1 | 0/0 |
| A6-B3 | 146 016 | 139 392 | 1 841 | 54,1 | 3/2/2 | 0/0 |
| A6-O3 | 204 597 | 187 008 | 3 160 | 104,2 | 2/1/1 | 43/35 162 |
| A6-O4 | 174 967 | 167 296 | 2 285 | 72,9 | 4/2/2 | 68/60 270 |
| A6-O5 | 173 534 | 165 248 | 2 941 | 88,3 | 3/2/1 | 43/28 725 |
| B6-B1 | 95 279 | 89 728 | 1 209 | 32,1 | 2/1/1 | 0/0 |
| B6-B2 | 104 554 | 97 408 | 1 226 | 32,6 | 2/1/1 | 0/0 |
| B6-B3 | 84 070 | 72 064 | 1 076 | 30,3 | 1/0/1 | 0/0 |
| B6-O1 | 128 593 | 121 216 | 1 610 | 53,6 | 2/1/1 | 44/44 274 |
| B6-O2 | 160 102 | 152 704 | 2 143 | 66,5 | 3/1/1 | 55/49 552 |
| B6-O3 | 150 951 | 142 848 | 1 879 | 59,3 | 1/0/1 | 47/58 109 |
| C6-B1 | 166 205 | 157 824 | 2 675 | 64,3 | 2/0/3 | 0/0 |
| C6-B2 | 147 797 | 132 864 | 2 477 | 50,9 | 2/1/3 | 0/0 |
| C6-B4 | 137 715 | 125 056 | 2 485 | 62,5 | 2/1/3 | 0/0 |
| C6-O1 | 193 270 | 166 400 | 2 698 | 84,1 | 1/0/3 | 70/70 566 |
| C6-O2 | 240 788 | 217 472 | 2 826 | 97,7 | 2/1/3 | 76/96 804 |
| C6-O3 | 164 729 | 157 184 | 2 537 | 73,9 | 2/1/2 | 49/31 740 |

## Résultats agrégés

Moyennes par tâche correctement terminée, trois runs par case. L'entrée hors
cache est calculée comme entrée moins cache; elle reste une mesure de tokens,
pas un coût. Le taux de réussite des 18 runs retenus est de 3/3 dans chaque
case.

| Tâche | Condition | Entrée | Cache | Hors cache | Sortie | Durée (s) | Réussite |
|---|---|---:|---:|---:|---:|---:|---:|
| A | Baseline | 127 514 | 119 125 | 8 389 | 2 106 | 53,0 | 3/3 |
| A | Actif | 184 366 | 173 184 | 11 182 | 2 795 | 88,5 | 3/3 |
| B | Baseline | 94 634 | 86 400 | 8 234 | 1 170 | 31,7 | 3/3 |
| B | Actif | 146 549 | 138 923 | 7 626 | 1 877 | 59,8 | 3/3 |
| C | Baseline | 150 572 | 138 581 | 11 991 | 2 546 | 59,2 | 3/3 |
| C | Actif | 199 596 | 180 352 | 19 244 | 2 687 | 85,2 | 3/3 |

À pondération égale des trois tâches, l'actif a consommé en moyenne
176 837 tokens d'entrée contre 124 240 en baseline (+42,3 % observés),
2 453 tokens de sortie contre 1 941 (+26,4 %) et 77,8 s contre 48,0 s
(+62,2 %). Le taux de réussite mesuré sur les runs retenus n'a pas changé
(9/9 dans chaque condition). **Le coût moyen facturé par tâche réussie est
indisponible** : aucune donnée de coût ou de crédits par run n'a été fournie
par l'authentification ChatGPT. Les caractères retirés ne servent pas à
calculer un coût.

## Essais non retenus et limites

Avant la série `gpt-6-sol`/`medium`, un essai A baseline et un essai A avec
proxy actif ont terminé sous `gpt-6.1-sol`/`low`. L'actif n'avait retiré aucun
caractère; ces essais ne sont pas mélangés avec la nouvelle série. Au début
de celle-ci, `A6-O1` et `A6-O2` ont réussi les tests, mais aucune sortie d'outil
n'a été réécrite : le format réel `custom_tool_call_output` de Codex n'était
pas encore pris en charge. Le support a été ajouté et testé avant `A6-O3`.

`C6-B3` a été interrompu après 399 s sans événement `turn.completed`. Le clone
modifié passait les 11 tests d'acceptation, mais la session n'a pas fourni de
mesure totale de tokens ni de réponse finale. `C6-B4` est sa répétition
indépendante. En comptant cette tentative interrompue, 9 baselines sur
10 tentées ont terminé, contre 9 runs actifs valides sur 9 après correction
du format. Cet écart ne permet pas de conclure à une différence de fiabilité.

Les 18 runs retenus ont été exécutés sur trois petits projets et un seul
modèle, avec trois répétitions par case. Les tests figés couvrent les règles
principales, pas tout comportement possible. L'inspection des diffs a confirmé
le calcul `Decimal` après remise pour A, l'extraction de logique commune sans
suppression des fonctions publiques pour B, et la validation des paramètres
avec ordre SQL stable pour C. Les répétitions ont été alternées, mais des
variations de service, de cache et de chemin de raisonnement restent possibles.
Les projets source figés sont restés propres. Les journaux bruts, clones et
scripts d'agrégation sont conservés localement dans
`/home/natty/token_diet_benchmarks/`; les commits initiaux et prompts sont
également conservés dans `benchmarks/` du dépôt.

## Conclusion

Avec ce seuil et ces tâches, Token Diet a réellement raccourci des requêtes,
mais les sessions actives ont consommé davantage de tokens observés et duré
plus longtemps. Le taux de réussite des runs achevés est identique dans les
deux conditions. Aucune économie de coût facturé n'est démontrée; le coût
moyen par tâche réussie reste non mesurable avec les données disponibles.
