# Mesurer

## Protocole

1. Une tache reproductible, un critere de succes explicite.
2. `tkn bench start --label X --model Y`
3. Execute. Note si les tests passent.
4. `tkn bench end --tests pass|fail`
5. `tkn bench snapshot avant.json`
6. Applique UNE technique. Rien d'autre.
7. Rejoue la meme tache, meme snapshot.
8. `tkn bench compare avant.json apres.json`

Une technique qui ne baisse pas le cout PAR TACHE REUSSIE sur trois taches
differentes est a supprimer.

## Le piege du cumulatif

100 credits puis 60 : un snapshot brut affiche 100 -> 160, soit +60 %, alors
que la seconde execution a coute 40 % de moins. D'ou les marqueurs.

## Ce que compare refuse de conclure

- tarif inconnu sur une des deux periodes
- toutes les taches ne sont pas evaluees

## Ce qu'il faut regarder

- cout par tache reussie, jamais le total
- part d'entree en cache (si elle baisse, ton prefixe bouge)
- requetes au-dessus de 200k tokens d'entree
- ecart avant/apres, en %, avec la meme qualite