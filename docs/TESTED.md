# Ce qu'on a teste

Aucun resultat chiffre pour l'instant : c'est un protocole, pas un bilan.
Les verdicts ci-dessous sont des INTENTIONS, pas des mesures.

## Format

    ### <levier>
    Hypothese :
    Methode : tache, modele, repetitions
    Resultat : chiffre + variance
    Verdict : retenu | ecarte | a retester

## A tester

### Troncature des sorties d'outils
Hypothese : gain de volume immediat.
Methode : `tkn proxy` en observation, puis `tkn report --stats`.
Limite : comparer des tailles prouve une baisse de VOLUME. Ca ne prouve ni
une baisse de facture, ni le maintien du taux de reussite. Il faut les deux.

### "Ne relis jamais un fichier"
Hypothese : gain de contexte.
Risque : erreurs sur des fichiers modifies, donc allers-retours qui coutent
plus que la relecture economisee.
C'est l'intuition la plus faible du lot.

### Zero prose / noms courts
Hypothese : moins de tokens.
Risque : cout de maintenance, invisible dans les mesures de tokens.

### Dialecte compresse
Hypothese : moins de tokens de sortie.
Candidat n1 au titre de placebo.

## Verdicts a rendre

| Levier | Mesure ? |
|---|---|
| Troncature des sorties d'outils | non |
| Ne pas relire | non |
| Zero prose | non |
| Noms courts | non |
| Dialecte compresse | non |
