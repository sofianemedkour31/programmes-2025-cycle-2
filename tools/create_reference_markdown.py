from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "reference"
GENERATOR = ROOT / "tools" / "generate_programmes_2025_html.py"


def entry_key(subject: str, grade: str, domain: str, global_competency: str) -> tuple[str, str, str, str]:
    return subject, grade, domain, global_competency


OVERRIDES = {
    entry_key("Français", "CE1", "Écriture", "Produire des écrits"): [
        "Rédiger une phrase simple à partir d’une phrase prototypique, en changeant un puis plusieurs mots.",
        "Écrire un texte court de une à trois phrases.",
        "Insérer des connecteurs pour rendre cohérent l’enchainement de plusieurs phrases.",
        "Retravailler un texte (issu de lecture et/ou d’écriture) en fonction d’une ou deux contraintes d’écriture.",
        "Continuer à acquérir une méthodologie de production écrite : planification, mise en mots avec vigilance orthographique, révision après retours immédiats du professeur.",
        "Écrire un texte de six ou sept phrases maximum en assurant la cohérence syntaxique et logique du texte produit.",
    ],
    entry_key("Mathématiques", "CP", "Nombres, calcul et résolution de problèmes", "Apprendre des procédures de calcul mental"): [
        "Ajouter ou soustraire 1 ou 2 à un nombre.",
        "Ajouter ou soustraire 10 à un nombre.",
        "Ajouter ou soustraire 20, 30, 40, 50, 60, 70, 80 ou 90 à un nombre.",
        "Ajouter un nombre inférieur à 9 à un nombre.",
        "Ajouter 9 à un nombre.",
        "Ajouter deux nombres inférieurs à 100.",
        "Déterminer la moitié d’un nombre pair.",
        "Soustraire un nombre inférieur à 10 à un nombre entier de dizaines.",
    ],
    entry_key("Mathématiques", "CP", "Nombres, calcul et résolution de problèmes", "La résolution de problèmes"): [
        "Résoudre des problèmes additifs en une étape.",
        "Résoudre des problèmes additifs en deux étapes.",
        "Résoudre des problèmes multiplicatifs en une étape (champ numérique inférieur ou égal à 30).",
    ],
    entry_key("Mathématiques", "CP", "Grandeurs et mesures", "Les masses"): [
        "Utiliser le lexique associé aux masses.",
        "Comparer des objets selon leur masse.",
    ],
    entry_key("Mathématiques", "CE1", "Nombres, calcul et résolution de problèmes", "Utiliser ses connaissances en numération pour calculer mentalement"): [
        "Ajouter ou soustraire un nombre entier de dizaines à un nombre. Ajouter ou soustraire un nombre entier de centaines à un nombre.",
        "Multiplier par 10 un nombre inférieur à 100.",
    ],
    entry_key("Mathématiques", "CE1", "Nombres, calcul et résolution de problèmes", "Apprendre des procédures de calcul mental"): [
        "Ajouter 9, 19 ou 29 à un nombre.",
        "Soustraire 9 à un nombre.",
        "Soustraire un nombre inférieur à 9 à un nombre.",
        "Déterminer la moitié d’un nombre pair.",
        "Calculer le produit d’un nombre compris entre 11 et 19 par un nombre inférieur à 10 en décomposant le plus grand des deux facteurs en la somme de deux nombres (propriété de distributivité de la multiplication par rapport à l’addition).",
    ],
    entry_key("Mathématiques", "CE1", "Nombres, calcul et résolution de problèmes", "La résolution de problèmes"): [
        "Résoudre des problèmes additifs en une étape de type parties-tout.",
        "Résoudre des problèmes additifs de comparaison en une étape.",
        "Résoudre des problèmes additifs en deux étapes.",
        "Résoudre des problèmes multiplicatifs en une étape.",
        "Résoudre des problèmes mixtes en deux étapes (une étape additive et une étape multiplicative).",
    ],
    entry_key("Mathématiques", "CE1", "Grandeurs et mesures", "Les masses"): [
        "Savoir identifier l’objet le plus léger (ou le plus lourd) parmi deux ou trois objets de volumes proches en les soupesant ou en utilisant une balance pour les peser.",
        "Connaitre et utiliser les unités gramme et kilogramme et les symboles associés (g, kg).",
        "Savoir que 1 kg est égal à 1 000 g.",
        "Comparer des masses.",
        "Disposer de quelques masses de référence. Estimer la masse d’objets du quotidien en gramme ou en kilogramme.",
    ],
    entry_key("Mathématiques", "CE1", "Grandeurs et mesures", "Le repérage dans le temps et les durées"): [
        "Lire l’heure sur une horloge à aiguilles (lorsque l’heure est donnée en heures entières, en heures et demi-heure ou en heures et quarts d’heure).",
        "Connaitre, utiliser et distinguer les heures du matin et celles de l’après-midi.",
        "Connaitre les unités de mesure de durée, heure et minute, et les symboles associés (h et min).",
        "Comparer et mesurer des durées écoulées entre deux instants affichés sur une horloge (pour des intervalles de temps situés dans une même journée, avec des heures données en heures entières, en heures et demi-heure ou en heures et quarts d’heure).",
    ],
    entry_key("Mathématiques", "CE1", "Espace et géométrie", "Le repérage dans l’espace"): [
        "Connaitre et utiliser le vocabulaire lié aux positions relatives.",
        "Situer des personnes ou des objets les uns par rapport aux autres ou par rapport à d’autres repères dans un espace familier.",
        "Construire et utiliser des représentations d’un espace familier pour localiser, mémoriser ou communiquer un emplacement.",
        "Construire des assemblages de cubes et de pavés.",
        "Comprendre, utiliser et produire une suite d’instructions qui codent un déplacement en utilisant un vocabulaire spatial précis.",
    ],
    entry_key("Mathématiques", "CE2", "Nombres, calcul et résolution de problèmes", "Apprendre des procédures de calcul mental"): [
        "Ajouter 8, 9, 18, 19, 28, 29, 38 ou 39 à un nombre.",
        "Soustraire 9, 19, 29 ou 39 à un nombre.",
        "Multiplier un nombre entier par 4 ou par 8.",
        "Multiplier un nombre inférieur à 10 par un nombre entier de dizaines.",
        "Calculer le produit d’un nombre compris entre 11 et 99 par un nombre inférieur à 10 en décomposant le plus grand des deux facteurs en la somme de deux nombres (propriété de distributivité de la multiplication par rapport à l’addition).",
    ],
    entry_key("Mathématiques", "CE2", "Grandeurs et mesures", "Les contenances"): [
        "Comparer les contenances de différents objets.",
        "Connaitre et utiliser les unités litre, décilitre et centilitre et les symboles associés (L, dL et cL).",
        "Savoir que 1 L est égal à 10 dL et également à 100 cL.",
    ],
    entry_key("Mathématiques", "CE2", "Grandeurs et mesures", "Les masses"): [
        "Connaitre et utiliser les unités gramme, kilogramme et tonne et les symboles associés (g, kg, t).",
        "Choisir l’unité la mieux adaptée pour exprimer une masse.",
        "Connaitre les relations entre les unités de masse usuelles.",
        "Comparer des masses.",
        "Disposer de quelques masses de référence.",
        "Estimer la masse d’un objet.",
    ],
    entry_key("Mathématiques", "CE2", "Organisation et gestion de données", "Organisation et gestion de données"): [
        "Produire un tableau ou un diagramme en barres pour présenter des données recueillies.",
        "Lire et interpréter les données d’un tableau à double entrée ou d’un diagramme en barres.",
        "Résoudre des problèmes en utilisant les données d’un tableau à double entrée ou d’un diagramme en barres.",
    ],
}


