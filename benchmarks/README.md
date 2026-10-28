# Projets reproductibles du benchmark

Les trois fichiers `.bundle` contiennent chacun l'historique Git complet d'un
petit projet indépendant, figé avant toute résolution. Pour les cloner depuis
la racine de `token_diet` :

```sh
git clone -b main benchmarks/fixtures/invoice_bug.bundle /tmp/td-invoice-bug
git clone -b main benchmarks/fixtures/order_refactor.bundle /tmp/td-order-refactor
git clone -b main benchmarks/fixtures/task_api.bundle /tmp/td-task-api
```

| Projet | Commit initial | Prompt exact |
|---|---|---|
| A, facturation | `66ac2ffc67e0a1086e8ce16a65c4c592dfe67d26` | « Corrige le calcul des factures pour garantir que les remises, la TVA et les arrondis monétaires produisent les résultats attendus. Ajoute les tests de régression nécessaires, sans modifier les règles fonctionnelles. » |
| B, commandes CSV | `21197a7aefa882dc7b5e0b0e7d3d7f12d3ef57fe` | « Refactorise le traitement des commandes pour réduire les duplications et améliorer la lisibilité, sans modifier l'API publique ni les résultats produits. » |
| C, API Flask | `3a84583d9d1528d042817ab3c09f29449172b50f` | « Ajoute à l'endpoint GET /tasks un filtre par statut et une pagination avec limit et offset. Prévois la validation des paramètres, des réponses JSON cohérentes et des tests d'intégration. » |

Chaque run du [rapport](../docs/BENCHMARKS.md) a cloné de nouveau le projet
concerné. Les sessions utilisaient `codex exec --ephemeral --ignore-user-config`
avec `-m gpt-6-sol -c 'model_reasoning_effort="medium"'`, la CLI
`0.162.0-alpha.17.2`, Python 3.12, pytest 9.2.0 et Flask 3.1.3 pour C. Le
proxy local était lancé avec `--mode actif --limit 1000` et le fournisseur
Codex configuré explicitement en `wire_api="responses"`, avec une URL de base
pointant vers le proxy. Les journaux et le script de lancement utilisés sont
conservés localement sous `/home/natty/token_diet_benchmarks/`.

Pour répéter la comparaison, crée un nouveau clone du bundle pour chaque run,
utilise le prompt exact du tableau et relève l'événement `turn.completed`, les
tests d'acceptation figés et les compteurs de réécriture du proxy. L'ordre
utilisé était baseline/actif, actif/baseline, baseline/actif pour chaque tâche.
Le routage vers le proxy doit être vérifié à chaque série : une session qui le
traverse sans réécriture ne mesure pas l'effet de Token Diet.
