# Programmes 2025 - Cycle 2

Application HTML statique pour explorer les programmes 2025 de français et de mathématiques au cycle 2.

## Fonctionnalités

- Filtres par matière, niveau, domaine, compétence globale et compétence spécifique.
- Vue détaillée avec progression CP, CE1 et CE2.
- Vue synthétique sur les trois niveaux.
- Recherche par mot-clé.

## Publication

Le fichier `index.html` est autonome et peut être publié avec GitHub Pages.

Les fichiers `reference/francais.md` et `reference/mathematiques.md` servent de source relue pour les compétences affichées.

Le script `tools/generate_programmes_2025_html.py` sert à régénérer l'application depuis ces fichiers Markdown.
