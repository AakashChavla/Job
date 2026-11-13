import re

LATEX_ESCAPE_MAP = {
    '\\': r'\textbackslash{}',
    '&': r'\&',
    '%': r'\%',
    '$': r'\$',
    '#': r'\#',
    '_': r'\_',
    '{': r'\{',
    '}': r'\}',
    '~': r'\textasciitilde{}',
    '^': r'\textasciicircum{}',
}

ESCAPE_REGEX = re.compile(r'([\\&%\$#_{}~^])')

def escape_latex(text: str) -> str:
    r"""
    Escape LaTeX special characters (\ & % $ # _ { } ~ ^) in plain text.
    Preserves '--' as written so dates render as an en dash.
    """
    if text is None:
        return ""
    if not isinstance(text, str):
        text = str(text)

    # Replace special characters using map
    return ESCAPE_REGEX.sub(lambda m: LATEX_ESCAPE_MAP[m.group(1)], text)

def clean_url(url: str) -> tuple[str, str]:
    r"""
    Returns (cleaned_target_url, display_text) for \href{target}{display}.
    - Target URL: strip backslashes, braces, whitespace, and escape % and #.
    - Display text: strip https:// and trailing slash, then escape for LaTeX.
    """
    if not url:
        return "", ""
    url_str = str(url).strip()

    # For href target: strip backslashes, braces and whitespace
    target = re.sub(r'[\s\\{}]', '', url_str)
    # Ensure URL protocol if missing (default to https:// if not mailto/http/https)
    # Note: user might provide username or domain or full URL
    if not (target.startswith("http://") or target.startswith("https://") or target.startswith("mailto:")):
        target = "https://" + target

    # Escape % and # for LaTeX in target URL
    target_escaped = target.replace('%', r'\%').replace('#', r'\#')

    # For display: remove https:// and http:// and trailing slash
    display = url_str
    if display.startswith("https://"):
        display = display[len("https://"):]
    elif display.startswith("http://"):
        display = display[len("http://"):]
    if display.endswith("/"):
        display = display[:-1]

    display_escaped = escape_latex(display)

    return target_escaped, display_escaped

def clean_email(email: str) -> tuple[str, str]:
    if not email:
        return "", ""
    email_str = str(email).strip()
    target = re.sub(r'[\s\\{}]', '', email_str)
    if not target.startswith("mailto:"):
        target = "mailto:" + target
    target_escaped = target.replace('%', r'\%').replace('#', r'\#')
    display_escaped = escape_latex(email_str)
    return target_escaped, display_escaped

PREAMBLE = r"""\documentclass[letterpaper,10.5pt]{article}

\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{lmodern}
\usepackage[margin=0.7in]{geometry}
\usepackage{titlesec}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{microtype}

% Make PDF text selectable/parsable by ATS
\input{glyphtounicode}
\pdfgentounicode=1

\pagestyle{empty}
\setlength{\parindent}{0pt}
\setlength{\parskip}{0pt}
\raggedbottom
\raggedright

\titleformat{\section}{\large\bfseries\scshape}{}{0em}{}[\vspace{2pt}\titlerule]
\titlespacing{\section}{0pt}{10pt}{6pt}

\setlist[itemize]{leftmargin=1.2em, itemsep=1pt, topsep=2pt, parsep=0pt, label=\textbullet}

\newcommand{\resumeentry}[4]{%
  \textbf{#1} \hfill #2 \\
  \textit{#3} \hfill \textit{#4} \par\vspace{1pt}%
}

\begin{document}
"""

def render_header(name: str, contact: dict) -> str:
    name_escaped = escape_latex(name)
    contact_parts = []

    if not contact:
        contact = {}

    location = contact.get("location")
    if location and str(location).strip():
        contact_parts.append(escape_latex(str(location).strip()))

    phone = contact.get("phone")
    if phone and str(phone).strip():
        contact_parts.append(escape_latex(str(phone).strip()))

    email = contact.get("email")
    if email and str(email).strip():
        target, display = clean_email(email)
        contact_parts.append(rf"\href{{{target}}}{{{display}}}")

    linkedin = contact.get("linkedin")
    if linkedin and str(linkedin).strip():
        target, display = clean_url(linkedin)
        contact_parts.append(rf"\href{{{target}}}{{{display}}}")

    github = contact.get("github")
    if github and str(github).strip():
        target, display = clean_url(github)
        contact_parts.append(rf"\href{{{target}}}{{{display}}}")

    website = contact.get("website")
    if website and str(website).strip():
        target, display = clean_url(website)
        contact_parts.append(rf"\href{{{target}}}{{{display}}}")

    contact_line = r" \ $|$ \ ".join(contact_parts)
    return (
        "\\begin{center}\n"
        f"  {{\\LARGE \\textbf{{{name_escaped}}}}} \\\\[4pt]\n"
        f"  {contact_line}\n"
        "\\end{center}\n"
    )

def render_summary(summary: str) -> str:
    if not summary or not str(summary).strip():
        return ""
    text = escape_latex(str(summary).strip())
    return (
        "\\section{Professional Summary}\n"
        f"{text}\n"
    )

def render_skills(skills: list) -> str:
    if not skills:
        return ""
    lines = []
    for item in skills:
        if not isinstance(item, dict):
            continue
        category = escape_latex(item.get("category", "")).strip()
        raw_items = item.get("items", [])
        if not raw_items:
            continue
        escaped_items = [escape_latex(it) for it in raw_items if str(it).strip()]
        if not escaped_items and not category:
            continue
        items_str = ", ".join(escaped_items)
        if category:
            lines.append(f"\\textbf{{{category}:}} {items_str}")
        else:
            lines.append(items_str)

    if not lines:
        return ""

    joined = " \\\\\n".join(lines)
    return (
        "\\section{Skills}\n"
        f"{joined}\n"
    )

