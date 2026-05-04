from __future__ import annotations

import json
import re
from pathlib import Path

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT.parent / "programmes-cycle-2-rentree-2025"
OUTPUT = ROOT / "index.html"

GRADES = {
    "Cours préparatoire": "CP",
    "Cours élémentaire première année": "CE1",
    "Cours élémentaire deuxième année": "CE2",
}

PROGRAMS = [
    {
        "subject": "Français",
        "file": "01-programme-francais-cycle-2-rentree-2025.pdf",
        "domains": {
            "Lecture": [
                "Identifier les mots de manière de plus en plus aisée",
                "Lire à voix haute",
                "Comprendre un texte",
                "Devenir lecteur",
            ],
            "Écriture": [
                "Apprendre à écrire en écriture cursive",
                "Encoder puis écrire sous dictée",
                "Copier et acquérir des stratégies de copie",
                "Produire des écrits",
            ],
            "Oral": [
                "Écouter pour comprendre",
                "Dire pour être compris",
                "Participer à des échanges",
            ],
            "Vocabulaire": [
                "Enrichir son vocabulaire dans tous les enseignements",
                "Enrichir son vocabulaire dans toutes les disciplines",
                "Établir des relations entre les mots",
                "Réemployer le vocabulaire étudié",
                "Mémoriser l’orthographe lexicale",
                "Mémoriser l’orthographe des mots",
            ],
            "Grammaire et orthographe": [
                "Se repérer dans la phrase simple",
                "Découvrir, comprendre et mettre en œuvre l’orthographe grammaticale",
            ],
        },
    },
    {
        "subject": "Mathématiques",
        "file": "02-programme-mathematiques-cycle-2-rentree-2025.pdf",
        "domains": {
            "Nombres, calcul et résolution de problèmes": [
                "Les nombres entiers",
                "Les fractions",
                "Les quatre opérations",
                "Le calcul mental",
                "Mémoriser des faits numériques",
                "Utiliser ses connaissances en numération pour calculer mentalement",
                "Apprendre des procédures de calcul mental",
                "La résolution de problèmes",
            ],
            "Grandeurs et mesures": [
                "Les longueurs et les masses",
                "Les longueurs, les masses et les contenances",
                "Les longueurs",
                "Les masses",
                "Les contenances",
                "La monnaie",
                "Le repérage dans le temps",
                "Le repérage dans le temps et les durées",
            ],
            "Espace et géométrie": [
                "Les solides",
                "La géométrie plane",
                "Le repérage dans l’espace",
            ],
            "Organisation et gestion de données": [
                "Organisation et gestion de données",
            ],
        },
    },
]


def clean_line(line: str) -> str:
    return re.sub(r"\s+", " ", line).strip()


def extract_pdf_text(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))
    pages = []
    for page in reader.pages[2:]:
        pages.append(page.extract_text(extraction_mode="layout") or "")
    return "\n".join(pages)


def split_entries(program: dict) -> list[dict]:
    text = extract_pdf_text(SOURCE_DIR / program["file"])
    domain_names = set(program["domains"])
    headings = {
        heading: domain
        for domain, values in program["domains"].items()
        for heading in values
    }
    entries: list[dict] = []
    current_domain = None
    current_grade = None
    current_entry = None

    def flush() -> None:
        nonlocal current_entry
        if current_entry:
            current_entry["text"] = "\n".join(current_entry.pop("_lines")).strip()
            current_entry["specifics"] = extract_specific_objectives(current_entry["text"])
            entries.append(current_entry)
            current_entry = None

    for raw_line in text.splitlines():
        line = clean_line(raw_line)
        if not line:
            if current_entry:
                current_entry["_lines"].append("")
            continue

        if line in domain_names:
            flush()
            current_domain = line
            current_grade = None
            continue

        if line in GRADES:
            flush()
            current_grade = GRADES[line]
            if current_domain == "Organisation et gestion de données":
                current_entry = {
                    "subject": program["subject"],
                    "source": program["file"],
                    "domain": current_domain,
                    "grade": current_grade,
                    "globalCompetency": current_domain,
                    "_lines": [],
                }
            continue

        if (
            current_domain
            and current_grade
            and line in headings
            and headings[line] == current_domain
            and not (line == current_domain == "Organisation et gestion de données")
        ):
            flush()
            current_entry = {
                "subject": program["subject"],
                "source": program["file"],
                "domain": current_domain,
                "grade": current_grade,
                "globalCompetency": line,
                "_lines": [],
            }
            continue

        if current_entry:
            current_entry["_lines"].append(raw_line.rstrip())

    flush()
    return entries


