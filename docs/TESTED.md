# Ce qu'on a testé

## Troncature des sorties d'outils

Hypothèse : le proxy actif avec un plafond de 1 000 caractères réduit la
consommation de tokens des tâches de développement.

Méthode : trois tâches Python externes, trois sessions indépendantes par tâche
et condition, `gpt-6-sol` en effort `medium`, clones issus du même commit,
prompts et outils identiques. Les neuf runs actifs retenus ont tous eu des
sorties d'outils réellement tronquées. Détails et résultats bruts :
[BENCHMARKS.md](BENCHMARKS.md).

Résultat : les 18 runs retenus ont réussi les tests d'acceptation. Les runs
actifs ont consommé en moyenne 176 837 tokens d'entrée contre 124 240 en
baseline, avec une durée moyenne de 77,8 s contre 48,0 s. Les crédits facturés
par run ne sont pas disponibles; les caractères retirés ne mesurent pas une
économie de crédits.

Verdict : aucune économie de tokens observée dans cette série. Le coût moyen
facturé par tâche réussie ne peut pas être évalué sans relevé de facturation.
Les autres leviers de Token Diet n'ont pas été évalués dans cette expérience.