def render_experience(experience: list) -> str:
    if not experience:
        return ""
    entries = []
    for exp in experience:
        if not isinstance(exp, dict):
            continue
        company = escape_latex(exp.get("company", ""))
        location = escape_latex(exp.get("location", ""))
        title = escape_latex(exp.get("title", ""))
        dates = escape_latex(exp.get("dates", ""))
        bullets = exp.get("bullets", [])

        entry_latex = f"\\resumeentry{{{company}}}{{{location}}}{{{title}}}{{{dates}}}\n"
        if bullets and any(str(b).strip() for b in bullets):
            entry_latex += "\\begin{itemize}\n"
            for b in bullets:
                if str(b).strip():
                    entry_latex += f"  \\item {escape_latex(b)}\n"
            entry_latex += "\\end{itemize}\n"
        entries.append(entry_latex.strip())

    if not entries:
        return ""

    joined = "\n\n\\vspace{4pt}\n".join(entries)
    return (
        "\\section{Work Experience}\n"
        f"{joined}\n"
    )

def render_projects(projects: list) -> str:
    if not projects:
        return ""
    entries = []
    for p in projects:
        if not isinstance(p, dict):
            continue
        name = escape_latex(p.get("name", ""))
        tech = escape_latex(p.get("tech", ""))
        link = p.get("link", "")
        bullets = p.get("bullets", [])

        header_parts = []
        if name:
            header_parts.append(f"\\textbf{{{name}}}")
        if tech:
            header_parts.append(f"\\textit{{{tech}}}")
        left_side = r" \ $|$ \ ".join(header_parts) if header_parts else ""

        if link and str(link).strip():
            target, display = clean_url(link)
            link_latex = rf"\href{{{target}}}{{{display}}}"
            if left_side:
                top_line = f"{left_side} \\hfill {link_latex}"
            else:
                top_line = f"\\hfill {link_latex}"
        else:
            top_line = left_side

        entry_latex = f"{top_line}\n"
        if bullets and any(str(b).strip() for b in bullets):
            entry_latex += "\\begin{itemize}\n"
            for b in bullets:
                if str(b).strip():
                    entry_latex += f"  \\item {escape_latex(b)}\n"
            entry_latex += "\\end{itemize}\n"
        entries.append(entry_latex.strip())

    if not entries:
        return ""

    joined = "\n\n\\vspace{4pt}\n".join(entries)
    return (
        "\\section{Projects}\n"
        f"{joined}\n"
    )

def render_education(education: list) -> str:
    if not education:
        return ""
    entries = []
    for edu in education:
        if not isinstance(edu, dict):
            continue
        school = escape_latex(edu.get("school", ""))
        location = escape_latex(edu.get("location", ""))
        degree = escape_latex(edu.get("degree", ""))
        dates = escape_latex(edu.get("dates", ""))
        details = edu.get("details", "")

        entry_latex = f"\\resumeentry{{{school}}}{{{location}}}{{{degree}}}{{{dates}}}\n"
        if details and str(details).strip():
            entry_latex += f"{escape_latex(details)}\n"
        entries.append(entry_latex.strip())

    if not entries:
        return ""

    joined = "\n\n\\vspace{4pt}\n".join(entries)
    return (
        "\\section{Education}\n"
        f"{joined}\n"
    )

def render_certifications(certifications: list) -> str:
    if not certifications:
        return ""
    items = [escape_latex(c) for c in certifications if str(c).strip()]
    if not items:
        return ""
    item_lines = "\n".join(f"  \\item {c}" for c in items)
    return (
        "\\section{Certifications}\n"
        "\\begin{itemize}\n"
        f"{item_lines}\n"
        "\\end{itemize}\n"
    )

def render_achievements(achievements: list) -> str:
    if not achievements:
        return ""
    items = [escape_latex(a) for a in achievements if str(a).strip()]
    if not items:
        return ""
    item_lines = "\n".join(f"  \\item {a}" for c in items for a in [c])
    return (
        "\\section{Achievements}\n"
        "\\begin{itemize}\n"
        f"{item_lines}\n"
        "\\end{itemize}\n"
    )

SECTION_RENDERERS = {
    "summary": lambda data: render_summary(data.get("summary")),
    "skills": lambda data: render_skills(data.get("skills")),
    "experience": lambda data: render_experience(data.get("experience")),
    "projects": lambda data: render_projects(data.get("projects")),
    "education": lambda data: render_education(data.get("education")),
    "certifications": lambda data: render_certifications(data.get("certifications")),
    "achievements": lambda data: render_achievements(data.get("achievements")),
}

DEFAULT_SECTION_ORDER = [
    "summary",
    "skills",
    "experience",
    "projects",
    "education",
    "certifications",
    "achievements",
]

def build(data: dict) -> str:
    """
    Returns full LaTeX document string matching the specified template.
    """
    if not isinstance(data, dict):
        raise ValueError("Data must be a dictionary")

    output = []
    output.append(PREAMBLE)

    name = data.get("name", "")
    contact = data.get("contact", {})
    output.append(render_header(name, contact))

    section_order = data.get("section_order")
    if not isinstance(section_order, list):
        section_order = DEFAULT_SECTION_ORDER

    rendered_sections = []
    for section_key in section_order:
        renderer = SECTION_RENDERERS.get(section_key)
        if renderer:
            sec_str = renderer(data)
            if sec_str and sec_str.strip():
                rendered_sections.append(sec_str.strip())

    if rendered_sections:
        output.append("\n\n".join(rendered_sections))

    output.append("\n\\end{document}\n")
    return "\n".join(output)