def clean_item(value: str) -> str:
    fixes = {
        " en A fonction ": " en fonction ",
        " en E assurant ": " en assurant ",
        "vigilance.-orthographique": "vigilance orthographique",
        "texte-produit": "texte produit",
        "Connaitre la notion de parité L d’un nombre. L": "Connaitre la notion de parité d’un nombre.",
        "(.!?)": "(. ! ?)",
    }
    for bad, good in fixes.items():
        value = value.replace(bad, good)
    return " ".join(value.split())


def load_pdf_data() -> list[dict]:
    spec = importlib.util.spec_from_file_location("programmes_generator", GENERATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError("Impossible de charger le générateur.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.REFERENCE_DIR = ROOT / "__reference_missing__"
    return module.build_data()


def build_reference_entries() -> list[dict]:
    entries = []
    seen = set()

    for entry in load_pdf_data():
        key = entry_key(entry["subject"], entry["grade"], entry["domain"], entry["globalCompetency"])
        specifics = OVERRIDES.get(key, entry["specifics"])
        specifics = [clean_item(item) for item in specifics]
        specifics = [item for item in specifics if item]
        if not specifics or key in seen:
            continue
        entries.append({
            "subject": entry["subject"],
            "domain": entry["domain"],
            "grade": entry["grade"],
            "globalCompetency": entry["globalCompetency"],
            "specifics": specifics,
        })
        seen.add(key)

    for key, specifics in OVERRIDES.items():
        if key in seen:
            continue
        subject, grade, domain, global_competency = key
        entries.append({
            "subject": subject,
            "domain": domain,
            "grade": grade,
            "globalCompetency": global_competency,
            "specifics": specifics,
        })
        seen.add(key)

    grade_order = {"CP": 0, "CE1": 1, "CE2": 2}
    subject_order = {"Français": 0, "Mathématiques": 1}
    return sorted(entries, key=lambda entry: (
        subject_order.get(entry["subject"], 9),
        entry["domain"],
        grade_order.get(entry["grade"], 9),
        entry["globalCompetency"],
    ))


def write_markdown(entries: list[dict], subject: str, filename: str) -> None:
    lines = [f"# {subject}", ""]
    current_domain = None
    for entry in [item for item in entries if item["subject"] == subject]:
        if entry["domain"] != current_domain:
            current_domain = entry["domain"]
            lines.extend([f"## {current_domain}", ""])
        lines.append(f"### {entry['grade']} — {entry['globalCompetency']}")
        for item in entry["specifics"]:
            lines.append(f"- {item}")
        lines.append("")
    (REFERENCE_DIR / filename).write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    REFERENCE_DIR.mkdir(exist_ok=True)
    entries = build_reference_entries()
    write_markdown(entries, "Français", "francais.md")
    write_markdown(entries, "Mathématiques", "mathematiques.md")
    print(f"Entrées : {len(entries)}")
    print(f"Compétences spécifiques : {sum(len(entry['specifics']) for entry in entries)}")


if __name__ == "__main__":
    main()