def extract_specific_objectives(section_text: str) -> list[str]:
    objectives: list[str] = []
    current = ""
    in_objectives = False
    split_at = 76

    for raw_line in section_text.splitlines():
        if "Objectifs d’apprentissage" in raw_line:
            in_objectives = True
            if "Exemples de réussite" in raw_line:
                split_at = raw_line.index("Exemples de réussite")
            continue
        if not in_objectives:
            continue

        left = raw_line[:split_at].strip()
        if not left:
            continue
        if left.startswith("Exemples de réussite"):
            continue
        if left in {"En fin de période 1", "En milieu d’année", "En fin d’année", "Dès le début de l’année", "En cours d’année", "Tout au long de l’année"}:
            continue
        if left.startswith("- "):
            if current:
                objectives.append(normalize_objective(current))
            current = left[2:].strip()
        elif current and not left.startswith(("", "")):
            current += " " + left

    if current:
        objectives.append(normalize_objective(current))

    deduped = []
    seen = set()
    for objective in objectives:
        objective = objective.strip(" -")
        if len(objective) < 5 or looks_like_success_example(objective):
            continue
        key = objective.casefold()
        if key not in seen:
            seen.add(key)
            deduped.append(objective)
    return deduped


def looks_like_success_example(value: str) -> bool:
    lowered = value.casefold()
    example_starts = (
        "l’élève ",
        "l'eleve ",
        "l' élève ",
        "il ",
        "elle ",
        "les collections ",
        "face à ",
        "par exemple",
        "sur son ardoise",
        "à la fin",
    )
    if lowered.startswith(example_starts):
        return True
    return any(fragment in lowered for fragment in (
        "l’élève sait",
        "l’élève comprend",
        "l’élève est capable",
        "l’élève peut",
        "l’élève montre",
        "l’élève utilise",
    ))


def normalize_objective(value: str) -> str:
    value = re.sub(r"\s+", " ", value)
    value = value.replace(" - ", "-")
    value = value.replace("  ", " ")
    return value.strip()


def build_data() -> list[dict]:
    all_entries: list[dict] = []
    for program in PROGRAMS:
        all_entries.extend(split_entries(program))
    return all_entries


