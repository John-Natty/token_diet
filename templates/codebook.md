# Dialecte comprime

Statut : HYPOTHESE. Non mesure. Candidat n1 au titre de placebo.

## Sortie
Reponds en anglais telegraphique. Pas d'articles, pas de pronoms.

## Notation de patch
    +   ajoute la ligne
    -   supprime la ligne
    ~   remplace
    @@  fichier:ligne

    @@ src/auth.ts:45
    ~ retry(3)
    + backoff(2 ** n, cap=30_000)

## Decodeur
`scripts/decode.py`, a ecrire une fois.