def render_html(data: list[dict]) -> str:
    public_data = [
        {
            "subject": entry["subject"],
            "domain": entry["domain"],
            "grade": entry["grade"],
            "globalCompetency": entry["globalCompetency"],
            "specifics": entry["specifics"],
        }
        for entry in data
    ]
    payload = json.dumps(public_data, ensure_ascii=False)
    payload = payload.replace("<", "\\u003c").replace("</", "<\\/")
    subjects = sorted({entry["subject"] for entry in data})
    domains = sorted({entry["domain"] for entry in data})
    grades = ["CP", "CE1", "CE2"]
    stat_specifics = sum(len(entry["specifics"]) for entry in data)

    return f"""<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Programmes 2025 - Cycle 2 | Français et Mathématiques</title>
  <style>
    :root {{
      --ink: #172033;
      --muted: #667085;
      --soft: #eef4ff;
      --paper: #f4f7fb;
      --panel: rgba(255, 255, 255, .68);
      --panel-strong: rgba(255, 255, 255, .84);
      --line: rgba(121, 139, 169, .28);
      --blue: #2f6fed;
      --cyan: #18a6b8;
      --green: #1f8a70;
      --amber: #b96f16;
      --rose: #b84072;
      --shadow: 0 24px 70px rgba(35, 48, 76, .16);
      --small-shadow: 0 10px 30px rgba(35, 48, 76, .11);
      --blur: blur(22px) saturate(150%);
    }}
    * {{ box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; }}
    body {{
      min-height: 100vh;
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at 12% 4%, rgba(47, 111, 237, .25), transparent 27rem),
        radial-gradient(circle at 86% 8%, rgba(24, 166, 184, .19), transparent 25rem),
        radial-gradient(circle at 74% 86%, rgba(184, 64, 114, .15), transparent 24rem),
        linear-gradient(135deg, #f8fbff 0%, #eef4f9 52%, #f9fbff 100%);
      background-attachment: fixed;
      letter-spacing: 0;
    }}
    body::before {{
      content: "";
      position: fixed;
      inset: 0;
      z-index: -1;
      pointer-events: none;
      opacity: .42;
      background-image:
        linear-gradient(rgba(23, 32, 51, .045) 1px, transparent 1px),
        linear-gradient(90deg, rgba(23, 32, 51, .04) 1px, transparent 1px);
      background-size: 34px 34px;
      mask-image: linear-gradient(180deg, #000 0%, transparent 75%);
    }}
    header {{
      padding: 34px clamp(18px, 4vw, 52px) 22px;
    }}
    .hero-shell {{
      overflow: hidden;
      position: relative;
      border: 1px solid rgba(255, 255, 255, .68);
      border-radius: 28px;
      padding: clamp(22px, 4vw, 42px);
      background: linear-gradient(135deg, rgba(255,255,255,.76), rgba(255,255,255,.44));
      box-shadow: var(--shadow);
      backdrop-filter: var(--blur);
      -webkit-backdrop-filter: var(--blur);
    }}
    .hero-shell::after {{
      content: "";
      position: absolute;
      right: clamp(18px, 6vw, 90px);
      top: -110px;
      width: 280px;
      height: 280px;
      border-radius: 50%;
      background: conic-gradient(from 130deg, rgba(47,111,237,.45), rgba(24,166,184,.22), rgba(184,64,114,.27), rgba(47,111,237,.45));
      filter: blur(32px);
      opacity: .55;
    }}
    h1 {{
      position: relative;
      margin: 0 0 12px;
      max-width: 840px;
      font-size: clamp(2.35rem, 5vw, 5.15rem);
      line-height: .94;
      letter-spacing: 0;
    }}
    .subhead {{
      position: relative;
      max-width: 980px;
      color: #475467;
      font-size: clamp(.98rem, 1.5vw, 1.12rem);
      line-height: 1.65;
    }}
    .stats {{
      position: relative;
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 22px;
    }}
    .pill, .tag {{
      border: 1px solid rgba(255,255,255,.7);
      border-radius: 999px;
      box-shadow: inset 0 1px 0 rgba(255,255,255,.7);
      backdrop-filter: var(--blur);
      -webkit-backdrop-filter: var(--blur);
    }}
    .pill {{
      background: rgba(255,255,255,.62);
      padding: 8px 12px;
      font-size: .88rem;
      font-weight: 760;
      color: #344054;
    }}
    main {{
      display: grid;
      grid-template-columns: minmax(280px, 360px) 1fr;
      gap: 24px;
      padding: 0 clamp(18px, 4vw, 52px) 44px;
      align-items: start;
      transition: grid-template-columns .28s ease, gap .28s ease;
    }}
    body.sidebar-collapsed main {{
      grid-template-columns: 0 minmax(0, 1fr);
      gap: 0;
    }}
    aside {{
      position: sticky;
      top: 16px;
      display: grid;
      gap: 16px;
      overflow: hidden;
      transition: opacity .22s ease, transform .24s ease, visibility .22s ease;
    }}
    body.sidebar-collapsed aside {{
      opacity: 0;
      transform: translateX(-18px);
      visibility: hidden;
      pointer-events: none;
    }}
    .panel, .card, .overview-card {{
      background: var(--panel);
      border: 1px solid rgba(255, 255, 255, .72);
      box-shadow: var(--small-shadow);
      backdrop-filter: var(--blur);
      -webkit-backdrop-filter: var(--blur);
    }}
    .panel {{
      padding: 16px;
      border-radius: 22px;
    }}
    .panel-title {{
      display: block;
      margin-bottom: 12px;
      font-size: .82rem;
      font-weight: 850;
      color: #344054;
      text-transform: uppercase;
    }}
    .view-switch {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 6px;
      padding: 5px;
      border-radius: 999px;
      background: rgba(255,255,255,.55);
      border: 1px solid rgba(255,255,255,.72);
    }}
    .view-switch button {{
      min-height: 38px;
      border-radius: 999px;
      border: 0;
      background: transparent;
      color: #475467;
      font-size: .88rem;
      font-weight: 850;
      box-shadow: none;
    }}
    .view-switch button.active {{
      color: #fff;
      background: linear-gradient(135deg, #2f6fed, #18a6b8);
      box-shadow: 0 9px 22px rgba(47,111,237,.25);
    }}
    .filters {{
      display: grid;
      gap: 12px;
    }}
    label {{
      display: grid;
      gap: 6px;
      font-size: .72rem;
      font-weight: 850;
      color: #526070;
      text-transform: uppercase;
    }}
    select, input {{
      width: 100%;
      min-height: 44px;
      border: 1px solid rgba(121, 139, 169, .3);
      border-radius: 14px;
      padding: 9px 12px;
      color: var(--ink);
      background: rgba(255,255,255,.72);
      box-shadow: inset 0 1px 0 rgba(255,255,255,.7);
      font: inherit;
      outline: none;
    }}
    select:focus, input:focus {{
      border-color: rgba(47,111,237,.56);
      box-shadow: 0 0 0 4px rgba(47,111,237,.13);
    }}
    button {{
      min-height: 44px;
      border: 1px solid rgba(121, 139, 169, .28);
      border-radius: 14px;
      padding: 9px 12px;
      background: rgba(255,255,255,.7);
      color: var(--ink);
      font-weight: 820;
      cursor: pointer;
      box-shadow: inset 0 1px 0 rgba(255,255,255,.65);
    }}
    button:hover {{ transform: translateY(-1px); background: rgba(255,255,255,.9); }}
    .primary-action {{
      color: #fff;
      border: 0;
      background: linear-gradient(135deg, #2f6fed, #18a6b8);
      box-shadow: 0 14px 28px rgba(47,111,237,.24);
    }}
    .tree {{
      max-height: calc(100vh - 390px);
      overflow: auto;
      padding-right: 4px;
    }}
    details {{
      border-top: 1px solid rgba(121,139,169,.18);
      padding: 8px 0;
    }}
    details:first-child {{ border-top: 0; }}
    summary {{
      cursor: pointer;
      font-weight: 860;
      line-height: 1.35;
    }}
    .tree button {{
      width: 100%;
      min-height: 0;
      margin: 5px 0 0;
      padding: 8px 10px;
      text-align: left;
      font-size: .86rem;
      font-weight: 680;
      background: rgba(255,255,255,.54);
    }}
    .toolbar {{
      position: sticky;
      top: 12px;
      z-index: 5;
      display: flex;
      gap: 10px;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 16px;
      padding: 10px;
      border: 1px solid rgba(255,255,255,.72);
      border-radius: 20px;
      background: rgba(255,255,255,.62);
      box-shadow: var(--small-shadow);
      backdrop-filter: var(--blur);
      -webkit-backdrop-filter: var(--blur);
    }}
    .count {{
      color: #475467;
      font-weight: 820;
      padding-left: 4px;
    }}
    .toolbar-actions {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      justify-content: flex-end;
    }}
    .ghost-action {{
      background: rgba(255,255,255,.58);
      color: #344054;
    }}
    .results {{
      display: grid;
      gap: 16px;
    }}
    .card {{
      overflow: hidden;
      position: relative;
      border-radius: 24px;
      padding: 20px;
    }}
    .card::before, .overview-card::before {{
      content: "";
      position: absolute;
      inset: 0 0 auto;
      height: 3px;
      background: linear-gradient(90deg, var(--blue), var(--cyan), var(--rose));
      opacity: .85;
    }}
    .meta {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 13px;
    }}
    .tag {{
      padding: 5px 9px;
      font-size: .75rem;
      font-weight: 850;
      color: #fff;
      background: var(--blue);
    }}
    .tag.math {{ background: var(--green); }}
    .tag.grade {{ background: var(--amber); }}
    .tag.domain {{ background: var(--rose); }}
    h2 {{
      margin: 0 0 11px;
      font-size: clamp(1.28rem, 2vw, 1.8rem);
      line-height: 1.16;
      letter-spacing: 0;
    }}
    h3 {{
      margin: 0 0 9px;
      font-size: 1rem;
      letter-spacing: 0;
    }}
    .specifics {{
      display: grid;
      gap: 8px;
      margin: 14px 0;
      padding: 0;
      list-style: none;
    }}
    .specifics li {{
      border: 1px solid rgba(143,180,223,.35);
      border-left: 4px solid #6fa1e6;
      background: rgba(244,248,252,.72);
      padding: 10px 11px;
      border-radius: 12px;
      line-height: 1.45;
    }}
    .progression {{
      margin-top: 15px;
      padding: 14px;
      border-radius: 18px;
      background: rgba(255,255,255,.55);
      border: 1px solid rgba(121,139,169,.2);
    }}
    .progression-grid, .overview-grid {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
    }}
    .level-panel {{
      min-width: 0;
      border: 1px solid rgba(121,139,169,.2);
      border-radius: 16px;
      padding: 11px;
      background: rgba(255,255,255,.58);
    }}
    .level-panel.current {{
      border-color: rgba(47,111,237,.5);
      box-shadow: 0 0 0 4px rgba(47,111,237,.09);
    }}
    .level-panel h4 {{
      margin: 0 0 8px;
      font-size: .84rem;
      color: #344054;
    }}
    .mini-list {{
      margin: 0;
      padding-left: 17px;
      color: #475467;
      font-size: .86rem;
      line-height: 1.42;
    }}
    .mini-list li + li {{ margin-top: 5px; }}
    .muted {{ color: var(--muted); }}
    .overview-card {{
      position: relative;
      overflow: hidden;
      border-radius: 24px;
      padding: 20px;
    }}
    .overview-top {{
      display: flex;
      justify-content: space-between;
      gap: 14px;
      margin-bottom: 14px;
      align-items: flex-start;
    }}
    .analysis {{
      margin: 8px 0 0;
      color: #526070;
      line-height: 1.5;
    }}
    .view-hidden {{ display: none; }}
    mark {{
      background: rgba(255, 229, 143, .82);
      padding: 0 2px;
      border-radius: 4px;
    }}
    .empty {{
      padding: 34px;
      text-align: center;
      color: var(--muted);
      border: 1px dashed rgba(121,139,169,.5);
      border-radius: 22px;
      background: rgba(255,255,255,.58);
      backdrop-filter: var(--blur);
      -webkit-backdrop-filter: var(--blur);
    }}
    @media (max-width: 980px) {{
      main, body.sidebar-collapsed main {{ grid-template-columns: 1fr; gap: 16px; }}
      aside {{ position: static; }}
      body.sidebar-collapsed aside {{ display: none; }}
      .tree {{ max-height: none; }}
      .toolbar {{ position: static; align-items: flex-start; flex-direction: column; }}
      .toolbar-actions {{ width: 100%; justify-content: stretch; }}
      .toolbar-actions button {{ flex: 1; }}
    }}
    @media (max-width: 720px) {{
      header {{ padding: 16px; }}
      main {{ padding: 0 16px 30px; }}
      .hero-shell {{ border-radius: 22px; padding: 22px; }}
      .progression-grid, .overview-grid {{ grid-template-columns: 1fr; }}
      .overview-top {{ flex-direction: column; }}
    }}
    @media print {{
      body {{ background: #fff; }}
      aside, .toolbar {{ display: none; }}
      main {{ display: block; padding: 0; }}
      header {{ padding: 0 0 16px; }}
      .hero-shell, .card, .overview-card {{ break-inside: avoid; box-shadow: none; border: 1px solid #ddd; }}
    }}
  </style>
</head>
<body>
  <header>
    <div class="hero-shell">
      <h1>Programmes 2025 - Cycle 2</h1>
      <p class="subhead">Compilation interactive des programmes de français et de mathématiques, organisée par niveau, domaine, compétence globale et compétences spécifiques. Les cartes de progression permettent de comparer rapidement CP, CE1 et CE2 sans quitter la compétence étudiée.</p>
    </div>
  </header>
  <main>
    <aside>
      <section class="panel">
        <span class="panel-title">Vue</span>
        <div class="view-switch" role="tablist" aria-label="Mode d'affichage">
          <button id="detailViewButton" class="active" type="button" onclick="setView('detail')">Détail</button>
          <button id="overviewViewButton" type="button" onclick="setView('overview')">Synthèse</button>
        </div>
      </section>
      <section class="panel filters" aria-label="Filtres">
        <label>Matière
          <select id="subjectFilter"></select>
        </label>
        <label>Niveau
          <select id="gradeFilter"></select>
        </label>
        <label>Domaine
          <select id="domainFilter"></select>
        </label>
        <label>Compétence globale
          <select id="globalFilter"></select>
        </label>
        <label>Compétence spécifique
          <select id="specificFilter"></select>
        </label>
        <label>Recherche
          <input id="searchFilter" type="search" placeholder="Mot-clé, notion, verbe...">
        </label>
        <button id="resetFilters" type="button">Réinitialiser les filtres</button>
      </section>
      <section class="panel">
        <strong>Menu dépliable</strong>
        <div id="tree" class="tree"></div>
      </section>
    </aside>
    <section>
      <div class="toolbar">
        <div class="count" id="resultCount"></div>
        <div class="toolbar-actions">
          <button id="toggleSidebarButton" class="ghost-action" type="button" aria-expanded="true">Masquer les filtres</button>
          <button id="printButton" class="primary-action" type="button">Imprimer / exporter en PDF</button>
        </div>
      </div>
      <div id="results" class="results"></div>
      <div id="overviewResults" class="results view-hidden"></div>
    </section>
  </main>
  <script id="program-data" type="application/json">{payload}</script>
  <script>
    const DATA = JSON.parse(document.getElementById('program-data').textContent);
    const GRADES = ['CP', 'CE1', 'CE2'];
    const state = {{
      view: 'detail',
      subject: '',
      grade: '',
      domain: '',
      global: '',
      specific: '',
      search: ''
    }};
    const el = id => document.getElementById(id);
    const controls = {{
      subject: el('subjectFilter'),
      grade: el('gradeFilter'),
      domain: el('domainFilter'),
      global: el('globalFilter'),
      specific: el('specificFilter'),
      search: el('searchFilter')
    }};
    const viewButtons = {{
      detail: el('detailViewButton'),
      overview: el('overviewViewButton')
    }};

    const groupKey = entry => [entry.subject, entry.domain, entry.globalCompetency].join('|||');
    const progressionIndex = DATA.reduce((acc, entry) => {{
      const key = groupKey(entry);
      acc[key] ??= {{}};
      acc[key][entry.grade] = entry;
      return acc;
    }}, {{}});

    function uniq(values) {{
      return [...new Set(values.filter(Boolean))].sort((a, b) => a.localeCompare(b, 'fr'));
    }}

    function optionList(select, values, label, current) {{
      select.innerHTML = '';
      select.append(new Option(label, ''));
      values.forEach(value => select.append(new Option(value, value)));
      select.value = values.includes(current) ? current : '';
    }}

    function matches(entry) {{
      if (state.subject && entry.subject !== state.subject) return false;
      if (state.grade && entry.grade !== state.grade) return false;
      if (state.domain && entry.domain !== state.domain) return false;
      if (state.global && entry.globalCompetency !== state.global) return false;
      if (state.specific && !entry.specifics.includes(state.specific)) return false;
      if (state.search) {{
        const haystack = [
          entry.subject, entry.grade, entry.domain, entry.globalCompetency,
          entry.specifics.join(' ')
        ].join(' ').toLocaleLowerCase('fr');
        if (!haystack.includes(state.search.toLocaleLowerCase('fr'))) return false;
      }}
      return true;
    }}

    function matchesOverview(group) {{
      const entries = GRADES.map(grade => group.byGrade[grade]).filter(Boolean);
      if (state.subject && !entries.some(entry => entry.subject === state.subject)) return false;
      if (state.grade && !group.byGrade[state.grade]) return false;
      if (state.domain && group.domain !== state.domain) return false;
      if (state.global && group.globalCompetency !== state.global) return false;
      if (state.specific && !entries.some(entry => entry.specifics.includes(state.specific))) return false;
      if (state.search) {{
        const haystack = entries.map(entry => [
          entry.subject, entry.grade, entry.domain, entry.globalCompetency,
          entry.specifics.join(' ')
        ].join(' ')).join(' ').toLocaleLowerCase('fr');
        if (!haystack.includes(state.search.toLocaleLowerCase('fr'))) return false;
      }}
      return true;
    }}

    function scopedData(level) {{
      return DATA.filter(entry => {{
        if (level !== 'subject' && state.subject && entry.subject !== state.subject) return false;
        if (level !== 'grade' && state.grade && entry.grade !== state.grade) return false;
        if (level !== 'domain' && state.domain && entry.domain !== state.domain) return false;
        if (level !== 'global' && state.global && entry.globalCompetency !== state.global) return false;
        return true;
      }});
    }}

    function refreshOptions() {{
      optionList(controls.subject, uniq(scopedData('subject').map(e => e.subject)), 'Toutes les matières', state.subject);
      state.subject = controls.subject.value;
      optionList(controls.grade, GRADES, state.view === 'overview' ? 'Tous les niveaux de la synthèse' : 'Tous les niveaux', state.grade);
      state.grade = controls.grade.value;
      optionList(controls.domain, uniq(scopedData('domain').map(e => e.domain)), 'Tous les domaines', state.domain);
      state.domain = controls.domain.value;
      optionList(controls.global, uniq(scopedData('global').map(e => e.globalCompetency)), 'Toutes les compétences globales', state.global);
      state.global = controls.global.value;
      optionList(controls.specific, uniq(scopedData('specific').flatMap(e => e.specifics)), 'Toutes les compétences spécifiques', state.specific);
      state.specific = controls.specific.value;
    }}

    function getOverviewGroups() {{
      const groups = {{}};
      DATA.forEach(entry => {{
        const key = groupKey(entry);
        groups[key] ??= {{
          key,
          subject: entry.subject,
          domain: entry.domain,
          globalCompetency: entry.globalCompetency,
          byGrade: {{}}
        }};
        groups[key].byGrade[entry.grade] = entry;
      }});
      return Object.values(groups).sort((a, b) =>
        a.subject.localeCompare(b.subject, 'fr') ||
        a.domain.localeCompare(b.domain, 'fr') ||
        a.globalCompetency.localeCompare(b.globalCompetency, 'fr')
      );
    }}

    function relevantSpecifics(entry, limit = 5) {{
      if (!entry) return [];
      let specifics = entry.specifics;
      if (state.specific) specifics = specifics.filter(item => item === state.specific);
      if (state.search) {{
        const q = state.search.toLocaleLowerCase('fr');
        const matched = specifics.filter(item => item.toLocaleLowerCase('fr').includes(q));
        if (matched.length) specifics = matched;
      }}
      return specifics.slice(0, limit);
    }}

    function progressionFor(entry) {{
      return progressionIndex[groupKey(entry)] || {{}};
    }}

    function progressionSentence(group) {{
      const present = GRADES.filter(grade => group.byGrade[grade]);
      const counts = present.map(grade => `${{grade}} : ${{group.byGrade[grade].specifics.length}} objectif${{group.byGrade[grade].specifics.length > 1 ? 's' : ''}}`);
      if (present.length === 3) return `Progression continue sur les trois niveaux. ${{counts.join(' · ')}}.`;
      return `Présence partielle dans le programme extrait : ${{present.join(', ') || 'aucun niveau'}}. ${{counts.join(' · ')}}.`;
    }}

    function levelPanel(entry, grade, currentGrade = '') {{
      if (!entry) {{
        return `<section class="level-panel"><h4>${{grade}}</h4><p class="muted">Pas d'entrée équivalente isolée pour ce niveau.</p></section>`;
      }}
      const items = relevantSpecifics(entry, 4);
      return `
        <section class="level-panel ${{grade === currentGrade ? 'current' : ''}}">
          <h4>${{grade}}</h4>
          ${{items.length
            ? `<ul class="mini-list">${{items.map(item => `<li>${{highlight(item)}}</li>`).join('')}}</ul>`
            : '<p class="muted">Consultez le texte officiel extrait.</p>'}}
        </section>
      `;
    }}

    function highlight(text) {{
      const escaped = escapeHtml(text);
      if (!state.search) return escaped;
      const needle = state.search.replace(/[.*+?^${{}}()|[\\]\\\\]/g, '\\\\$&');
      return escaped.replace(new RegExp(`(${{needle}})`, 'gi'), '<mark>$1</mark>');
    }}

    function escapeHtml(value) {{
      return String(value).replace(/[&<>"']/g, char => ({{
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'
      }}[char]));
    }}

    function renderResults() {{
      const rows = DATA.filter(matches);
      el('resultCount').textContent = `${{rows.length}} résultat${{rows.length > 1 ? 's' : ''}}`;
      el('results').classList.remove('view-hidden');
      el('overviewResults').classList.add('view-hidden');
      if (!rows.length) {{
        el('results').innerHTML = '<div class="empty">Aucune compétence ne correspond aux filtres sélectionnés.</div>';
        return;
      }}
      el('results').innerHTML = rows.map(entry => `
        <article class="card">
          <div class="meta">
            <span class="tag ${{entry.subject === 'Mathématiques' ? 'math' : ''}}">${{escapeHtml(entry.subject)}}</span>
            <span class="tag grade">${{escapeHtml(entry.grade)}}</span>
            <span class="tag domain">${{escapeHtml(entry.domain)}}</span>
          </div>
          <h2>${{highlight(entry.globalCompetency)}}</h2>
          <ul class="specifics">
            ${{entry.specifics.length
              ? entry.specifics.map(item => `<li>${{highlight(item)}}</li>`).join('')
              : '<li>Objectifs spécifiques non isolés automatiquement ; consultez le texte officiel extrait.</li>'}}
          </ul>
          <section class="progression">
            <h3>Progression CP · CE1 · CE2</h3>
            <div class="progression-grid">
              ${{GRADES.map(grade => levelPanel(progressionFor(entry)[grade], grade, entry.grade)).join('')}}
            </div>
          </section>
        </article>
      `).join('');
    }}

    function renderOverview() {{
      const groups = getOverviewGroups().filter(matchesOverview);
      el('resultCount').textContent = `${{groups.length}} synthèse${{groups.length > 1 ? 's' : ''}}`;
      el('results').classList.add('view-hidden');
      el('overviewResults').classList.remove('view-hidden');
      if (!groups.length) {{
        el('overviewResults').innerHTML = '<div class="empty">Aucune synthèse ne correspond aux filtres sélectionnés.</div>';
        return;
      }}
      el('overviewResults').innerHTML = groups.map(group => `
        <article class="overview-card">
          <div class="overview-top">
            <div>
              <div class="meta">
                <span class="tag ${{group.subject === 'Mathématiques' ? 'math' : ''}}">${{escapeHtml(group.subject)}}</span>
                <span class="tag domain">${{escapeHtml(group.domain)}}</span>
              </div>
              <h2>${{highlight(group.globalCompetency)}}</h2>
              <p class="analysis">${{escapeHtml(progressionSentence(group))}}</p>
            </div>
            <button type="button" data-overview-key="${{escapeHtml(group.key)}}">Voir en détail</button>
          </div>
          <div class="overview-grid">
            ${{GRADES.map(grade => levelPanel(group.byGrade[grade], grade, state.grade)).join('')}}
          </div>
        </article>
      `).join('');
      el('overviewResults').querySelectorAll('button[data-overview-key]').forEach(button => {{
        button.addEventListener('click', () => {{
          const group = getOverviewGroups().find(item => item.key === button.dataset.overviewKey);
          if (!group) return;
          state.view = 'detail';
          state.subject = group.subject;
          state.domain = group.domain;
          state.global = group.globalCompetency;
          state.specific = '';
          refreshOptions();
          renderCurrentView();
          window.scrollTo({{ top: 0, behavior: 'smooth' }});
        }});
      }});
    }}

    function renderCurrentView() {{
      viewButtons.detail.classList.toggle('active', state.view === 'detail');
      viewButtons.overview.classList.toggle('active', state.view === 'overview');
      if (state.view === 'overview') renderOverview();
      else renderResults();
    }}

    function setView(view) {{
      state.view = view;
      refreshOptions();
      renderCurrentView();
    }}

    function renderTree() {{
      const grouped = {{}};
      DATA.forEach(entry => {{
        grouped[entry.subject] ??= {{}};
        grouped[entry.subject][entry.grade] ??= {{}};
        grouped[entry.subject][entry.grade][entry.domain] ??= [];
        grouped[entry.subject][entry.grade][entry.domain].push(entry);
      }});
      el('tree').innerHTML = Object.entries(grouped).map(([subject, byGrade]) => `
        <details open>
          <summary>${{escapeHtml(subject)}}</summary>
          ${{Object.entries(byGrade).map(([grade, byDomain]) => `
            <details>
              <summary>${{escapeHtml(grade)}}</summary>
              ${{Object.entries(byDomain).map(([domain, entries]) => `
                <details>
                  <summary>${{escapeHtml(domain)}}</summary>
                  ${{entries.map(entry => `<button type="button" data-subject="${{escapeHtml(subject)}}" data-grade="${{escapeHtml(grade)}}" data-domain="${{escapeHtml(domain)}}" data-global="${{escapeHtml(entry.globalCompetency)}}">${{escapeHtml(entry.globalCompetency)}}</button>`).join('')}}
                </details>
              `).join('')}}
            </details>
          `).join('')}}
        </details>
      `).join('');
      el('tree').querySelectorAll('button').forEach(button => {{
        button.addEventListener('click', () => {{
          state.subject = button.dataset.subject;
          state.grade = button.dataset.grade;
          state.domain = button.dataset.domain;
          state.global = button.dataset.global;
          state.specific = '';
          state.search = '';
          controls.search.value = '';
          refreshOptions();
          renderCurrentView();
          window.scrollTo({{ top: 0, behavior: 'smooth' }});
        }});
      }});
    }}

    Object.entries(controls).forEach(([key, control]) => {{
      control.addEventListener(key === 'search' ? 'input' : 'change', () => {{
        state[key] = control.value;
        refreshOptions();
        renderCurrentView();
      }});
    }});
    viewButtons.detail.addEventListener('click', () => {{
      setView('detail');
    }});
    viewButtons.overview.addEventListener('click', () => {{
      setView('overview');
    }});
    el('toggleSidebarButton').addEventListener('click', () => {{
      const collapsed = document.body.classList.toggle('sidebar-collapsed');
      const button = el('toggleSidebarButton');
      button.textContent = collapsed ? 'Afficher les filtres' : 'Masquer les filtres';
      button.setAttribute('aria-expanded', String(!collapsed));
    }});
    el('resetFilters').addEventListener('click', () => {{
      const currentView = state.view;
      Object.keys(state).forEach(key => state[key] = '');
      state.view = currentView;
      controls.search.value = '';
      refreshOptions();
      renderCurrentView();
    }});
    el('printButton').addEventListener('click', () => window.print());

    refreshOptions();
    renderTree();
    renderCurrentView();
  </script>
</body>
</html>
"""


def main() -> None:
    data = build_data()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render_html(data), encoding="utf-8")
    print(f"HTML généré : {OUTPUT}")
    print(f"Compétences globales : {len(data)}")
    print(f"Compétences spécifiques : {sum(len(entry['specifics']) for entry in data)}")


if __name__ == "__main__":
    main()
