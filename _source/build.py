# -*- coding: utf-8 -*-
"""Збирає сайт AWS SAA-C03 (версія 2): курс з уроками, шпаргалку, практику, схеми,
довідник сервісів з режимом підказок, офлайн-режим (PWA) і PDF.

Джерела:
  sheet/NN_*.md   — розділи шпаргалки
  lessons/*.md    — уроки курсу (блоки === метадані === текст)
  services.md     — довідник сервісів для підказок
  questions.md    — практичний тест
Результат:
  ../docs/                 — сайт (index.html, PWA, pdf/)
  ../AWS_SAA-C03_*.html/pdf — локальні копії
Запуск:  python build.py            (усе)
         python build.py --no-pdf   (лише HTML)
"""
import hashlib
import html
import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse

sys.stdout.reconfigure(encoding="utf-8")

SRC = pathlib.Path(__file__).resolve().parent
ROOT = SRC.parent
DOCS = ROOT / "docs"
LOCAL_HTML = "AWS_SAA-C03_Курс.html"
PDFS = {  # ключ: (шлях на сайті, ім'я локальної копії)
    "lessons": ("pdf/saa-c03-kurs-uroky.pdf", "AWS_SAA-C03_Курс_уроки.pdf"),
    "full": ("pdf/saa-c03-shpargalka.pdf", "AWS_SAA-C03_Шпаргалка.pdf"),
    "quick": ("pdf/saa-c03-shvydke-povtorennia.pdf", "AWS_SAA-C03_Швидке_повторення.pdf"),
    "test": ("pdf/saa-c03-praktychnyi-test.pdf", "AWS_SAA-C03_Практичний_тест.pdf"),
}
DOMAINS = {"secure": "Безпека", "resilient": "Відмовостійкість",
           "performance": "Продуктивність", "cost": "Вартість"}
CATS = {"compute": "Обчислення", "serverless": "Serverless", "containers": "Контейнери",
        "storage": "Сховище", "database": "Бази даних", "network": "Мережа", "security": "Безпека",
        "integration": "Інтеграція", "analytics": "Аналітика", "ml": "ML / AI", "management": "Керування",
        "cost": "Вартість", "migration": "Міграція", "frontend": "Веб і мобільні", "concept": "Поняття"}
BROWSERS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
]


# ---------- Markdown → HTML (потрібна підмножина) ----------

def inline(text):
    t = html.escape(text, quote=False)
    codes = []

    def keep_code(m):
        codes.append(m.group(1))
        return f"\x00{len(codes) - 1}\x00"

    t = re.sub(r"`([^`]+)`", keep_code, t)
    t = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)",
               lambda m: f'<a href="{m.group(2)}" target="_blank" rel="noopener">{m.group(1)}</a>', t)
    t = re.sub(r"\[([^\]]+)\]\((#[\w/-]+)\)", lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>', t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![*\w])\*(?![\s*])(.+?)(?<![\s*])\*(?![*\w])", r"<em>\1</em>", t)
    t = re.sub(r"\x00(\d+)\x00", lambda m: f"<code>{codes[int(m.group(1))]}</code>", t)
    return t


def plural(n, one, few, many):
    """1 урок · 2 уроки · 5 уроків (і 11–14 — теж «уроків»)."""
    if n % 10 == 1 and n % 100 != 11:
        return f"{n} {one}"
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return f"{n} {few}"
    return f"{n} {many}"


def short_id(text):
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:8]


def split_trigger(text):
    """«питання → **відповідь**»: ділимо на першій стрілці перед жирним текстом."""
    k = text.find("→ **")
    if k < 0:
        k = text.rfind("→")
    if k < 0:
        return None
    return text[:k].strip(), text[k + 1:].strip()


def render_list(lines, mode, ordered=False):
    tree = []
    for raw in lines:
        m = re.match(r"^(\s*)(?:- |\d+\.\s)(.*)$", raw)
        text = m.group(2).strip()
        if len(m.group(1)) >= 2 and tree:
            tree[-1][1].append(text)
        else:
            tree.append([text, []])
    cls = {"trg": "trg-list", "warn": "warn-list", "rem": "rem-list"}.get(mode)
    tag = "ol" if ordered else "ul"
    out = [f'<{tag} class="{cls}">' if cls else f"<{tag}>"]
    n_trg = 0
    for text, kids in tree:
        pair = split_trigger(text) if mode == "trg" else None
        if pair:
            q, a = pair
            n_trg += 1
            body = (f'<span class="q">{inline(q)}</span> <span class="arr" aria-hidden="true">→</span> '
                    f'<span class="ans">{inline(a)}</span>')
            li = f'<li class="trg" data-id="{short_id(q)}">'
        else:
            body = inline(text)
            li = "<li>"
        if kids:
            body += "<ul>" + "".join(f"<li>{inline(k)}</li>" for k in kids) + "</ul>"
        out.append(li + body + "</li>")
    out.append(f"</{tag}>")
    return "".join(out), n_trg


def render_table(rows):
    def cells(r):
        return [c.strip() for c in r.strip().strip("|").split("|")]

    head = cells(rows[0])
    body = rows[2:] if len(rows) > 1 and re.match(r"^\|?\s*:?-{2,}", rows[1]) else rows[1:]
    cls = "tbl tbl-2" if len(head) <= 2 else "tbl"
    out = [f'<div class="{cls}"><table><thead><tr>']
    out += [f"<th>{inline(h)}</th>" for h in head]
    out.append("</tr></thead><tbody>")
    for r in body:
        out.append("<tr>")
        for i, c in enumerate(cells(r)):
            label = html.escape(re.sub(r"\*\*|`", "", head[i] if i < len(head) else ""), quote=True)
            out.append(f'<td data-label="{label}">{inline(c)}</td>')
        out.append("</tr>")
    out.append("</tbody></table></div>")
    return "".join(out)


def render(md, split_h2=True):
    """split_h2=True: повертає (title, sections) для шпаргалки; False: (html, stats) для уроку."""
    lines = md.replace("\r\n", "\n").split("\n")
    title, sections, mode = "", [], None
    cur = None if split_h2 else {"content": [], "trg": 0, "warn": False, "figs": 0}
    i, n = 0, len(lines)
    heading_re = re.compile(r"^(#{1,4})\s+(.*)$")
    block_start = re.compile(r"^(#{1,4}\s|\s*\||\s*>|\s*- |\d+\.\s|```|<)")

    def add(fragment):
        if cur is not None:
            cur["content"].append(fragment)

    while i < n:
        line = lines[i]
        s = line.strip()
        if not s:
            i += 1
            continue
        if s.startswith("```"):
            lang = s[3:].strip()
            i += 1
            buf = []
            while i < n and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            add(f'<pre class="code"><code class="lang-{html.escape(lang)}">{html.escape(chr(10).join(buf))}</code></pre>')
            continue
        if s.startswith("<"):
            buf = []
            while i < n and lines[i].strip():
                buf.append(lines[i])
                i += 1
            add("\n".join(buf))
            if cur is not None:
                cur["figs"] += "\n".join(buf).count('class="diagram"')
            continue
        m = heading_re.match(line)
        if m:
            level, text = len(m.group(1)), m.group(2).strip()
            if level == 1:
                title = text
            elif level == 2 and split_h2:
                quick = bool(re.search(r"\{quick\}\s*$", text))
                text = re.sub(r"\s*\{quick\}\s*$", "", text)
                mnum = re.match(r"^(\d+)\.\s*(.*)$", text)
                num, name = (mnum.group(1), mnum.group(2)) if mnum else ("", text)
                cur = {"id": f"s{len(sections) + 1}", "num": num, "title": name, "quick": quick,
                       "content": [], "trg": 0, "warn": False, "figs": 0}
                sections.append(cur)
                mode = None
            elif level <= 3:
                add(f"<h{max(level, 3)}>{inline(text)}</h{max(level, 3)}>")
                mode = None
            else:
                if "🎯" in text:
                    mode, cls = "trg", "trg-h"
                elif "⚠" in text:
                    mode, cls = "warn", "warn-h"
                elif "💡" in text:
                    mode, cls = "rem", "rem-h"
                else:
                    mode, cls = None, ""
                add(f'<h4 class="{cls}">{inline(text)}</h4>' if cls else f"<h4>{inline(text)}</h4>")
            i += 1
            continue
        if s.startswith("|"):
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                rows.append(lines[i].strip())
                i += 1
            add(render_table(rows))
            continue
        if s.startswith(">"):
            buf = []
            while i < n and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip()[1:].strip())
                i += 1
            txt = " ".join(buf)
            kind = ("img" if txt.startswith("🖼") else "warn" if txt.startswith("⚠")
                    else "new" if txt.startswith("🆕") else "tip")
            add(f'<div class="callout {kind}">{inline(txt)}</div>')
            continue
        if re.match(r"^\s*- ", line) or re.match(r"^\d+\.\s", s):
            ordered = bool(re.match(r"^\d+\.\s", s))
            pat = r"^\s*(\d+\.\s|- )" if ordered else r"^\s*- "
            items = []
            while i < n and re.match(pat, lines[i]):
                items.append(lines[i])
                i += 1
            frag, n_trg = render_list(items, mode, ordered)
            if cur is not None:
                cur["trg"] += n_trg
                cur["warn"] = cur["warn"] or mode == "warn"
            add(frag)
            continue
        buf = [s]
        i += 1
        while i < n and lines[i].strip() and not block_start.match(lines[i].strip()):
            buf.append(lines[i].strip())
            i += 1
        add(f"<p>{inline(' '.join(buf))}</p>")
    if split_h2:
        return title, sections
    return "".join(cur["content"]), cur


# ---------- Джерела даних ----------

def parse_lessons(sheet_nums):
    lessons = []
    for f in sorted((SRC / "lessons").glob("*.md")):
        parts = re.split(r"^===\s*$", f.read_text(encoding="utf-8"), flags=re.M)
        for k in range(1, len(parts) - 1, 2):
            meta = {}
            for line in parts[k].strip().splitlines():
                if ":" in line:
                    key, val = line.split(":", 1)
                    meta[key.strip()] = val.strip()
            body_html, stats = render(parts[k + 1], split_h2=False)
            sheets = [int(x) for x in re.findall(r"\d+", meta.get("sheet", ""))]
            for sn in sheets:
                if sn not in sheet_nums:
                    raise ValueError(f"Урок {meta.get('id')}: немає розділу шпаргалки {sn}")
            lessons.append({"id": meta["id"], "module": meta["module"], "title": meta["title"],
                            "emoji": meta.get("emoji", "📘"), "minutes": meta.get("minutes", "5"),
                            "sheet": sheets, "html": body_html, "trg": stats["trg"], "figs": stats["figs"]})
    ids = [l["id"] for l in lessons]
    if len(set(ids)) != len(ids):
        raise ValueError("Повторюються id уроків")
    return lessons


def parse_services(lesson_ids):
    text = (SRC / "services.md").read_text(encoding="utf-8")
    services, seen_alias = [], {}
    for block in re.split(r"^## ", text, flags=re.M)[1:]:
        lines = [l.strip() for l in block.strip().splitlines() if l.strip()]
        head = [x.strip() for x in lines[0].split("|")]
        if len(head) != 5:
            raise ValueError(f"Поганий заголовок сервісу: {lines[0][:60]}")
        sid, name, aliases, cat, emoji = head
        f = {}
        for line in lines[1:]:
            key, val = line.split(":", 1)
            f[key.strip()] = val.strip()
        if cat not in CATS:
            raise ValueError(f"{sid}: невідома категорія {cat}")
        al = [a.strip() for a in aliases.split(",") if a.strip()]
        for a in al:
            if a in seen_alias:
                raise ValueError(f"Аліас «{a}» є і в {seen_alias[a]}, і в {sid}")
            seen_alias[a] = sid

        def exam_item(x):
            if "→" in x:
                q, a = x.split("→", 1)
                return (f'<span class="q">{inline(q.strip())}</span> <span class="arr">→</span> '
                        f'<span class="a">{inline(a.strip())}</span>')
            return inline(x)

        lesson = f.get("LESSON", "")
        if lesson and lesson not in lesson_ids:
            raise ValueError(f"{sid}: немає уроку {lesson}")
        services.append({
            "id": sid, "name": name, "aliases": al, "cat": cat, "emoji": emoji,
            "what": inline(f["WHAT"]), "image": inline(f["IMAGE"]),
            "when": [inline(x.strip()) for x in f.get("WHEN", "").split(";") if x.strip()],
            "exam": [exam_item(x.strip()) for x in f.get("EXAM", "").split(";") if x.strip()],
            "confuse": [c.strip() for c in f.get("CONFUSE", "").split(",") if c.strip()],
            "lesson": lesson,
        })
    ids = {s["id"] for s in services}
    if len(ids) != len(services):
        raise ValueError("Повторюються id сервісів")
    for s in services:
        for c in s["confuse"]:
            if c not in ids:
                raise ValueError(f"{s['id']}: CONFUSE посилається на невідомий {c}")
    return services


def parse_questions(path):
    text = path.read_text(encoding="utf-8")
    qs = []
    for block in re.split(r"^## Q", text, flags=re.M)[1:]:
        lines = [l.strip() for l in block.strip().splitlines() if l.strip()]
        m = re.match(r"(\d+)\s*\|\s*(\w+)", lines[0])
        num, dom = int(m.group(1)), m.group(2)
        if dom not in DOMAINS:
            raise ValueError(f"Q{num}: невідомий домен {dom}")
        q = {"id": f"q{num}", "n": num, "domain": dom, "en": "", "ua": "", "options": [], "correct": [], "why": ""}
        for line in lines[1:]:
            if line.startswith("EN:"):
                q["en"] = inline(line[3:].strip())
            elif line.startswith("UA:"):
                q["ua"] = inline(line[3:].strip())
            elif line.startswith("WHY:"):
                q["why"] = inline(line[4:].strip())
            else:
                mo = re.match(r"^([A-F])(\*?):\s*(.*)$", line)
                if not mo:
                    raise ValueError(f"Q{num}: незрозумілий рядок: {line[:60]}")
                if mo.group(2):
                    q["correct"].append(len(q["options"]))
                q["options"].append(inline(mo.group(3)))
        if not (q["en"] and q["ua"] and q["why"] and len(q["options"]) >= 4 and q["correct"]):
            raise ValueError(f"Q{num}: неповне питання")
        q["multi"] = len(q["correct"]) > 1
        qs.append(q)
    return qs


# ---------- Стилі ----------

CSS = r"""
:root{
  --bg:#f5f6f8;--surface:#ffffff;--surface-2:#eef1f5;--zebra:#f8f9fb;--text:#1a1f26;--muted:#5d6673;--border:#dde2e8;--border-strong:#c3cad3;
  --accent:#1f6feb;--accent-ink:#ffffff;--accent-soft:#e8f0fe;
  --trg:#0b57c9;--trg-bg:#f3f8ff;--trg-line:#c5dafc;
  --warn:#8a5300;--warn-bg:#fff8eb;--warn-line:#f1cf8f;
  --ok:#1f7a45;--ok-bg:#eaf7ef;--bad:#b42318;--bad-bg:#fdecea;
  --code-bg:#edf0f4;--shadow:0 1px 2px rgba(16,24,40,.05),0 2px 6px rgba(16,24,40,.06);
  --c-net:#7c3aed;--c-cmp:#c2410c;--c-db:#1d4ed8;--c-sto:#15803d;--c-sec:#b91c1c;--c-int:#be185d;--c-ana:#0f766e;
  color-scheme:light;
}
@media (prefers-color-scheme:dark){
  :root:not([data-theme="light"]){
    --bg:#0f1115;--surface:#171a20;--surface-2:#1f232b;--zebra:#1b1f26;--text:#e6e8eb;--muted:#9aa3ae;--border:#2b3038;--border-strong:#3b424d;
    --accent:#5b9dff;--accent-ink:#0b0d10;--accent-soft:#182439;
    --trg:#8dbaff;--trg-bg:#141c29;--trg-line:#2a4270;
    --warn:#f2b865;--warn-bg:#231b10;--warn-line:#5c4418;
    --ok:#6fd49a;--ok-bg:#11241a;--bad:#ff8a80;--bad-bg:#2c1413;
    --code-bg:#252a33;--shadow:none;
    --c-net:#a78bfa;--c-cmp:#fb923c;--c-db:#60a5fa;--c-sto:#4ade80;--c-sec:#f87171;--c-int:#f472b6;--c-ana:#2dd4bf;
    color-scheme:dark;
  }
}
:root[data-theme="dark"]{
  --bg:#0f1115;--surface:#171a20;--surface-2:#1f232b;--zebra:#1b1f26;--text:#e6e8eb;--muted:#9aa3ae;--border:#2b3038;--border-strong:#3b424d;
  --accent:#5b9dff;--accent-ink:#0b0d10;--accent-soft:#182439;
  --trg:#8dbaff;--trg-bg:#141c29;--trg-line:#2a4270;
  --warn:#f2b865;--warn-bg:#231b10;--warn-line:#5c4418;
  --ok:#6fd49a;--ok-bg:#11241a;--bad:#ff8a80;--bad-bg:#2c1413;
  --code-bg:#252a33;--shadow:none;
  --c-net:#a78bfa;--c-cmp:#fb923c;--c-db:#60a5fa;--c-sto:#4ade80;--c-sec:#f87171;--c-int:#f472b6;--c-ana:#2dd4bf;
  color-scheme:dark;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%;font-size:16px}
body{margin:0;background:var(--bg);color:var(--text);font:1rem/1.55 "Segoe UI",Roboto,"Helvetica Neue",Arial,"Noto Sans",sans-serif}
a{color:var(--accent)}
[hidden]{display:none!important}
.skip{position:absolute;left:-999px}
.skip:focus{left:16px;top:8px;z-index:99;background:var(--surface);padding:6px 10px;border-radius:8px}
.muted{color:var(--muted)}
kbd{font:inherit}
.topbar{position:sticky;top:0;z-index:30;background:var(--surface);border-bottom:1px solid var(--border)}
.topbar-inner{max-width:1320px;margin:0 auto;padding:8px 16px;display:flex;flex-wrap:wrap;align-items:center;gap:8px}
.brand{font-weight:700;font-size:1.05rem;white-space:nowrap;color:var(--text);text-decoration:none}
.brand-sub{font-weight:400;color:var(--muted)}
.search{flex:1 1 220px;display:flex;align-items:center;gap:6px;background:var(--surface-2);border:1px solid var(--border);border-radius:10px;padding:0 10px}
.search input{flex:1;min-width:0;border:0;background:transparent;color:var(--text);font:inherit;padding:8px 0;outline:none}
.search:focus-within{border-color:var(--accent)}
.actions{display:flex;flex-wrap:wrap;gap:6px;margin-left:auto;align-items:center}
.tb-btn{border:1px solid var(--border);background:var(--surface);color:var(--text);border-radius:10px;padding:7px 11px;font:inherit;font-size:.9rem;line-height:1.2;cursor:pointer;white-space:nowrap;text-decoration:none;display:inline-flex;align-items:center;gap:4px}
.tb-btn:hover{border-color:var(--accent)}
.tb-btn:disabled{opacity:.5;cursor:not-allowed}
.tb-btn[aria-pressed="true"]{background:var(--accent);border-color:var(--accent);color:var(--accent-ink)}
.tb-btn.icon{padding:7px 10px}
.tb-btn.primary{background:var(--accent);border-color:var(--accent);color:var(--accent-ink)}
.tb-btn.ok{background:var(--ok-bg);border-color:var(--ok);color:var(--ok)}
.tb-btn.bad{background:var(--bad-bg);border-color:var(--bad);color:var(--bad)}
.linkbtn{border:0;background:none;color:var(--accent);font:inherit;cursor:pointer;padding:0;text-decoration:underline}
.dl{position:relative}
.dl summary{list-style:none}
.dl summary::-webkit-details-marker{display:none}
.dl-menu{position:absolute;right:0;top:calc(100% + 6px);z-index:60;background:var(--surface);border:1px solid var(--border);border-radius:12px;box-shadow:0 10px 30px rgba(0,0,0,.18);padding:6px;min-width:240px;display:grid}
.dl-menu a{padding:9px 10px;border-radius:8px;color:var(--text);text-decoration:none}
.dl-menu a:hover{background:var(--surface-2)}
.tabs{max-width:1320px;margin:0 auto;padding:0 16px 8px;display:flex;gap:6px;flex-wrap:wrap}
.tab{border:1px solid var(--border);background:var(--surface);color:var(--text);border-radius:99px;padding:6px 14px;font-size:.92rem;text-decoration:none;display:inline-flex;gap:6px;align-items:center}
.tab:hover{border-color:var(--accent)}
.tab[aria-current="page"]{background:var(--accent);border-color:var(--accent);color:var(--accent-ink)}
.search-info{max-width:1320px;margin:0 auto;padding:0 16px 6px;font-size:.85rem;color:var(--muted)}
.search-info:empty{display:none}
body:not([data-view="sheet"]):not([data-view="quick"]) .sheet-only{display:none!important}
body:not([data-view="sheet"]):not([data-view="quick"]):not([data-view="learn"]) .hide-only{display:none!important}
.seg{display:inline-flex;border:1px solid var(--border);border-radius:12px;overflow:hidden;background:var(--surface);margin:0 0 14px}
.seg a{padding:8px 14px;font-size:.92rem;color:var(--text);text-decoration:none}
.seg a+a{border-left:1px solid var(--border)}
.seg a[aria-current="page"]{background:var(--accent);color:var(--accent-ink)}
.layout{max-width:1320px;margin:0 auto;padding:0 16px;display:grid;grid-template-columns:270px minmax(0,1fr);gap:28px}
.toc{position:sticky;top:112px;align-self:start;max-height:calc(100vh - 124px);overflow:auto;padding:18px 4px 24px 0}
.toc-head{display:flex;justify-content:space-between;align-items:baseline;gap:8px;margin-bottom:6px}
.toc-head span{font-size:.82rem;color:var(--muted)}
.bar{height:6px;background:var(--surface-2);border-radius:99px;overflow:hidden;margin-bottom:10px}
.bar span{display:block;height:100%;width:0;background:var(--ok);transition:width .3s}
.toc ol,.print-toc ol{list-style:none;margin:0;padding:0}
.toc a{display:flex;gap:8px;padding:6px 8px;border-radius:8px;color:var(--text);text-decoration:none;font-size:.9rem;line-height:1.3}
.toc a:hover{background:var(--surface-2)}
.toc a.current{background:var(--accent-soft);color:var(--accent)}
.toc a .n{min-width:1.6em;color:var(--muted);font-variant-numeric:tabular-nums}
.toc a.done::after{content:"✓";margin-left:auto;color:var(--ok);font-weight:700}
.scrim{display:none;position:fixed;inset:0;background:rgba(0,0,0,.4);z-index:45}
main{min-width:0;padding:20px 0 96px}
.page{max-width:900px;margin:0 auto;padding:20px 16px 96px}
.page h1{font-size:clamp(1.4rem,3vw,1.9rem);margin:.2em 0 .3em}
.hero{padding:6px 0 18px}
.hero h1{font-size:clamp(1.45rem,3.2vw,2.05rem);line-height:1.2;margin:.15em 0 .45em}
.sub{color:var(--muted);margin:0 0 12px}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 12px}
.chips span{background:var(--surface);border:1px solid var(--border);border-radius:99px;padding:4px 12px;font-size:.86rem}
.how{background:var(--accent-soft);border:1px solid var(--trg-line);border-radius:12px;padding:10px 14px;margin:0 0 8px}
.progress-line{font-size:.9rem;color:var(--muted);margin:6px 0 0}
section{background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:18px 22px 10px;margin:0 0 18px;box-shadow:var(--shadow);scroll-margin-top:120px}
figure.diagram,article.lesson{scroll-margin-top:120px}
.card{background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:18px 20px;margin:0 0 16px;box-shadow:var(--shadow)}
.sec-head{display:flex;justify-content:space-between;align-items:flex-start;gap:12px;border-bottom:1px solid var(--border);padding-bottom:10px;margin-bottom:10px}
h2{margin:0;font-size:1.28rem;line-height:1.3;display:flex;gap:10px;align-items:flex-start}
h2 .num{flex:none;display:inline-grid;place-items:center;min-width:2.1rem;height:2.1rem;padding:0 .3rem;border-radius:9px;background:var(--accent-soft);color:var(--accent);font-size:1rem}
h2 .t{padding-top:.2rem}
.learn-btn{flex:none;border:1px solid var(--border);background:var(--surface-2);color:var(--muted);border-radius:99px;padding:4px 10px;font:inherit;font-size:.8rem;cursor:pointer;white-space:nowrap}
.learn-btn[aria-pressed="true"]{background:var(--ok-bg);color:var(--ok);border-color:var(--ok)}
h3{font-size:1.12rem;margin:18px 0 6px}
h4{font-size:1rem;margin:16px 0 8px}
h4.trg-h{color:var(--trg)}
h4.warn-h{color:var(--warn)}
h4.rem-h{color:var(--ok)}
p{margin:8px 0}
ul,ol{margin:6px 0 12px;padding-left:1.25rem}
ol{padding-left:1.5rem}
li{margin:5px 0}
li::marker{color:var(--muted)}
strong{font-weight:650}
code{background:var(--code-bg);padding:.08em .35em;border-radius:5px;font-family:Consolas,"Cascadia Mono","Roboto Mono",monospace;font-size:.88em}
pre.code{background:var(--code-bg);border:1px solid var(--border);border-radius:10px;padding:10px 12px;overflow-x:auto;font-size:.8rem;line-height:1.45;margin:8px 0 14px}
pre.code code{background:none;padding:0;font-size:inherit}
.trg-list,.warn-list,.rem-list{list-style:none;padding:0;display:grid;gap:6px}
.trg-list>li{background:var(--trg-bg);border:1px solid var(--trg-line);border-radius:10px;padding:8px 12px;margin:0}
.warn-list>li{background:var(--warn-bg);border:1px solid var(--warn-line);border-radius:10px;padding:8px 12px;margin:0}
.rem-list>li{background:var(--ok-bg);border:1px solid var(--ok);border-radius:10px;padding:8px 12px;margin:0}
.trg .arr{color:var(--muted)}
.trg .ans{color:var(--trg);font-weight:600;border-radius:6px;transition:filter .15s}
body.hide-ans .trg .ans{filter:blur(6px);cursor:pointer;user-select:none;-webkit-user-select:none}
body.hide-ans .trg .ans.revealed{filter:none}
.callout{border-radius:10px;padding:10px 12px;margin:10px 0;border:1px solid var(--trg-line);background:var(--trg-bg)}
.callout.warn{border-color:var(--warn-line);background:var(--warn-bg)}
.callout.img{font-size:1.03rem;line-height:1.6;background:linear-gradient(135deg,var(--accent-soft),var(--trg-bg));border-color:var(--trg-line);padding:14px 16px;border-radius:14px;margin:4px 0 16px}
.tbl{overflow-x:auto;margin:10px 0 14px;border:1px solid var(--border);border-radius:10px}
table{border-collapse:collapse;width:100%;font-size:.92rem}
th,td{text-align:left;vertical-align:top;padding:8px 10px;border-bottom:1px solid var(--border)}
tbody tr:last-child td{border-bottom:0}
th{background:var(--surface-2);font-weight:650}
tbody tr:nth-child(even) td{background:var(--zebra)}
.hit-hidden{display:none!important}
body.only-trg section.no-quick{display:none}
body.only-trg section:not(.quick-keep)>:not(.sec-head):not(.trg-h):not(.trg-list):not(.warn-h):not(.warn-list){display:none}
body.only-trg .toc li.no-quick,body.only-trg .print-toc li.no-quick{display:none}
body.only-trg #view-sheet .hero .how{display:none}
/* курс */
.progress-card{display:flex;flex-wrap:wrap;gap:10px 16px;align-items:center;background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:12px 14px;margin:0 0 12px;box-shadow:var(--shadow)}
.progress-card .bar{flex:1 1 200px;margin:0}
.progress-card p{margin:0;font-size:.9rem;color:var(--muted)}
#learn-continue,.svc-links .tb-btn,.lesson-nav .tb-btn{white-space:normal;text-align:left}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:8px;margin:0 0 12px}
.stat{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:10px 12px}
.stat b{display:block;font-size:1.25rem}
.stat span{font-size:.8rem;color:var(--muted)}
section.module{background:none;border:0;box-shadow:none;padding:0;margin:22px 0 0}
section.module h2{display:block;font-size:.9rem;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);margin:0 0 10px}
.lesson-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:10px}
.lesson-card{display:flex;gap:12px;align-items:flex-start;border:1px solid var(--border);background:var(--surface);border-radius:12px;padding:12px;text-decoration:none;color:var(--text);box-shadow:var(--shadow)}
.lesson-card:hover{border-color:var(--accent)}
.lesson-card .le{font-size:1.7rem;line-height:1}
.lesson-card .ln{display:block;font-size:.78rem;color:var(--muted)}
.lesson-card .lt{display:block;font-weight:650;line-height:1.3}
.lesson-card.done{border-color:var(--ok)}
.lesson-card.done .ln::after{content:" · ✓ пройдено";color:var(--ok);font-weight:600}
.disclaimer{font-size:.8rem;color:var(--muted);margin:26px 0 0}
.install-card{display:flex;flex-wrap:wrap;gap:8px 12px;align-items:center;justify-content:space-between;background:var(--surface);border:1px dashed var(--accent);border-radius:14px;padding:10px 14px;margin:0 0 12px}
.install-card .muted{font-size:.88rem}
.offline-ok{font-size:.85rem;color:var(--ok);margin:0 0 10px}
article.lesson{max-width:800px;margin:0 auto 18px;padding:20px 24px}
.lesson-top{display:flex;flex-wrap:wrap;gap:6px 14px;justify-content:space-between;font-size:.88rem}
.lesson-top .meta{color:var(--muted)}
article.lesson h1{font-size:clamp(1.35rem,3vw,1.8rem);line-height:1.25;margin:.35em 0 .6em;display:flex;gap:10px;align-items:flex-start}
article.lesson p,article.lesson li{line-height:1.6}
.lesson-links{margin:18px 0 6px;padding:10px 12px;border-radius:10px;background:var(--surface-2);font-size:.92rem}
.lesson-nav{display:flex;flex-wrap:wrap;gap:8px;justify-content:space-between;align-items:center;margin:14px 0 4px}
.print-lessons-only{display:none}
/* схеми */
.diagram{margin:14px 0 16px;border:1px solid var(--border);border-radius:12px;padding:12px;background:var(--surface-2);font-size:.86rem;line-height:1.4}
.diagram figcaption{font-size:.84rem;color:var(--muted);margin-top:10px}
.dg-box{border:1.5px dashed var(--border-strong);border-radius:10px;padding:8px;background:var(--surface)}
.dg-label{font-size:.74rem;font-weight:700;letter-spacing:.03em;text-transform:uppercase;color:var(--muted);margin:0 0 6px;display:flex;flex-wrap:wrap;gap:6px;align-items:center}
.dg-azs{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.dg-az{background:var(--surface-2)}
.dg-sub{--c:var(--c-sto);border-radius:8px;padding:6px 8px;margin-top:6px;border:1px solid var(--border);border-left:4px solid var(--c);background:var(--surface)}
.dg-sub.pub{--c:var(--c-sto)}.dg-sub.app{--c:var(--c-cmp)}.dg-sub.db{--c:var(--c-db)}
.dg-sub small{display:block;color:var(--muted);margin-top:3px}
.dg-nodes{display:flex;flex-wrap:wrap;gap:4px;margin-top:4px}
.dg-node{--c:var(--muted);display:inline-flex;align-items:center;gap:4px;padding:2px 8px;border-radius:7px;border:1px solid var(--c);background:var(--surface);color:var(--text);font-size:.8rem;font-weight:600;line-height:1.35;text-transform:none;letter-spacing:0}
.dg-node.net{--c:var(--c-net)}.dg-node.cmp{--c:var(--c-cmp)}.dg-node.db{--c:var(--c-db)}.dg-node.sto{--c:var(--c-sto)}.dg-node.sec{--c:var(--c-sec)}.dg-node.int{--c:var(--c-int)}.dg-node.ana{--c:var(--c-ana)}
.flow{display:flex;align-items:stretch;gap:6px}
.flow>.st{flex:1 1 0;min-width:0;border:1px solid var(--border);border-radius:10px;padding:8px;background:var(--surface);font-size:.8rem}
.flow>.st b{display:block;font-size:.85rem;margin-bottom:3px}
.flow>.st .dg-node{margin:2px 0}
.flow>.st.lanes .dg-node{display:flex;margin:4px 0}
.flow>.st small{display:block;color:var(--muted);margin-top:4px}
.flow>.ar{align-self:center;color:var(--muted);font-weight:700;flex:none;font-size:1.1rem}
.dg-govern{margin-top:8px;border:1px solid var(--c-sec);border-radius:10px;padding:6px 10px;background:var(--surface);font-size:.82rem}
.tiers{display:grid;gap:2px}
.tier{display:flex;flex-wrap:wrap;gap:6px;align-items:center;border:1px solid var(--border);border-radius:10px;padding:8px;background:var(--surface)}
.tier .tl{min-width:104px;font-size:.72rem;font-weight:700;text-transform:uppercase;color:var(--muted)}
.tier small{color:var(--muted)}
.down{text-align:center;color:var(--muted);line-height:1.1;font-weight:700}
.dec{display:grid;gap:2px}
.dec-step{display:grid;grid-template-columns:auto 1fr auto;gap:10px;align-items:center;border:1px solid var(--border);border-radius:10px;padding:8px 10px;background:var(--surface)}
.dec-n{display:inline-grid;place-items:center;width:1.7rem;height:1.7rem;border-radius:50%;background:var(--accent-soft);color:var(--accent);font-weight:700}
.dec-out{font-weight:700;white-space:nowrap;font-size:.82rem}
.dec-out.no{color:var(--bad)}.dec-out.yes{color:var(--ok)}
.dr{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}
.dr .card{margin:0;padding:10px;font-size:.82rem;box-shadow:none;display:flex;flex-direction:column;gap:4px}
.dr .card b{font-size:.88rem}
.dr .price{margin-top:auto}
.dr-bar{height:8px;border-radius:99px;background:linear-gradient(90deg,var(--c-sto),var(--c-cmp),var(--c-sec));margin:10px 0 4px}
.dr-legend{display:flex;justify-content:space-between;gap:8px;font-size:.75rem;color:var(--muted)}
#dg-gallery .dg-item{margin:0 0 26px}
#dg-gallery h2{display:block;font-size:1.1rem;margin:0 0 4px}
.dg-link{font-size:.9rem}
/* практика */
.qz-row{display:flex;flex-wrap:wrap;gap:10px;align-items:center;justify-content:space-between}
select{font:inherit;font-size:.9rem;padding:7px 9px;border-radius:9px;border:1px solid var(--border);background:var(--surface-2);color:var(--text);max-width:100%}
.chk{display:inline-flex;gap:6px;align-items:center;font-size:.92rem;cursor:pointer}
.qz-sec{margin-top:16px;font-size:.82rem;color:var(--muted)}
.qz-q{font-size:1.18rem;font-weight:600;line-height:1.45;margin:6px 0 14px;min-height:3.2em}
.qz-a{background:var(--trg-bg);border:1px solid var(--trg-line);color:var(--trg);border-radius:10px;padding:10px 12px;font-weight:600;margin-bottom:14px}
.qz-actions{display:flex;flex-wrap:wrap;gap:8px}
.qz-stats{margin-top:14px;font-size:.86rem;color:var(--muted)}
.qz-hint{font-size:.82rem;color:var(--muted)}
.opt-group{display:grid;gap:8px;margin:10px 0}
.radio{display:flex;gap:10px;align-items:flex-start;border:1px solid var(--border);border-radius:10px;padding:10px 12px;cursor:pointer;background:var(--surface)}
.radio:has(input:checked){border-color:var(--accent);background:var(--accent-soft)}
.row{display:flex;flex-wrap:wrap;gap:10px 18px;align-items:center;margin:10px 0}
.row label{display:inline-flex;gap:6px;align-items:center}
.t-head{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-bottom:10px}
.t-pos{font-weight:700}
.chip{display:inline-block;border-radius:99px;padding:2px 10px;font-size:.8rem;background:var(--accent-soft);color:var(--accent)}
.t-timer{margin-left:auto;font-variant-numeric:tabular-nums;font-weight:700}
.t-timer.low{color:var(--bad)}
.t-stem{font-size:1.04rem;line-height:1.55;margin:4px 0 6px}
.t-alt{font-size:.95rem;color:var(--muted);border-left:3px solid var(--accent);padding:4px 10px;margin:6px 0}
.t-note{font-weight:700;color:var(--warn);margin:6px 0}
.t-note:empty{display:none}
.t-opts{display:grid;gap:8px;margin:10px 0 14px}
.t-opt{display:flex;gap:10px;align-items:flex-start;text-align:left;width:100%;border:1.5px solid var(--border);background:var(--surface);color:var(--text);border-radius:12px;padding:10px 12px;font:inherit;line-height:1.45;cursor:pointer}
.t-opt:hover{border-color:var(--accent)}
.t-opt[aria-pressed="true"]{border-color:var(--accent);background:var(--accent-soft)}
.t-opt.right{border-color:var(--ok);background:var(--ok-bg)}
.t-opt.wrong{border-color:var(--bad);background:var(--bad-bg)}
.t-opt:disabled{cursor:default;opacity:1}
.t-letter{flex:none;display:inline-grid;place-items:center;width:1.6rem;height:1.6rem;border-radius:7px;background:var(--surface-2);font-weight:700;font-size:.85rem}
.t-why{border-radius:10px;padding:10px 12px;margin:0 0 12px;background:var(--surface-2);border:1px solid var(--border)}
.t-why.ok{background:var(--ok-bg);border-color:var(--ok)}
.t-why.bad{background:var(--bad-bg);border-color:var(--bad)}
.t-actions{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.t-actions .spacer{flex:1}
.t-nav{display:grid;grid-template-columns:repeat(auto-fill,minmax(38px,1fr));gap:5px;margin-top:16px}
.t-nav button{border:1px solid var(--border);background:var(--surface);color:var(--text);border-radius:8px;padding:6px 0;font:inherit;font-size:.82rem;cursor:pointer}
.t-nav button.ans{background:var(--accent-soft);border-color:var(--accent)}
.t-nav button.flag{box-shadow:inset 0 -3px 0 var(--warn)}
.t-nav button.cur{outline:2px solid var(--accent);outline-offset:1px}
.t-score{font-size:2rem;font-weight:800;margin:4px 0}
.t-bar{height:12px;background:var(--surface-2);border-radius:99px;overflow:hidden;margin:6px 0 10px}
.t-bar span{display:block;height:100%;width:0;background:var(--accent);transition:width .4s}
.t-bar span.ok{background:var(--ok)}.t-bar span.mid{background:var(--warn)}.t-bar span.bad{background:var(--bad)}
.t-hist{padding-left:1.1rem;font-size:.9rem}
.t-rev{border:1px solid var(--border);border-left:4px solid var(--ok);border-radius:10px;padding:10px 12px;margin:10px 0;background:var(--surface)}
.t-rev.bad{border-left-color:var(--bad)}
.t-rev-h{font-weight:700;font-size:.88rem;color:var(--muted);margin-bottom:4px}
.t-rev-opts{list-style:none;padding:0;margin:8px 0}
.t-rev-opts li{display:flex;gap:8px;align-items:flex-start;padding:4px 6px;border-radius:8px}
.t-rev-opts li.right{background:var(--ok-bg)}
.t-rev-opts li.wrong{background:var(--bad-bg)}
/* довідник і підказки */
.search.wide{max-width:none;margin:6px 0}
.cat-chips{display:flex;flex-wrap:wrap;gap:6px;margin:10px 0}
.cat-chip{border:1px solid var(--border);background:var(--surface);color:var(--text);border-radius:99px;padding:5px 11px;font:inherit;font-size:.85rem;cursor:pointer}
.cat-chip[aria-pressed="true"]{background:var(--accent);border-color:var(--accent);color:var(--accent-ink)}
.svc-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:8px}
.svc-item{display:flex;gap:10px;align-items:flex-start;text-align:left;border:1px solid var(--border);background:var(--surface);color:var(--text);border-radius:12px;padding:10px 12px;font:inherit;cursor:pointer;box-shadow:var(--shadow)}
.svc-item:hover{border-color:var(--accent)}
.svc-item .svc-e{font-size:1.5rem;line-height:1}
.svc-item b{display:block;font-size:.95rem}
.svc-item small{display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;color:var(--muted);font-size:.8rem;line-height:1.35;margin-top:2px}
body.hints-on .svc{text-decoration:underline dotted var(--accent);text-decoration-color:color-mix(in srgb,var(--accent) 65%,transparent);text-decoration-thickness:1.5px;text-underline-offset:3px;cursor:pointer;border-radius:3px}
body.hints-on .svc:hover{background:var(--accent-soft)}
.svc-overlay{position:fixed;inset:0;z-index:70;background:rgba(10,12,16,.45);display:flex;align-items:flex-end;justify-content:center}
.svc-card{width:min(620px,100%);max-height:84vh;overflow:auto;background:var(--surface);color:var(--text);border:1px solid var(--border);border-radius:18px 18px 0 0;padding:16px 18px calc(18px + env(safe-area-inset-bottom));box-shadow:0 -10px 40px rgba(0,0,0,.25)}
.svc-head{display:flex;gap:12px;align-items:flex-start;margin-bottom:6px}
.svc-emoji{font-size:2.1rem;line-height:1}
.svc-head h2{font-size:1.2rem;margin:0 0 4px;display:block}
.svc-head .x{margin-left:auto}
.svc-what{font-size:1.02rem;margin:6px 0 10px}
.svc-image{background:linear-gradient(135deg,var(--accent-soft),var(--trg-bg));border:1px solid var(--trg-line);border-radius:12px;padding:10px 12px;margin:0 0 10px}
.svc-card h4{margin:12px 0 6px}
.svc-when{margin:0 0 6px}
.svc-exam{list-style:none;padding:0;display:grid;gap:5px;margin:0}
.svc-exam li{background:var(--trg-bg);border:1px solid var(--trg-line);border-radius:10px;padding:6px 10px;margin:0}
.svc-exam .a{color:var(--trg);font-weight:650}
.svc-exam .arr{color:var(--muted)}
.svc-confuse{margin:12px 0 4px;display:flex;flex-wrap:wrap;gap:6px;align-items:center;font-size:.9rem}
.svc-confuse:empty{display:none}
.chip-btn{border:1px solid var(--border);background:var(--surface-2);color:var(--text);border-radius:99px;padding:4px 10px;font:inherit;font-size:.85rem;cursor:pointer}
.chip-btn:hover{border-color:var(--accent)}
.svc-links{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}
.ask-overlay{position:fixed;inset:0;z-index:80;background:rgba(10,12,16,.45);display:flex;align-items:center;justify-content:center;padding:16px}
.ask-card{width:100%;max-width:420px;background:var(--surface);color:var(--text);border:1px solid var(--border);border-radius:16px;padding:16px 18px;box-shadow:0 10px 30px rgba(0,0,0,.25)}
.ask-card p{margin:0 0 12px;font-size:1.02rem}
.ask-actions{display:flex;gap:8px;justify-content:flex-end}
.hint-chip{position:fixed;left:50%;transform:translateX(-50%);bottom:calc(20px + env(safe-area-inset-bottom));z-index:65;border:0;border-radius:99px;padding:10px 16px;background:var(--accent);color:var(--accent-ink);font:inherit;font-weight:650;box-shadow:0 6px 20px rgba(0,0,0,.25);cursor:pointer;max-width:90vw;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.to-top{position:fixed;right:16px;bottom:16px;z-index:25;width:44px;height:44px;border-radius:50%;border:1px solid var(--border);background:var(--surface);color:var(--text);font-size:1.2rem;cursor:pointer;box-shadow:var(--shadow);opacity:0;pointer-events:none;transition:opacity .2s}
.to-top.show{opacity:1;pointer-events:auto}
.foot{color:var(--muted);font-size:.85rem;text-align:center;padding:12px 0}
body.modal-open{overflow:hidden}
.print-toc,.print-only{display:none}
@media (min-width:721px){.svc-overlay{align-items:center;padding:16px}.svc-card{border-radius:18px}}
@media (min-width:961px){#btn-toc{display:none}}
@media (max-width:960px){
  .layout{grid-template-columns:minmax(0,1fr)}
  .toc{position:fixed;top:0;left:0;bottom:0;width:min(86vw,340px);max-height:none;z-index:50;background:var(--surface);border-right:1px solid var(--border);padding:16px;transform:translateX(-105%);transition:transform .2s ease}
  body.toc-open .toc{transform:none}
  body.toc-open .scrim{display:block}
  .tabs{position:fixed;left:0;right:0;bottom:0;z-index:40;background:var(--surface);border-top:1px solid var(--border);margin:0;max-width:none;padding:4px 4px calc(4px + env(safe-area-inset-bottom));gap:0;flex-wrap:nowrap;justify-content:space-around;box-shadow:0 -2px 10px rgba(0,0,0,.06)}
  .tab{flex:1;flex-direction:column;gap:1px;border:0;border-radius:10px;padding:5px 2px;font-size:.68rem;background:none;justify-content:center}
  .tab .ti{font-size:1.25rem;line-height:1.1}
  .tab[aria-current="page"]{background:var(--accent-soft);color:var(--accent)}
  body{padding-bottom:calc(64px + env(safe-area-inset-bottom))}
  .to-top{bottom:calc(78px + env(safe-area-inset-bottom))}
  .hint-chip{bottom:calc(82px + env(safe-area-inset-bottom))}
  section,figure.diagram,article.lesson{scroll-margin-top:110px}
}
@media (max-width:720px){
  .lbl,.brand-sub{display:none}
  .search{order:5;flex-basis:100%}
  section{padding:14px 14px 6px;border-radius:12px}
  .card{padding:14px}
  article.lesson{padding:14px}
  h2{font-size:1.15rem}
  .flow{flex-direction:column}
  .flow>.ar{transform:rotate(90deg)}
  .dr{grid-template-columns:1fr 1fr}
  .dec-step{grid-template-columns:auto 1fr}
  .dec-out{grid-column:2}
  .qz-hint kbd{display:none}
}
@media (max-width:560px){.dg-azs{grid-template-columns:1fr}}
@media screen and (max-width:640px){
  .tbl:not(.tbl-2){border:0;overflow:visible}
  .tbl:not(.tbl-2) table,.tbl:not(.tbl-2) tbody,.tbl:not(.tbl-2) tr,.tbl:not(.tbl-2) td{display:block;width:100%}
  .tbl:not(.tbl-2) thead{display:none}
  .tbl:not(.tbl-2) tbody tr{border:1px solid var(--border);border-radius:10px;margin:0 0 8px;padding:6px 10px;background:var(--surface)}
  .tbl:not(.tbl-2) tbody tr:nth-child(even) td{background:none}
  .tbl:not(.tbl-2) td{border:0;padding:3px 0}
  .tbl:not(.tbl-2) td::before{content:attr(data-label);display:block;font-size:.75rem;color:var(--muted);font-weight:600}
  .tbl:not(.tbl-2) td:first-child::before{display:none}
  .tbl:not(.tbl-2) td:first-child{font-weight:650}
  .tbl-2 th,.tbl-2 td{padding:6px 8px}
}
@page{size:A5;margin:12mm 10mm 14mm;@bottom-center{content:counter(page);font-size:8pt;color:#777}}
@media print{
  :root,:root[data-theme="dark"]{
    --bg:#fff;--surface:#fff;--surface-2:#f1f3f6;--zebra:#f7f8fa;--text:#111;--muted:#555;--border:#d7dbe0;--border-strong:#b8c0ca;
    --accent:#1f5fcf;--accent-soft:#e9f0fd;--trg:#0b4fb8;--trg-bg:#f3f7ff;--trg-line:#c9dafa;
    --warn:#7a4a00;--warn-bg:#fff7e6;--warn-line:#efcf93;--code-bg:#eef0f3;--ok:#1f7a45;--ok-bg:#eaf7ef;--bad:#b42318;--bad-bg:#fdecea;
    --c-net:#7c3aed;--c-cmp:#c2410c;--c-db:#1d4ed8;--c-sto:#15803d;--c-sec:#b91c1c;--c-int:#be185d;--c-ana:#0f766e;
    color-scheme:light;
  }
  html{font-size:10.5pt}
  body{background:#fff;line-height:1.45;padding:0;-webkit-print-color-adjust:exact;print-color-adjust:exact}
  p,li{margin:3px 0}
  h3{margin:10px 0 4px}
  h4{margin:9px 0 5px}
  .topbar,.tabs,.toc,.scrim,.learn-btn,.to-top,.skip,.how,.foot,.progress-line,.seg,.hint-chip,.svc-overlay,.lesson-nav,.lesson-top .back,.progress-card,.quiz-links,.install-card,.ask-overlay,.offline-ok,#learn-summary{display:none!important}
  body.print-lessons article a[href^="#fig-"]::after{content:" (у PDF «Шпаргалка»)";color:var(--muted);font-weight:400}
  .svc{text-decoration:none!important;background:none!important}
  .view{display:none!important}
  #view-sheet{display:block!important}
  body.print-lessons #view-sheet{display:none!important}
  body.print-lessons #view-learn{display:block!important}
  body.print-lessons #learn-home{display:none!important}
  body.print-lessons .print-lessons-only{display:block!important}
  body.print-lessons article.lesson{display:block!important;break-before:page;border:0;box-shadow:none;padding:0;margin:0;max-width:none}
  .print-only{display:block}
  .layout{display:block;padding:0;max-width:none}
  main,.page{padding:0;max-width:none}
  .hero{padding:30mm 0 0}
  .print-toc{display:block;break-before:page}
  .print-toc h2{margin:0 0 3mm}
  .print-toc a{display:flex;gap:6px;color:inherit;text-decoration:none;padding:1mm 0;border-bottom:.5px dotted #bbb}
  .print-toc a .n{min-width:1.8em;color:var(--accent);font-weight:700}
  section{border:0;box-shadow:none;border-radius:0;padding:0;margin:0;break-before:page}
  body.print-quick .hero{padding:4mm 0 0}
  body.print-quick section{break-before:auto;margin-top:7mm}
  body.print-quick section.first-quick{break-before:page;margin-top:0}
  .sec-head{border-bottom:1.5px solid var(--accent)}
  h2,h3,h4{break-after:avoid}
  li,tr,.callout,.diagram,pre.code,.pq,.pa{break-inside:avoid}
  .trg-list>li,.warn-list>li,.rem-list>li{padding:2px 7px;border-radius:6px}
  .trg-list,.warn-list,.rem-list{gap:3px;margin:4px 0 8px}
  ul,ol{margin:3px 0 8px}
  .trg .ans{filter:none!important}
  a{color:inherit;text-decoration:none}
  .tbl{overflow:visible;border-radius:0}
  table{font-size:8.2pt}
  th,td{padding:4px 6px}
  .diagram{font-size:8.5pt}
  .flow{flex-direction:column}
  .flow>.ar{transform:rotate(90deg)}
  .dr{grid-template-columns:1fr 1fr}
}
.pq{border:1px solid var(--border);border-radius:10px;padding:8px 10px;margin:0 0 8px;background:var(--surface)}
.pq-h{font-weight:700;color:var(--accent);font-size:.9rem}
.pq-ua{color:var(--muted);font-size:.92rem;margin:4px 0}
.pq ol{margin:6px 0 2px;padding-left:1.6rem}
.pa{margin:0 0 6px;padding:6px 8px;border-left:3px solid var(--ok);background:var(--surface)}
"""

# ---------- Скрипт сторінки ----------

JS = r"""
(function(){
  var $=function(s,r){return (r||document).querySelector(s)};
  var $$=function(s,r){return Array.prototype.slice.call((r||document).querySelectorAll(s))};
  var store={get:function(k,d){try{var v=localStorage.getItem(k);return v===null?d:JSON.parse(v)}catch(e){return d}},
             set:function(k,v){try{localStorage.setItem(k,JSON.stringify(v))}catch(e){}}};
  var body=document.body, root=document.documentElement;
  function esc(s){return String(s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
  function txt(h){var d=document.createElement('div');d.innerHTML=h;return d.textContent}
  function idle(fn){(window.requestIdleCallback||function(cb){return setTimeout(cb,30)})(fn)}
  function ask(text,yes){
    var o=$('#ask'),y=$('#ask-yes'),n=$('#ask-no');
    $('#ask-text').textContent=text; o.hidden=false; body.classList.add('modal-open');
    function close(){o.hidden=true;body.classList.remove('modal-open');y.onclick=n.onclick=o.onclick=null}
    y.onclick=function(){close();yes()}; n.onclick=close; o.onclick=function(e){if(e.target===o){close()}};
    y.focus();
  }

  var SVC=JSON.parse($('#sdata').textContent), SMAP={}; SVC.forEach(function(s){SMAP[s.id]=s});
  var LES=JSON.parse($('#ldata').textContent), LMAP={}; LES.forEach(function(l){LMAP[l.id]=l});
  var CATS=JSON.parse($('#cdata').textContent);

  /* тема */
  var theme=store.get('saa.theme',null); if(theme){root.setAttribute('data-theme',theme)}
  $('#btn-theme').addEventListener('click',function(){
    var cur=root.getAttribute('data-theme');
    var dark=cur?cur==='dark':window.matchMedia('(prefers-color-scheme: dark)').matches;
    root.setAttribute('data-theme',dark?'light':'dark'); store.set('saa.theme',dark?'light':'dark');
  });

  /* сховати відповіді */
  (function(){
    var btn=$('#btn-hide');
    function apply(on){body.classList.toggle('hide-ans',on);btn.setAttribute('aria-pressed',on?'true':'false')}
    apply(!!store.get('saa.hideAns',false));
    btn.addEventListener('click',function(){var on=!body.classList.contains('hide-ans');apply(on);store.set('saa.hideAns',on);
      $$('.ans.revealed').forEach(function(e){e.classList.remove('revealed')})});
    document.addEventListener('click',function(e){
      var a=e.target.closest('.trg .ans'); if(!a||!body.classList.contains('hide-ans')){return}
      if(!a.classList.contains('revealed')){a.classList.add('revealed');e.preventDefault();e.stopImmediatePropagation();return}
      if(!e.target.closest('.svc')){a.classList.remove('revealed')}
    });
  })();

  /* меню PDF і зміст */
  var dl=$('.dl');
  document.addEventListener('click',function(e){if(dl&&dl.open&&!dl.contains(e.target)){dl.open=false}});
  $('#btn-toc').addEventListener('click',function(){body.classList.toggle('toc-open')});
  $('#scrim').addEventListener('click',function(){body.classList.remove('toc-open')});
  $$('.toc a').forEach(function(a){a.addEventListener('click',function(){body.classList.remove('toc-open')})});

  /* шпаргалка: «Вивчено» */
  var sections=$$('#view-sheet main section');
  var learnIds=$$('.learn-btn').map(function(b){return b.dataset.sec});
  var learned=store.get('saa.learned',[]); if(!Array.isArray(learned)){learned=[]}
  function renderLearned(){
    $$('.learn-btn').forEach(function(b){var on=learned.indexOf(b.dataset.sec)>=0;
      b.setAttribute('aria-pressed',on?'true':'false'); b.textContent=on?'✅ Вивчено':'☐ Вивчено'});
    $$('.toc a[data-sec]').forEach(function(a){a.classList.toggle('done',learned.indexOf(a.dataset.sec)>=0)});
    var done=learnIds.filter(function(id){return learned.indexOf(id)>=0}).length;
    $('#progress').textContent='Вивчено: '+done+' / '+learnIds.length;
    $('#progress-bar').style.width=(learnIds.length?Math.round(done*100/learnIds.length):0)+'%';
    renderSummary();
  }
  $$('.learn-btn').forEach(function(b){b.addEventListener('click',function(){
    var id=b.dataset.sec,k=learned.indexOf(id); if(k>=0){learned.splice(k,1)}else{learned.push(id)}
    store.set('saa.learned',learned); renderLearned();
  })});

  /* пошук у шпаргалці */
  var input=$('#q'), info=$('#search-info'), timer=null;
  input.addEventListener('input',function(){clearTimeout(timer);timer=setTimeout(function(){
    if(body.dataset.view!=='sheet'&&body.dataset.view!=='quick'){location.hash='#sheet'}
    search(input.value)},150)});
  function search(raw){
    var q=raw.trim().toLowerCase(), hits=0;
    sections.forEach(function(sec){
      var items=$$('li, tbody tr, p, .callout, figure.diagram, pre.code',sec), tables=$$('.tbl',sec);
      if(!q){items.concat(tables).forEach(function(el){el.classList.remove('hit-hidden')});sec.classList.remove('hit-hidden');return}
      var any=false;
      items.forEach(function(el){
        if(el.closest('figure.diagram')&&!el.matches('figure.diagram')){return}
        var m=el.textContent.toLowerCase().indexOf(q)>=0;el.classList.toggle('hit-hidden',!m);if(m){any=true;hits++}});
      $$('li:not(.hit-hidden)',sec).forEach(function(li){$$('.hit-hidden',li).forEach(function(d){d.classList.remove('hit-hidden')})});
      tables.forEach(function(t){t.classList.toggle('hit-hidden',!$$('tbody tr:not(.hit-hidden)',t).length)});
      if(!any&&$('.sec-head',sec).textContent.toLowerCase().indexOf(q)>=0){items.concat(tables).forEach(function(el){el.classList.remove('hit-hidden')});any=true}
      sec.classList.toggle('hit-hidden',!any);
    });
    $('#view-sheet .hero').classList.toggle('hit-hidden',!!q);
    info.textContent=q?(hits?'Знайдено: '+hits:'Нічого не знайдено'):'';
  }

  if('IntersectionObserver' in window){
    var links={}; $$('.toc a[data-sec]').forEach(function(a){links[a.dataset.sec]=a});
    var io=new IntersectionObserver(function(entries){entries.forEach(function(en){
      if(en.isIntersecting){$$('.toc a.current').forEach(function(a){a.classList.remove('current')});
        var l=links[en.target.id]; if(l){l.classList.add('current')}}
    })},{rootMargin:'-120px 0px -70% 0px'});
    sections.forEach(function(s){io.observe(s)});
  }
  var topBtn=$('#to-top');
  window.addEventListener('scroll',function(){topBtn.classList.toggle('show',window.scrollY>700)},{passive:true});
  topBtn.addEventListener('click',function(){window.scrollTo({top:0})});

  /* ---------- підказки ---------- */
  var hintsOn=store.get('saa.hints',true)!==false;
  var aliasPairs=[]; SVC.forEach(function(s){s.aliases.forEach(function(a){aliasPairs.push([a,s.id])})});
  aliasPairs.sort(function(x,y){return y[0].length-x[0].length});
  var ALIAS={}, ALIAS_LC={};
  aliasPairs.forEach(function(p){ALIAS[p[0]]=p[1];var k=p[0].toLowerCase();if(!ALIAS_LC[k]){ALIAS_LC[k]=p[1]}});
  var RX=new RegExp(aliasPairs.map(function(p){return p[0].replace(/[.*+?^${}()|[\]\\]/g,'\\$&')}).join('|'),'g');
  var WORDCH=/[0-9A-Za-zА-ЩЬЮЯҐЄІЇа-щьюяґєії_]/;
  var SKIP='code,pre,a,button,.svc,input,textarea,select,script,style,.svc-card,summary,.tab,.seg,kbd,.lesson-card,.t-opt';
  function firstAlias(t){
    RX.lastIndex=0; var m;
    while((m=RX.exec(t))){var s=m.index,e=s+m[0].length;
      if((s>0&&WORDCH.test(t[s-1]))||(e<t.length&&WORDCH.test(t[e]))){RX.lastIndex=s+1;continue}
      return ALIAS[m[0]]}
    return null;
  }
  function linkify(el,force){
    if(!el||!hintsOn){return}
    if(el.dataset.linked&&!force){return}
    el.dataset.linked='1';
    var walker=document.createTreeWalker(el,NodeFilter.SHOW_TEXT,{acceptNode:function(n){
      if(!n.nodeValue.trim()){return NodeFilter.FILTER_REJECT}
      var p=n.parentElement; if(!p||p.closest(SKIP)){return NodeFilter.FILTER_REJECT}
      return NodeFilter.FILTER_ACCEPT}});
    var nodes=[]; while(walker.nextNode()){nodes.push(walker.currentNode)}
    nodes.forEach(function(n){
      var t=n.nodeValue,m,last=0,frag=null; RX.lastIndex=0;
      while((m=RX.exec(t))){
        var s=m.index,e=s+m[0].length;
        if((s>0&&WORDCH.test(t[s-1]))||(e<t.length&&WORDCH.test(t[e]))){RX.lastIndex=s+1;continue}
        if(!frag){frag=document.createDocumentFragment()}
        if(s>last){frag.appendChild(document.createTextNode(t.slice(last,s)))}
        var sp=document.createElement('span'); sp.className='svc'; sp.dataset.svc=ALIAS[m[0]]; sp.textContent=m[0];
        frag.appendChild(sp); last=e;
      }
      if(frag){if(last<t.length){frag.appendChild(document.createTextNode(t.slice(last)))}n.parentNode.replaceChild(frag,n)}
    });
  }
  function hintsSheet(){
    if(!hintsOn){return}
    var queue=sections.filter(function(s){return !s.dataset.linked});
    (function step(){var s=queue.shift();if(!s){return}linkify(s);idle(step)})();
  }
  var overlay=$('#svc-overlay');
  function openCard(id){
    var s=SMAP[id]; if(!s){return}
    $('#svc-emoji').textContent=s.emoji; $('#svc-title').textContent=s.name; $('#svc-cat').textContent=CATS[s.cat]||'';
    $('#svc-what').innerHTML=s.what; $('#svc-image').innerHTML='<b>🖼️ Образ.</b> '+s.image;
    $('#svc-when').innerHTML=s.when.map(function(w){return '<li>'+w+'</li>'}).join('');
    $('#svc-when-h').hidden=!s.when.length;
    $('#svc-exam').innerHTML=s.exam.map(function(x){return '<li>'+x+'</li>'}).join('');
    $('#svc-exam-h').hidden=!s.exam.length;
    $('#svc-confuse').innerHTML=s.confuse.length?('<span class="muted">Не плутай з:</span> '+s.confuse.map(function(c){var o=SMAP[c];
      return o?'<button class="chip-btn" type="button" data-open="'+c+'">'+o.emoji+' '+esc(o.name)+'</button>':''}).join(' ')):'';
    var l=LMAP[s.lesson], out='';
    if(l){out+='<a class="tb-btn primary" href="#learn/'+l.id+'">📖 Урок: '+esc(l.emoji+' '+l.title)+'</a>'}
    out+='<button class="tb-btn" type="button" data-find="'+esc(s.aliases[0]||s.name)+'">🔍 Знайти в шпаргалці</button>';
    $('#svc-links').innerHTML=out;
    overlay.hidden=false; body.classList.add('modal-open'); $('.svc-card').scrollTop=0;
  }
  function closeCard(){overlay.hidden=true;body.classList.remove('modal-open')}
  overlay.addEventListener('click',function(e){
    if(e.target===overlay){closeCard();return}
    var b=e.target.closest('[data-open]'); if(b){openCard(b.dataset.open);return}
    var f=e.target.closest('[data-find]');
    if(f){closeCard();location.hash='#sheet';input.value=f.dataset.find;search(f.dataset.find);window.scrollTo({top:0});return}
    if(e.target.closest('a[href^="#learn/"]')){closeCard()}
  });
  $('#svc-close').addEventListener('click',closeCard);
  document.addEventListener('keydown',function(e){if(e.key!=='Escape'){return}
    if(!$('#ask').hidden){$('#ask-no').click()}else if(!overlay.hidden){closeCard()}});
  document.addEventListener('click',function(e){
    var s=e.target.closest('.svc'); if(!s||!hintsOn||s.closest('.svc-card')){return}
    e.preventDefault(); openCard(s.dataset.svc);
  });
  var chip=$('#hint-chip'), selTimer=null;
  document.addEventListener('selectionchange',function(){
    clearTimeout(selTimer);
    selTimer=setTimeout(function(){
      if(!hintsOn){chip.hidden=true;return}
      var sel=window.getSelection(), t=sel?sel.toString().trim():'';
      if(!t||t.length>80){chip.hidden=true;return}
      var node=sel.anchorNode&&(sel.anchorNode.nodeType===1?sel.anchorNode:sel.anchorNode.parentElement);
      if(node&&node.closest('.svc-card,input,textarea')){chip.hidden=true;return}
      var id=ALIAS[t]||ALIAS_LC[t.toLowerCase()]||firstAlias(t);
      if(!id){chip.hidden=true;return}
      chip.dataset.svc=id; chip.textContent='🤖 Пояснити: '+SMAP[id].name; chip.hidden=false;
    },350);
  });
  chip.addEventListener('click',function(){openCard(chip.dataset.svc);chip.hidden=true;try{window.getSelection().removeAllRanges()}catch(e){}});
  var hb=$('#btn-hints');
  function applyHints(on){
    hintsOn=on; body.classList.toggle('hints-on',on); hb.setAttribute('aria-pressed',on?'true':'false'); store.set('saa.hints',on);
    if(on){hintsCurrent()}else{chip.hidden=true}
  }
  hb.addEventListener('click',function(){applyHints(!hintsOn)});

  /* ---------- довідник ---------- */
  var sq=$('#svc-q'), scat='all', catBox=$('#svc-cats');
  SVC.forEach(function(s){s.q=(s.name+' '+s.aliases.join(' ')+' '+txt(s.what)+' '+txt(s.image)).toLowerCase()});
  var catKeys=Object.keys(CATS).filter(function(k){return SVC.some(function(s){return s.cat===k})});
  catBox.innerHTML='<button class="cat-chip" type="button" data-cat="all" aria-pressed="true">Усі</button>'+
    catKeys.map(function(k){return '<button class="cat-chip" type="button" data-cat="'+k+'" aria-pressed="false">'+esc(CATS[k])+'</button>'}).join('');
  function sortKey(s){var n=/^[А-ЯҐЄІЇа-яґєії]/.test(s.name)&&s.aliases.length?s.aliases[0]:s.name;return n.replace(/^(Amazon|AWS)\s+/,'').toLowerCase()}
  function renderDir(){
    var q=sq.value.trim().toLowerCase();
    var list=SVC.filter(function(s){return (scat==='all'||s.cat===scat)&&(!q||s.q.indexOf(q)>=0)});
    list.sort(function(a,b){return sortKey(a).localeCompare(sortKey(b),'en')});
    $('#svc-grid').innerHTML=list.map(function(s){return '<button class="svc-item" type="button" data-open="'+s.id+'"><span class="svc-e">'+s.emoji+'</span><span><b>'+esc(s.name)+'</b><small>'+esc(txt(s.what))+'</small></span></button>'}).join('')||'<p class="muted">Нічого не знайдено.</p>';
    $('#svc-count').textContent='Показано: '+list.length+' з '+SVC.length;
  }
  catBox.addEventListener('click',function(e){var b=e.target.closest('[data-cat]');if(!b){return}scat=b.dataset.cat;
    $$('.cat-chip',catBox).forEach(function(c){c.setAttribute('aria-pressed',c===b?'true':'false')});renderDir()});
  sq.addEventListener('input',function(){renderDir()});
  $('#svc-grid').addEventListener('click',function(e){var b=e.target.closest('[data-open]');if(b){openCard(b.dataset.open)}});

  /* ---------- уроки ---------- */
  var done=store.get('saa.lessons',[]); if(!Array.isArray(done)){done=[]}
  function renderLessons(){
    $$('.lesson-card').forEach(function(c){c.classList.toggle('done',done.indexOf(c.dataset.id)>=0)});
    $$('.done-btn').forEach(function(b){var on=done.indexOf(b.dataset.id)>=0;b.setAttribute('aria-pressed',on?'true':'false');b.textContent=on?'✅ Пройдено':'☐ Позначити пройденим'});
    var n=LES.filter(function(l){return done.indexOf(l.id)>=0}).length;
    $('#learn-progress-text').textContent='Пройдено уроків: '+n+' з '+LES.length;
    $('#learn-bar').style.width=Math.round(n*100/LES.length)+'%';
    var last=store.get('saa.lastLesson',null), cont=$('#learn-continue');
    var target=(last&&LMAP[last])?LMAP[last]:(LES.filter(function(l){return done.indexOf(l.id)<0})[0]||LES[0]);
    cont.href='#learn/'+target.id; cont.textContent=(last?'▶ Продовжити: ':'▶ Почати: ')+target.emoji+' '+target.title;
    renderSummary();
  }
  $$('.done-btn').forEach(function(b){b.addEventListener('click',function(){
    var id=b.dataset.id,k=done.indexOf(id);if(k>=0){done.splice(k,1)}else{done.push(id)}
    store.set('saa.lessons',done);renderLessons()})});
  function showLearnHome(){$('#learn-home').hidden=false;$$('article.lesson').forEach(function(a){a.hidden=true})}
  function openLesson(id){
    var art=document.getElementById('lesson-'+id); if(!art){showLearnHome();return}
    $('#learn-home').hidden=true; $$('article.lesson').forEach(function(a){a.hidden=a!==art});
    store.set('saa.lastLesson',id); linkify(art); renderLessons();
  }
  var pendingScope=null;
  document.addEventListener('click',function(e){var a=e.target.closest('[data-quiz-scope]');if(a){pendingScope=a.dataset.quizScope}});

  /* ---------- схеми ---------- */
  var gal=$('#dg-gallery');
  $$('#view-learn figure.diagram, #view-sheet figure.diagram').forEach(function(fig){
    var sec=fig.closest('section, article'), wrap=document.createElement('div'); wrap.className='dg-item';
    var h=document.createElement('h2'); h.textContent=fig.dataset.caption||'';
    var clone=fig.cloneNode(true); clone.removeAttribute('id');
    var a=document.createElement('a'); a.className='dg-link'; a.href='#'+fig.id;
    a.textContent=(sec&&sec.tagName==='ARTICLE'?'До уроку «':'До розділу «')+(sec?sec.dataset.title:'')+'» →';
    wrap.appendChild(h); wrap.appendChild(clone); wrap.appendChild(a); gal.appendChild(wrap);
  });

  /* ---------- квіз ---------- */
  var trgs=$$('#view-sheet li.trg').map(function(li){var s=li.closest('section');
    return {id:li.dataset.id,q:li.querySelector('.q').textContent.trim(),a:li.querySelector('.ans').innerHTML,sec:s.dataset.title,sid:s.id}});
  var qstat=store.get('saa.quiz',{}); if(!qstat||typeof qstat!=='object'){qstat={}}
  var qscope=$('#qz-scope'), qweak=$('#qz-weak'), qcur=null, qlast=null, qs={k:0,u:0}, seen={};
  trgs.forEach(function(t){if(!seen[t.sid]){seen[t.sid]=1;var o=document.createElement('option');o.value=t.sid;o.textContent=t.sec;qscope.appendChild(o)}});
  function qpool(){var s=qscope.value,w=qweak.checked;
    return trgs.filter(function(t){return (s==='all'||t.sid===s)&&(!w||(qstat[t.id]&&qstat[t.id].l==='u'))})}
  function qstats(){
    var known=trgs.filter(function(t){return qstat[t.id]&&qstat[t.id].l==='k'}).length;
    var weak=trgs.filter(function(t){return qstat[t.id]&&qstat[t.id].l==='u'}).length;
    $('#qz-stats').textContent='Зараз: ✓ '+qs.k+' · ✗ '+qs.u+'   |   Усього знаєш: '+known+' з '+trgs.length+' · слабких: '+weak;
    renderSummary();
  }
  function qnext(){
    var pool=qpool();
    if(!pool.length){qcur=null;$('#qz-sec').textContent='';
      $('#qz-q').textContent=qweak.checked?'Слабких тригерів немає 🎉 Зніми галочку «Лише слабкі».':'У цьому наборі немає тригерів.';
      $('#qz-a').hidden=true;$('#qz-show').hidden=true;$('#qz-know').hidden=true;$('#qz-dont').hidden=true;qstats();return}
    var weak=pool.filter(function(t){var st=qstat[t.id];return !st||st.l==='u'});
    var from=(weak.length&&Math.random()<0.6)?weak:pool, c, tries=0;
    do{c=from[Math.floor(Math.random()*from.length)];tries++}while(from.length>1&&qlast&&c.id===qlast.id&&tries<12);
    qcur=c;qlast=c;
    $('#qz-sec').textContent=c.sec; $('#qz-q').textContent=c.q; linkify($('#qz-q'),true);
    $('#qz-a').innerHTML=c.a; $('#qz-a').hidden=true;
    $('#qz-show').hidden=false;$('#qz-know').hidden=true;$('#qz-dont').hidden=true;qstats();
  }
  function qshow(){if(!qcur){return}$('#qz-a').hidden=false;linkify($('#qz-a'),true);$('#qz-show').hidden=true;$('#qz-know').hidden=false;$('#qz-dont').hidden=false}
  function qmark(ok){if(!qcur){return}var st=qstat[qcur.id]||{k:0,u:0};if(ok){st.k++}else{st.u++}st.l=ok?'k':'u';
    qstat[qcur.id]=st;store.set('saa.quiz',qstat);if(ok){qs.k++}else{qs.u++}qnext()}
  $('#qz-show').addEventListener('click',qshow);
  $('#qz-know').addEventListener('click',function(){qmark(true)});
  $('#qz-dont').addEventListener('click',function(){qmark(false)});
  qscope.addEventListener('change',qnext); qweak.addEventListener('change',qnext);
  $('#qz-reset').addEventListener('click',function(){ask('Скинути статистику квізу?',function(){qstat={};store.set('saa.quiz',qstat);qs={k:0,u:0};qnext()})});
  document.addEventListener('keydown',function(e){
    if(body.dataset.view!=='quiz'||!overlay.hidden||!$('#ask').hidden||e.target.closest('input,select,textarea,button')){return}
    if((e.key===' '||e.key==='Enter')&&!$('#qz-show').hidden){e.preventDefault();qshow()}
    else if(e.key==='ArrowRight'&&!$('#qz-know').hidden){qmark(true)}
    else if(e.key==='ArrowLeft'&&!$('#qz-dont').hidden){qmark(false)}
  });

  /* ---------- практичний тест ---------- */
  var QS=JSON.parse($('#qdata').textContent), QMAP={};
  QS.forEach(function(q){QMAP[q.id]=q});
  var DOM={secure:'Безпека',resilient:'Відмовостійкість',performance:'Продуктивність',cost:'Вартість'};
  var ts=store.get('saa.test',null); if(ts&&(!ts.ids||!ts.ids.every(function(id){return QMAP[id]}))){ts=null}
  var thist=store.get('saa.testHistory',[]); if(!Array.isArray(thist)){thist=[]}
  var twrong=store.get('saa.testWrong',[]); if(!Array.isArray(twrong)){twrong=[]}
  var showUa=!!store.get('saa.qUa',false), tick=null;
  function L(i){return String.fromCharCode(65+i)}
  function tsave(){store.set('saa.test',ts)}
  function right(q,a){a=(a||[]).slice().sort();var c=q.correct.slice().sort();if(a.length!==c.length){return false}
    for(var i=0;i<a.length;i++){if(a[i]!==c[i]){return false}}return true}
  function markWrong(q,ok){var k=twrong.indexOf(q.id);if(ok&&k>=0){twrong.splice(k,1)}if(!ok&&k<0){twrong.push(q.id)}store.set('saa.testWrong',twrong)}
  function panel(id){['#t-start','#t-run','#t-result'].forEach(function(p){$(p).hidden=(p!==id)})}
  function fillSets(){var sel=$('#t-set'),keep=sel.value;sel.innerHTML='';
    function add(v,t){var o=document.createElement('option');o.value=v;o.textContent=t;sel.appendChild(o)}
    add('all','Усі питання ('+QS.length+')');
    Object.keys(DOM).forEach(function(d){add(d,DOM[d]+' ('+QS.filter(function(q){return q.domain===d}).length+')')});
    add('wrong','Мої помилки ('+twrong.length+')'); if(keep){sel.value=keep}}
  function bestFull(){return thist.filter(function(x){return x.n>=QS.length}).reduce(function(m,x){return Math.max(m,x.pct)},-1)}
  function renderStart(){
    fillSets(); $('#t-msg').textContent='';
    var r=$('#t-resume');
    if(ts&&!ts.done){r.hidden=false;r.textContent='▶ Продовжити ('+(ts.idx+1)+' / '+ts.ids.length+')'}else{r.hidden=true}
    var h=$('#t-history');
    if(!thist.length){h.innerHTML='<p class="muted">Ще немає результатів. Почни з режиму «Тренування».</p>'}
    else{var b=bestFull();
      h.innerHTML=(b>=0?'<p><b>Найкращий повний тест: '+b+'%</b></p>':'')+'<p class="muted">Останні спроби:</p><ul class="t-hist">'+
        thist.slice(-6).reverse().map(function(x){return '<li>'+esc(x.date)+' · '+(x.mode==='exam'?'Іспит':'Тренування')+' · '+x.ok+' / '+x.n+' ('+x.pct+'%)</li>'}).join('')+'</ul>'}
    panel('#t-start');
  }
  function begin(){
    var mode=$('input[name="t-mode"]:checked').value, set=$('#t-set').value;
    var ids=QS.filter(function(q){return set==='all'||(set==='wrong'?twrong.indexOf(q.id)>=0:q.domain===set)}).map(function(q){return q.id});
    if(!ids.length){$('#t-msg').textContent='У цьому наборі поки немає питань.';return}
    if($('#t-shuffle').checked){for(var i=ids.length-1;i>0;i--){var j=Math.floor(Math.random()*(i+1)),t=ids[i];ids[i]=ids[j];ids[j]=t}}
    var mins=ids.length*2+($('#t-esl').checked?Math.ceil(ids.length*30/65):0);
    ts={mode:mode,set:set,ids:ids,idx:0,ans:{},chk:{},flag:{},start:Date.now(),deadline:mode==='exam'?Date.now()+mins*60000:0,done:false};
    tsave(); run();
  }
  function run(){panel('#t-run');renderQ();startTick();window.scrollTo({top:0})}
  function cq(){return QMAP[ts.ids[ts.idx]]}
  function renderQ(){
    var q=cq(),a=ts.ans[q.id]||[],exam=ts.mode==='exam',checked=!exam&&ts.chk[q.id],last=ts.idx===ts.ids.length-1;
    $('#t-pos').textContent='Питання '+(ts.idx+1)+' / '+ts.ids.length;
    $('#t-dom').textContent=DOM[q.domain];
    $('#t-stem').innerHTML=q.en; $('#t-alt').innerHTML=q.ua; $('#t-alt').hidden=!showUa;
    if(!exam){linkify($('#t-stem'),true);linkify($('#t-alt'),true)}
    $('#t-lang').textContent=showUa?'🇺🇦 Сховати переклад':'🇺🇦 Показати переклад';
    $('#t-note').textContent=q.multi?'Оберіть '+q.correct.length+' відповіді (Choose '+(q.correct.length===2?'TWO':q.correct.length)+')':'';
    var box=$('#t-opts'); box.innerHTML='';
    q.options.forEach(function(o,i){
      var b=document.createElement('button'); b.type='button'; b.className='t-opt';
      b.setAttribute('aria-pressed',a.indexOf(i)>=0?'true':'false');
      b.innerHTML='<span class="t-letter">'+L(i)+'</span><span>'+o+'</span>';
      if(checked){b.disabled=true;if(q.correct.indexOf(i)>=0){b.classList.add('right')}else if(a.indexOf(i)>=0){b.classList.add('wrong')}}
      b.addEventListener('click',function(){choose(i)}); box.appendChild(b);
    });
    var why=$('#t-why');
    if(checked){var ok=right(q,a);why.hidden=false;why.className='t-why '+(ok?'ok':'bad');
      why.innerHTML='<b>'+(ok?'✓ Правильно.':'✗ Неправильно. Правильна відповідь: '+q.correct.map(L).join(', ')+'.')+'</b> '+q.why;
      linkify(why,true)}
    else{why.hidden=true}
    $('#t-flag').hidden=!exam; $('#t-flag').setAttribute('aria-pressed',ts.flag[q.id]?'true':'false');
    $('#t-prev').hidden=!exam||ts.idx===0;
    $('#t-check').hidden=exam||checked; $('#t-check').disabled=!a.length;
    $('#t-next').hidden=last||(!exam&&!checked);
    $('#t-finish').textContent=exam?'Завершити тест':(checked&&last?'Показати результат':'Завершити');
    var nav=$('#t-nav'); nav.hidden=!exam;
    if(exam){nav.innerHTML='';ts.ids.forEach(function(id,i){var b=document.createElement('button');b.type='button';b.textContent=i+1;
      if((ts.ans[id]||[]).length){b.classList.add('ans')}if(ts.flag[id]){b.classList.add('flag')}if(i===ts.idx){b.classList.add('cur')}
      b.addEventListener('click',function(){ts.idx=i;tsave();renderQ()});nav.appendChild(b)})}
  }
  function choose(i){
    var q=cq(); if(ts.mode==='practice'&&ts.chk[q.id]){return}
    var a=(ts.ans[q.id]||[]).slice();
    if(q.multi){var k=a.indexOf(i);if(k>=0){a.splice(k,1)}else{a.push(i);if(a.length>q.correct.length){a.shift()}}}else{a=[i]}
    ts.ans[q.id]=a; tsave(); renderQ();
  }
  function check(){var q=cq();if(!(ts.ans[q.id]||[]).length){return}ts.chk[q.id]=true;markWrong(q,right(q,ts.ans[q.id]));tsave();renderQ()}
  function go(d){var n=ts.idx+d;if(n<0||n>=ts.ids.length){return}ts.idx=n;tsave();renderQ();window.scrollTo({top:0})}
  function finish(force){
    if(!ts){return}
    var exam=ts.mode==='exam', answered=ts.ids.filter(function(id){return (ts.ans[id]||[]).length}).length;
    if(!force&&exam&&answered<ts.ids.length){ask('Без відповіді: '+(ts.ids.length-answered)+'. Завершити тест?',function(){finish(true)});return}
    stopTick();
    var ids=exam?ts.ids:ts.ids.filter(function(id){return ts.chk[id]});
    if(!ids.length){ts=null;tsave();renderStart();return}
    var ok=0,dom={};
    ids.forEach(function(id){var q=QMAP[id],r=right(q,ts.ans[id]),d=dom[q.domain]||(dom[q.domain]={n:0,ok:0});d.n++;if(r){ok++;d.ok++}if(exam&&(ts.ans[id]||[]).length){markWrong(q,r)}});
    var pct=Math.round(ok*100/ids.length), secs=Math.round((Date.now()-ts.start)/1000), dt=new Date();
    thist.push({date:dt.toLocaleDateString('uk-UA')+' '+dt.toLocaleTimeString('uk-UA',{hour:'2-digit',minute:'2-digit'}),mode:ts.mode,n:ids.length,ok:ok,pct:pct});
    if(thist.length>30){thist=thist.slice(-30)} store.set('saa.testHistory',thist);
    ts.done=true; ts.result={ids:ids,ok:ok,pct:pct,dom:dom,secs:secs}; tsave(); renderResult(); renderSummary();
  }
  function renderResult(){
    var r=ts.result;
    $('#t-score').textContent=r.ok+' / '+r.ids.length+' · '+r.pct+'%';
    var bar=$('#t-bar'); bar.style.width=r.pct+'%'; bar.className=r.pct>=80?'ok':(r.pct>=70?'mid':'bad');
    $('#t-verdict').textContent=r.pct>=80?'🎉 Відмінно! Стабільно 80%+ — можна записуватися на іспит.':(r.pct>=70?'👍 Майже. Повтори слабкі домени й розбери помилки.':'📚 Ще потренуйся: розбери помилки й повтори відповідні уроки.');
    var rows=Object.keys(DOM).filter(function(k){return r.dom[k]}).map(function(k){var d=r.dom[k];
      return '<tr><td data-label="Домен">'+DOM[k]+'</td><td data-label="Правильно">'+d.ok+' / '+d.n+'</td><td data-label="%">'+Math.round(d.ok*100/d.n)+'%</td></tr>'}).join('');
    $('#t-domains').innerHTML='<div class="tbl"><table><thead><tr><th>Домен</th><th>Правильно</th><th>%</th></tr></thead><tbody>'+rows+'</tbody></table></div>'+
      '<p class="muted">Час: '+Math.floor(r.secs/60)+' хв '+(r.secs%60)+' с</p>';
    $('#t-review').innerHTML=''; panel('#t-result'); window.scrollTo({top:0});
  }
  function review(onlyWrong){
    var r=ts.result;
    var out=r.ids.map(function(id,i){var q=QMAP[id],a=ts.ans[id]||[],ok=right(q,a);if(onlyWrong&&ok){return ''}
      var opts=q.options.map(function(o,j){var c=q.correct.indexOf(j)>=0,ch=a.indexOf(j)>=0;
        return '<li class="'+(c?'right':(ch?'wrong':''))+'"><span class="t-letter">'+L(j)+'</span><span>'+o+(c?' ✓':'')+(ch&&!c?' ✗ (твоя відповідь)':'')+'</span></li>'}).join('');
      return '<div class="t-rev '+(ok?'':'bad')+'"><div class="t-rev-h">'+(ok?'✓':'✗')+' Питання '+(i+1)+' · '+DOM[q.domain]+'</div><div class="t-stem">'+q.en+'</div><div class="t-alt">'+q.ua+'</div><ul class="t-rev-opts">'+opts+'</ul><div class="t-why">'+q.why+'</div></div>'}).join('');
    $('#t-review').innerHTML=out||'<p>Помилок немає 🎉</p>'; linkify($('#t-review'),true);
  }
  function startTick(){stopTick();if(!ts||ts.mode!=='exam'){$('#t-timer').textContent='';return}tickFn();tick=setInterval(tickFn,1000)}
  function stopTick(){if(tick){clearInterval(tick);tick=null}}
  function tickFn(){if(!ts||ts.done){stopTick();return}var left=Math.max(0,ts.deadline-Date.now()),m=Math.floor(left/60000),s=Math.floor(left%60000/1000);
    $('#t-timer').textContent='⏱ '+m+':'+(s<10?'0':'')+s;$('#t-timer').classList.toggle('low',left<300000);if(left<=0){finish(true)}}
  $('#t-begin').addEventListener('click',begin);
  $('#t-resume').addEventListener('click',run);
  $('#t-check').addEventListener('click',check);
  $('#t-next').addEventListener('click',function(){go(1)});
  $('#t-prev').addEventListener('click',function(){go(-1)});
  $('#t-finish').addEventListener('click',function(){finish(false)});
  $('#t-flag').addEventListener('click',function(){var q=cq();ts.flag[q.id]=!ts.flag[q.id];tsave();renderQ()});
  $('#t-lang').addEventListener('click',function(){showUa=!showUa;store.set('saa.qUa',showUa);renderQ()});
  $('#t-review-all').addEventListener('click',function(){review(false)});
  $('#t-review-wrong').addEventListener('click',function(){review(true)});
  $('#t-new').addEventListener('click',function(){renderStart();window.scrollTo({top:0})});
  $('#t-retry').addEventListener('click',function(){renderStart();$('#t-set').value='wrong';window.scrollTo({top:0})});

  /* ---------- підсумок прогресу ---------- */
  function renderSummary(){
    if(typeof trgs==='undefined'||typeof thist==='undefined'){return}
    var ld=LES.filter(function(l){return done.indexOf(l.id)>=0}).length;
    var sd=learnIds.filter(function(id){return learned.indexOf(id)>=0}).length;
    var known=trgs.filter(function(t){return qstat[t.id]&&qstat[t.id].l==='k'}).length;
    var b=bestFull();
    var box=$('#learn-summary');
    if(box){box.innerHTML='<div class="stat"><b>'+ld+' / '+LES.length+'</b><span>уроків пройдено</span></div>'+
      '<div class="stat"><b>'+sd+' / '+learnIds.length+'</b><span>розділів шпаргалки</span></div>'+
      '<div class="stat"><b>'+known+' / '+trgs.length+'</b><span>тригерів знаєш</span></div>'+
      '<div class="stat"><b>'+(b>=0?b+'%':'—')+'</b><span>найкращий тест</span></div>'}
    var hp=$('#hero-progress');
    if(hp){hp.textContent='Твій прогрес: розділів '+sd+' / '+learnIds.length+' · тригерів '+known+' / '+trgs.length+(b>=0?' · найкращий тест '+b+'%':'')}
  }

  /* ---------- перемикання вкладок ---------- */
  var TAB_OF={learn:'learn',sheet:'sheet',quick:'sheet',diagrams:'diagrams',quiz:'practice',test:'practice',services:'services'};
  var cur='learn';
  function hintsCurrent(){
    if(!hintsOn){return}
    if(cur==='sheet'||cur==='quick'){hintsSheet()}
    else if(cur==='diagrams'){linkify(gal)}
    else if(cur==='learn'){var art=$$('article.lesson').filter(function(a){return !a.hidden})[0];if(art){linkify(art)}}
  }
  function setView(v){
    cur=v; body.dataset.view=v; var tab=TAB_OF[v];
    $$('.view').forEach(function(el){el.hidden=el.dataset.view!==tab});
    body.classList.toggle('only-trg',v==='quick'||body.classList.contains('print-quick'));
    $$('.tab').forEach(function(t){t.setAttribute('aria-current',t.dataset.tab===tab?'page':'false');
      if(t.dataset.tab===tab&&(tab==='sheet'||tab==='practice')){t.setAttribute('href','#'+v)}});
    $$('.seg a').forEach(function(a){a.setAttribute('aria-current',a.dataset.v===v?'page':'false')});
    $('#practice-quiz').hidden=v!=='quiz'; $('#practice-test').hidden=v!=='test';
    body.classList.remove('toc-open'); chip.hidden=true;
    store.set('saa2.view',v);
    if(v==='quiz'){if(pendingScope){qscope.value=pendingScope;pendingScope=null;qnext()}else if(!qcur){qnext()}}
    if(v==='test'&&$('#t-run').hidden&&$('#t-result').hidden){renderStart()}
    if(v==='services'){renderDir()}
    hintsCurrent();
  }
  function route(){
    var h=decodeURIComponent(location.hash.slice(1));
    if(h==='learn'){setView('learn');showLearnHome();window.scrollTo({top:0});return}
    if(h.indexOf('learn/')===0){setView('learn');openLesson(h.slice(6));window.scrollTo({top:0});return}
    if(TAB_OF[h]){setView(h);window.scrollTo({top:0});return}
    var el=h?document.getElementById(h):null;
    if(el){
      var vw=el.closest('.view');
      if(vw&&vw.dataset.view==='learn'){var art=el.closest('article.lesson');setView('learn');if(art){openLesson(art.dataset.id)}
        setTimeout(function(){el.scrollIntoView()},0);return}
      if(vw&&vw.dataset.view==='sheet'){setView(cur==='quick'?'quick':'sheet');if(!el.offsetParent){setView('sheet')}
        setTimeout(function(){el.scrollIntoView()},0);return}
    }
    var saved=store.get('saa2.view','learn'); if(!TAB_OF[saved]){saved='learn'}
    setView(saved); if(saved==='learn'){showLearnHome()}
  }
  $$('.tab, .seg a').forEach(function(t){t.addEventListener('click',function(e){
    var target=t.getAttribute('href'); if(location.hash===target){e.preventDefault();route();window.scrollTo({top:0})}})});
  window.addEventListener('hashchange',route);

  body.classList.toggle('hints-on',hintsOn); hb.setAttribute('aria-pressed',hintsOn?'true':'false');
  renderLearned(); renderLessons(); qstats(); renderStart(); route();

  if('serviceWorker' in navigator&&(location.protocol==='https:'||location.hostname==='localhost'||location.hostname==='127.0.0.1')){
    window.addEventListener('load',function(){navigator.serviceWorker.register('sw.js').catch(function(){})});
    navigator.serviceWorker.ready.then(function(){$('#offline-ok').hidden=false}).catch(function(){});
  }

  /* встановлення як застосунок */
  (function(){
    var standalone=(window.matchMedia&&matchMedia('(display-mode: standalone)').matches)||navigator.standalone===true;
    if(standalone){return}
    var card=$('#install-card'), btn=$('#btn-install'), deferred=null;
    if(/iphone|ipad|ipod/i.test(navigator.userAgent)){card.hidden=false;$('#install-ios').hidden=false}
    window.addEventListener('beforeinstallprompt',function(e){e.preventDefault();deferred=e;card.hidden=false;btn.hidden=false});
    btn.addEventListener('click',function(){if(!deferred){return}deferred.prompt();
      deferred.userChoice.then(function(){deferred=null;card.hidden=true},function(){deferred=null})});
    window.addEventListener('appinstalled',function(){card.hidden=true});
  })();
})();
"""

# ---------- Шаблон сторінки ----------

PAGE = """<!DOCTYPE html>
<html lang="uk">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>%%TITLE%%</title>
<meta name="description" content="Курс і шпаргалка до іспиту AWS Certified Solutions Architect – Associate (SAA-C03) українською: уроки з образами, тригери, схеми, довідник сервісів, квіз і практичний тест.">
<meta name="theme-color" content="#4f46e5">
%%HEAD_EXTRA%%
<style>%%CSS%%</style>
</head>
<body class="%%BODY_CLASS%%" data-view="learn">
<a class="skip" href="#main">До змісту</a>
<header class="topbar">
  <div class="topbar-inner">
    <button class="tb-btn icon sheet-only" id="btn-toc" type="button" aria-label="Зміст" title="Зміст">☰</button>
    <a class="brand" href="#learn">SAA-C03 <span class="brand-sub">курс і шпаргалка</span></a>
    <label class="search sheet-only"><span aria-hidden="true">🔍</span><input id="q" type="search" placeholder="Пошук: NAT, Glacier, RPO…" autocomplete="off" aria-label="Пошук у шпаргалці"></label>
    <div class="actions">
      <button class="tb-btn hide-only" id="btn-hide" type="button" aria-pressed="false" title="Розмити відповіді в тригерах для самоперевірки">🙈<span class="lbl"> Сховати відповіді</span></button>
      <button class="tb-btn" id="btn-hints" type="button" aria-pressed="true" title="Підказки: торкнись або виділи назву сервісу, щоб побачити пояснення">🤖<span class="lbl"> Підказки</span></button>
      <details class="dl"><summary class="tb-btn" title="Завантажити PDF">⬇<span class="lbl"> PDF</span></summary>
        <div class="dl-menu"><a href="%%PDF_LESSONS%%" download>🎓 Курс: усі уроки (PDF)</a><a href="%%PDF_FULL%%" download>📘 Повна шпаргалка (PDF)</a><a href="%%PDF_QUICK%%" download>⚡ Швидке повторення (PDF)</a><a href="%%PDF_TEST%%" download>📝 Практичний тест (PDF)</a></div></details>
      <button class="tb-btn icon" id="btn-theme" type="button" aria-label="Світла або темна тема" title="Світла / темна тема">🌓</button>
    </div>
  </div>
  <nav class="tabs" aria-label="Розділи сайту">
    <a class="tab" href="#learn" data-tab="learn"><span class="ti">🎓</span><span>Навчання</span></a>
    <a class="tab" href="#sheet" data-tab="sheet"><span class="ti">📘</span><span>Шпаргалка</span></a>
    <a class="tab" href="#quiz" data-tab="practice"><span class="ti">🎯</span><span>Практика</span></a>
    <a class="tab" href="#diagrams" data-tab="diagrams"><span class="ti">🗺️</span><span>Схеми</span></a>
    <a class="tab" href="#services" data-tab="services"><span class="ti">📚</span><span>Сервіси</span></a>
  </nav>
  <div class="search-info sheet-only" id="search-info" aria-live="polite"></div>
</header>
<div class="scrim" id="scrim"></div>

<div class="view" id="view-learn" data-view="learn">
  <main class="page" id="main">
%%PRINT_LESSONS%%
%%LEARN_HOME%%
%%LESSONS%%
  </main>
</div>

<div class="view" id="view-sheet" data-view="sheet" hidden>
<div class="layout">
  <nav class="toc" aria-label="Зміст шпаргалки">
    <div class="toc-head"><strong>Зміст</strong><span id="progress"></span></div>
    <div class="bar"><span id="progress-bar"></span></div>
    <ol>%%TOC%%</ol>
  </nav>
  <main>
    <nav class="seg" aria-label="Режим шпаргалки"><a href="#sheet" data-v="sheet">📘 Повна</a><a href="#quick" data-v="quick">⚡ Швидко</a></nav>
%%SHEET_HERO%%
    <nav class="print-toc" aria-hidden="true"><h2>Зміст</h2><ol>%%TOC%%</ol></nav>
%%SECTIONS%%
    <footer class="foot">Оновлено 29.09.2026 · незалежний навчальний матеріал, не пов'язаний з AWS · джерела — в останньому розділі</footer>
  </main>
</div>
</div>

<div class="view" id="view-practice" data-view="practice" hidden>
  <main class="page">
    <nav class="seg" aria-label="Режим практики"><a href="#quiz" data-v="quiz">🎲 Квіз</a><a href="#test" data-v="test">📝 Тест</a></nav>
    <div id="practice-quiz">
      <h1>🎲 Квіз: тригери</h1>
      <p class="sub">Випадкові тригери зі шпаргалки. Спершу відповідай подумки, потім відкривай відповідь. Те, що «не знав», повертається частіше.</p>
      <section class="card">
        <div class="qz-row"><select id="qz-scope" aria-label="Розділ"><option value="all">Усі розділи</option></select>
          <label class="chk"><input type="checkbox" id="qz-weak"> Лише слабкі</label></div>
        <div class="qz-sec" id="qz-sec"></div>
        <div class="qz-q" id="qz-q"></div>
        <div class="qz-a" id="qz-a" hidden></div>
        <div class="qz-actions">
          <button class="tb-btn primary" id="qz-show" type="button">Показати відповідь</button>
          <button class="tb-btn ok" id="qz-know" type="button" hidden>✓ Знав</button>
          <button class="tb-btn bad" id="qz-dont" type="button" hidden>✗ Не знав</button>
        </div>
        <div class="qz-stats" id="qz-stats"></div>
      </section>
      <p class="qz-hint"><kbd>Клавіші: пробіл — показати, → знав, ← не знав.</kbd> <button class="linkbtn" id="qz-reset" type="button">Скинути статистику квізу</button></p>
    </div>
    <div id="practice-test" hidden>
      <h1>📝 Практичний тест</h1>
      <p class="sub">%%NQ%% оригінальних питань у стилі SAA-C03 (не реальні питання іспиту). Питання англійською, як на іспиті, з перекладом і поясненнями українською.</p>
      <section class="card" id="t-start">
        <h2>Новий тест</h2>
        <div class="opt-group">
          <label class="radio"><input type="radio" name="t-mode" value="practice" checked><span><b>Тренування</b> — відповідь і пояснення одразу після кожного питання</span></label>
          <label class="radio"><input type="radio" name="t-mode" value="exam"><span><b>Іспит</b> — таймер (2 хв на питання), результат і пояснення в кінці</span></label>
        </div>
        <div class="row"><label>Набір: <select id="t-set"></select></label></div>
        <div class="row"><label><input type="checkbox" id="t-shuffle" checked> Перемішати питання</label>
          <label><input type="checkbox" id="t-esl"> +30 хв (ESL) у режимі «Іспит»</label></div>
        <div class="row"><button class="tb-btn primary" id="t-begin" type="button">Почати</button>
          <button class="tb-btn" id="t-resume" type="button" hidden>▶ Продовжити</button></div>
        <p class="t-note" id="t-msg"></p>
        <div id="t-history"></div>
      </section>
      <section class="card" id="t-run" hidden>
        <div class="t-head"><span class="t-pos" id="t-pos"></span><span class="chip" id="t-dom"></span>
          <button class="tb-btn icon" id="t-flag" type="button" aria-pressed="false" title="Позначити, щоб повернутися">🚩</button>
          <span class="t-timer" id="t-timer"></span></div>
        <div class="t-stem" id="t-stem"></div>
        <button class="linkbtn" id="t-lang" type="button">🇺🇦 Показати переклад</button>
        <div class="t-alt" id="t-alt" hidden></div>
        <div class="t-note" id="t-note"></div>
        <div class="t-opts" id="t-opts"></div>
        <div class="t-why" id="t-why" hidden></div>
        <div class="t-actions">
          <button class="tb-btn" id="t-prev" type="button">← Назад</button>
          <button class="tb-btn primary" id="t-check" type="button">Перевірити</button>
          <button class="tb-btn primary" id="t-next" type="button">Далі →</button>
          <span class="spacer"></span>
          <button class="tb-btn" id="t-finish" type="button">Завершити</button>
        </div>
        <div class="t-nav" id="t-nav" hidden></div>
      </section>
      <section class="card" id="t-result" hidden>
        <h2>Результат</h2>
        <div class="t-score" id="t-score"></div>
        <div class="t-bar"><span id="t-bar"></span></div>
        <p id="t-verdict"></p>
        <div id="t-domains"></div>
        <div class="row">
          <button class="tb-btn" id="t-review-wrong" type="button">Розібрати помилки</button>
          <button class="tb-btn" id="t-review-all" type="button">Усі відповіді</button>
          <button class="tb-btn" id="t-retry" type="button">Пройти «Мої помилки»</button>
          <button class="tb-btn primary" id="t-new" type="button">Новий тест</button>
        </div>
        <div id="t-review"></div>
      </section>
    </div>
  </main>
</div>

<div class="view" id="view-diagrams" data-view="diagrams" hidden>
  <main class="page">
    <h1>🗺️ Схеми</h1>
    <p class="sub">Типові архітектури й образи з уроків. Торкнись назви сервісу на схемі — з'явиться пояснення. Під кожною схемою — посилання на урок чи розділ.</p>
    <div id="dg-gallery"></div>
  </main>
</div>

<div class="view" id="view-services" data-view="services" hidden>
  <main class="page">
    <h1>📚 Сервіси AWS</h1>
    <p class="sub">Довідник сервісів і понять з іспиту: що це, образ, коли обирати, як питають на іспиті і з чим не плутати. Торкнись картки.</p>
    <label class="search wide"><span aria-hidden="true">🔍</span><input id="svc-q" type="search" placeholder="Назва або задача: черга, кеш, DDoS, архів…" autocomplete="off" aria-label="Пошук сервісу"></label>
    <div class="cat-chips" id="svc-cats"></div>
    <p class="muted" id="svc-count"></p>
    <div class="svc-grid" id="svc-grid"></div>
  </main>
</div>

<div class="svc-overlay" id="svc-overlay" hidden>
  <div class="svc-card" role="dialog" aria-modal="true" aria-labelledby="svc-title">
    <div class="svc-head"><span class="svc-emoji" id="svc-emoji"></span>
      <div><h2 id="svc-title"></h2><span class="chip" id="svc-cat"></span></div>
      <button class="tb-btn icon x" id="svc-close" type="button" aria-label="Закрити">✕</button></div>
    <p class="svc-what" id="svc-what"></p>
    <div class="svc-image" id="svc-image"></div>
    <h4 id="svc-when-h">✅ Коли обирати</h4><ul class="svc-when" id="svc-when"></ul>
    <h4 id="svc-exam-h" class="trg-h">🎯 На іспиті</h4><ul class="svc-exam" id="svc-exam"></ul>
    <div class="svc-confuse" id="svc-confuse"></div>
    <div class="svc-links" id="svc-links"></div>
  </div>
</div>
<div class="ask-overlay" id="ask" hidden><div class="ask-card" role="alertdialog" aria-modal="true" aria-labelledby="ask-text">
  <p id="ask-text"></p><div class="ask-actions"><button class="tb-btn" id="ask-no" type="button">Скасувати</button>
  <button class="tb-btn primary" id="ask-yes" type="button">Так</button></div></div></div>
<button class="hint-chip" id="hint-chip" type="button" hidden></button>
<button class="to-top" id="to-top" type="button" aria-label="Нагору">↑</button>
<script id="qdata" type="application/json">%%QDATA%%</script>
<script id="sdata" type="application/json">%%SDATA%%</script>
<script id="ldata" type="application/json">%%LDATA%%</script>
<script id="cdata" type="application/json">%%CDATA%%</script>
<script>%%JS%%</script>
</body>
</html>
"""

DISCLAIMER = ("Незалежний навчальний курс. Не пов'язаний з Amazon Web Services і не схвалений AWS. "
              "AWS і назви сервісів — торговельні марки Amazon.com, Inc. або її афілійованих осіб. "
              "Практичні питання — оригінальні, це не реальні питання іспиту.")


def build_sheet(sections, quick=False):
    toc, body = [], []
    first_quick_done = False
    for s in sections:
        keep = s["quick"] or s["trg"] or s["warn"]
        classes = ["quick-keep"] if s["quick"] else ([] if keep else ["no-quick"])
        if quick and keep and not first_quick_done:
            classes.append("first-quick")
            first_quick_done = True
        li_cls = ' class="no-quick"' if not keep else ""
        toc.append(f'<li{li_cls}><a href="#{s["id"]}" data-sec="{s["id"]}"><span class="n">{s["num"]}</span>'
                   f'<span>{inline(s["title"])}</span></a></li>')
        cls_attr = f' class="{" ".join(classes)}"' if classes else ""
        num = f'<span class="num">{s["num"]}</span>' if s["num"] else ""
        learn = (f'<button class="learn-btn" data-sec="{s["id"]}" type="button" aria-pressed="false">☐ Вивчено</button>'
                 if s["num"] else "")
        body.append(
            f'<section id="{s["id"]}"{cls_attr} data-title="{html.escape(s["title"], quote=True)}">'
            f'<div class="sec-head"><h2>{num}<span class="t">{inline(s["title"])}</span></h2>{learn}</div>'
            + "".join(s["content"]) + "</section>")
    return "".join(toc), "\n".join(body)


def build_learn(lessons, sec_by_num):
    modules, cards = [], {}
    for i, l in enumerate(lessons, 1):
        if l["module"] not in cards:
            modules.append(l["module"])
            cards[l["module"]] = []
        cards[l["module"]].append(
            f'<a class="lesson-card" href="#learn/{l["id"]}" data-id="{l["id"]}"><span class="le">{l["emoji"]}</span>'
            f'<span><span class="ln">Урок {i} · ⏱ {l["minutes"]} хв</span><span class="lt">{inline(l["title"])}</span></span></a>')
    mods = "".join(f'<section class="module"><h2>Модуль {k} · {html.escape(m)}</h2><div class="lesson-grid">{"".join(cards[m])}</div></section>'
                   for k, m in enumerate(modules, 1))
    n_trg = sum(l["trg"] for l in lessons)
    home = (f'<div id="learn-home"><header class="hero"><h1>🎓 AWS з нуля до SAA-C03</h1>'
            f'<p class="sub">{plural(len(lessons), "короткий урок", "короткі уроки", "коротких уроків")} з образами, які легко уявити й запам\'ятати. Кожен урок — 5–8 хвилин: '
            f'образ → пояснення → «запам\'ятай» → як питають на іспиті → не плутай. Після уроку — шпаргалка і квіз по темі.</p>'
            f'<div class="progress-card"><div class="bar"><span id="learn-bar"></span></div><p id="learn-progress-text"></p>'
            f'<a class="tb-btn primary" id="learn-continue" href="#learn/{lessons[0]["id"]}">▶ Почати</a></div>'
            f'<div class="stats" id="learn-summary"></div>'
            f'<div class="install-card" id="install-card" hidden><span>📲 <b>Встанови як застосунок</b> — відкриватиметься з головного екрана '
            f'і працюватиме без інтернету.</span><button class="tb-btn primary" id="btn-install" type="button" hidden>Встановити</button>'
            f'<span class="muted" id="install-ios" hidden>iPhone: Safari → «Поділитися» → «На початковий екран».</span></div>'
            f'<p class="offline-ok" id="offline-ok" hidden>✓ Курс збережено на цьому пристрої — відкривається і без інтернету.</p>'
            f'<p class="how">🤖 <b>Підказки:</b> торкнись підкресленої назви сервісу або виділи її пальцем — з\'явиться пояснення з образом '
            f'і тригерами для іспиту. Вимикаються кнопкою 🤖 угорі. Повний довідник — вкладка 📚 «Сервіси».</p></header>'
            f'{mods}<p class="disclaimer">{DISCLAIMER}</p></div>')
    arts = []
    for i, l in enumerate(lessons):
        prev_l = lessons[i - 1] if i > 0 else None
        next_l = lessons[i + 1] if i + 1 < len(lessons) else None
        sheet_links = " · ".join(f'<a href="#{sec_by_num[n]["id"]}">{n}. {inline(sec_by_num[n]["title"])}</a>' for n in l["sheet"])
        quiz_links = " · ".join(f'<a href="#quiz" data-quiz-scope="{sec_by_num[n]["id"]}">квіз по розділу {n}</a>'
                                for n in l["sheet"] if sec_by_num[n]["trg"])
        links = f'<div class="lesson-links"><div>📘 У шпаргалці: {sheet_links}</div>'
        links += (f'<div class="quiz-links">🎲 Закріпити: {quiz_links}</div></div>' if quiz_links else "</div>")
        nav = '<div class="lesson-nav">'
        nav += f'<a class="tb-btn" href="#learn/{prev_l["id"]}">← Назад</a>' if prev_l else '<a class="tb-btn" href="#learn">← Усі уроки</a>'
        nav += f'<button class="tb-btn done-btn" data-id="{l["id"]}" type="button" aria-pressed="false">☐ Позначити пройденим</button>'
        nav += (f'<a class="tb-btn primary" href="#learn/{next_l["id"]}">Далі: {next_l["emoji"]} →</a>' if next_l
                else '<a class="tb-btn primary" href="#test">📝 До тесту →</a>')
        nav += "</div>"
        arts.append(
            f'<article class="lesson card" id="lesson-{l["id"]}" data-id="{l["id"]}" data-title="{html.escape(l["title"], quote=True)}" hidden>'
            f'<div class="lesson-top"><a class="back" href="#learn">← Усі уроки</a>'
            f'<span class="meta">{html.escape(l["module"])} · урок {i + 1} з {len(lessons)} · ⏱ {l["minutes"]} хв</span></div>'
            f'<h1><span class="le">{l["emoji"]}</span><span>{inline(l["title"])}</span></h1>{l["html"]}{links}{nav}</article>')
    lessons_toc = "".join(f'<li><a href="#lesson-{l["id"]}"><span class="n">{i}</span><span>{l["emoji"]} {inline(l["title"])}</span></a></li>'
                          for i, l in enumerate(lessons, 1))
    print_block = (f'<div class="print-lessons-only"><header class="hero"><h1>🎓 AWS з нуля до SAA-C03 — підручник</h1>'
                   f'<p class="sub">{plural(len(lessons), "урок", "уроки", "уроків")} з образами, «запам\'ятай», тригерами іспиту і пастками. '
                   f'Інтерактивна версія з підказками, квізом і тестом — на сайті.</p><p class="sub">{DISCLAIMER}</p></header>'
                   f'<nav class="print-toc"><h2>Уроки</h2><ol>{lessons_toc}</ol></nav></div>')
    return home, "\n".join(arts), print_block, n_trg


def build_page(ctx, pdf_links, head_extra, variant="site"):
    quick = variant == "quick"
    toc, body = build_sheet(ctx["sections"], quick)
    n_trg = sum(s["trg"] for s in ctx["sections"])
    n_sec = sum(1 for s in ctx["sections"] if s["num"])
    if quick:
        sheet_hero = (f'<header class="hero"><h1>SAA-C03: швидке повторення</h1>'
                      f'<p class="sub">Лише тригери «бачиш у питанні → відповідь», пастки, порівняння «X чи Y», цифри і тактика. '
                      f'Повна версія — на сайті та в PDF «Повна шпаргалка». Перевірено станом на вересень 2026.</p>'
                      f'<div class="chips"><span>{plural(n_trg, "тригер", "тригери", "тригерів")}</span><span>65 питань · 130 хв</span>'
                      f'<span>прохідний 720 / 1000</span></div></header>')
    else:
        sheet_hero = (f'<header class="hero"><h1>{inline(ctx["title"])}</h1>'
                      f'<p class="sub">Стисла версія курсу: короткі факти → 🎯 тригери «бачиш у питанні → відповідь» → ⚠️ пастки. '
                      f'Перевірено за офіційним гайдом і документацією AWS станом на вересень 2026.</p>'
                      f'<div class="chips"><span>{plural(n_sec, "розділ", "розділи", "розділів")}</span><span>{plural(n_trg, "тригер", "тригери", "тригерів")}</span>'
                      f'<span>іспит: 65 питань · 130 хв · 720 / 1000</span></div>'
                      f'<p class="how">Прочитай розділ → увімкни <b>🙈 Сховати відповіді</b> і перевір себе → квіз по розділу. '
                      f'Перед іспитом — режим <b>⚡ Швидко</b>. План на 14 днів — у розділі 29.</p>'
                      f'<p class="progress-line" id="hero-progress"></p></header>')
    body_class = {"quick": "only-trg print-quick", "lessons": "print-lessons"}.get(variant, "")
    ldata = [{"id": l["id"], "title": l["title"], "emoji": l["emoji"], "module": l["module"]} for l in ctx["lessons"]]
    page = PAGE
    for key, val in {
        "%%TITLE%%": "AWS SAA-C03 — курс і шпаргалка",
        "%%BODY_CLASS%%": body_class,
        "%%HEAD_EXTRA%%": head_extra,
        "%%PRINT_LESSONS%%": ctx["print_lessons"],
        "%%LEARN_HOME%%": ctx["learn_home"],
        "%%LESSONS%%": ctx["lesson_html"],
        "%%SHEET_HERO%%": sheet_hero,
        "%%TOC%%": toc,
        "%%SECTIONS%%": body,
        "%%NQ%%": str(len(ctx["questions"])),
        "%%PDF_LESSONS%%": pdf_links["lessons"],
        "%%PDF_FULL%%": pdf_links["full"],
        "%%PDF_QUICK%%": pdf_links["quick"],
        "%%PDF_TEST%%": pdf_links["test"],
        "%%QDATA%%": json.dumps(ctx["questions"], ensure_ascii=False).replace("</", "<\\/"),
        "%%SDATA%%": json.dumps(ctx["services"], ensure_ascii=False).replace("</", "<\\/"),
        "%%LDATA%%": json.dumps(ldata, ensure_ascii=False).replace("</", "<\\/"),
        "%%CDATA%%": json.dumps(CATS, ensure_ascii=False),
        "%%CSS%%": CSS,
        "%%JS%%": JS,
    }.items():
        page = page.replace(key, val)
    return page


def build_test_print(questions):
    letters = "ABCDEF"
    qs_html, ans_html = [], []
    for i, q in enumerate(questions, 1):
        multi = f" <b>(Оберіть {len(q['correct'])})</b>" if q["multi"] else ""
        opts = "".join(f"<li>{o}</li>" for o in q["options"])
        qs_html.append(f'<div class="pq"><div class="pq-h">{i}. {DOMAINS[q["domain"]]}</div>'
                       f'<div class="pq-en">{q["en"]}{multi}</div><div class="pq-ua">{q["ua"]}</div>'
                       f'<ol type="A">{opts}</ol></div>')
        right = ", ".join(letters[k] for k in q["correct"])
        ans_html.append(f'<div class="pa"><b>{i} — {right}.</b> {q["why"]}</div>')
    body = (f'<main><header class="hero"><h1>SAA-C03: практичний тест ({len(questions)} питань)</h1>'
            f'<p class="sub">Оригінальні питання у стилі іспиту (не реальні питання AWS). Спершу дай відповіді на всі, '
            f'потім звір із розділом «Відповіді і пояснення». Орієнтир: 80%+ — готовий до іспиту. '
            f'Інтерактивна версія з таймером — на сайті, вкладка «Практика».</p></header>'
            f'<section><div class="sec-head"><h2>Питання</h2></div>{"".join(qs_html)}</section>'
            f'<section><div class="sec-head"><h2>Відповіді і пояснення</h2></div>{"".join(ans_html)}</section></main>')
    return (f'<!DOCTYPE html><html lang="uk"><head><meta charset="utf-8"><title>SAA-C03 — практичний тест</title>'
            f'<style>{CSS}</style></head><body>{body}</body></html>')


# ---------- PWA ----------

ICON_HTML = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
html,body{{margin:0;width:{w}px;height:{w}px;overflow:hidden}}
body{{background:linear-gradient(135deg,#7c3aed 0%,#1f6feb 100%);display:flex;align-items:center;justify-content:center;font-family:"Segoe UI",Arial,sans-serif;color:#fff}}
.t{{text-align:center}}
.a{{font-size:{a}px;font-weight:800;line-height:1;letter-spacing:{ls}px}}
.c{{width:{cw}px;height:{ch}px;border-radius:{ch}px;background:#22d3ee;margin:{m1}px auto 0}}
.b{{font-size:{b}px;font-weight:700;line-height:1;margin-top:{m2}px;opacity:.95}}
</style></head><body><div class="t"><div class="a">SAA</div><div class="c"></div><div class="b">C03</div></div></body></html>"""

MANIFEST = {
    "name": "AWS SAA-C03 — курс і шпаргалка",
    "short_name": "SAA-C03",
    "description": "Курс, шпаргалка, довідник сервісів, квіз і практичний тест до AWS Solutions Architect – Associate (SAA-C03) українською",
    "lang": "uk",
    "id": "./",
    "start_url": "./",
    "scope": "./",
    "display": "standalone",
    "background_color": "#0f1115",
    "theme_color": "#4f46e5",
    "icons": [
        {"src": "icons/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
        {"src": "icons/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
        {"src": "icons/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
    ],
}

SW = """// Офлайн-режим: сторінка — спершу з мережі (щоб бачити оновлення), без мережі — з кешу.
const PREFIX = 'saa2-';
const CACHE = PREFIX + '%s';
const CORE = ['./', './index.html', './manifest.webmanifest', './icons/icon-192.png', './icons/icon-512.png'];
self.addEventListener('install', e => {
  // кожен файл окремо: якщо одного бракує, офлайн-режим однаково встановиться
  e.waitUntil(caches.open(CACHE).then(c => Promise.all(CORE.map(u => c.add(u).catch(() => null))))
    .then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys()
    .then(keys => Promise.all(keys.filter(k => k.startsWith(PREFIX) && k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET' || new URL(req.url).origin !== location.origin) return;
  if (req.mode === 'navigate') {
    e.respondWith(fetch(req).then(res => {
      const copy = res.clone();
      caches.open(CACHE).then(c => c.put('./index.html', copy));
      return res;
    }).catch(() => caches.match('./index.html')));
    return;
  }
  e.respondWith(caches.match(req).then(hit => hit || fetch(req).then(res => {
    if (res.ok) { const copy = res.clone(); caches.open(CACHE).then(c => c.put(req, copy)); }
    return res;
  })));
});
"""


def browser_path():
    return next((b for b in BROWSERS if pathlib.Path(b).exists()), None)


def run_browser(args, timeout=240):
    browser = browser_path()
    if not browser:
        raise RuntimeError("Chrome/Edge не знайдено")
    work = pathlib.Path(tempfile.mkdtemp(prefix="saa_"))
    try:
        cmd = [browser, "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
               f"--user-data-dir={work / 'profile'}"] + args(work)
        subprocess.run(cmd, check=True, timeout=timeout, capture_output=True)
        return work
    except Exception:
        shutil.rmtree(work, ignore_errors=True)
        raise


def print_pdf(url, pdf_paths):
    work = run_browser(lambda w: ["--no-pdf-header-footer", "--generate-pdf-document-outline",
                                  "--virtual-time-budget=15000", f"--print-to-pdf={w / 'out.pdf'}", url])
    try:
        for p in pdf_paths:
            p.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(work / "out.pdf", p)
    finally:
        shutil.rmtree(work, ignore_errors=True)


def render_icon(size, out_path):
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="saa_icon_"))
    try:
        page = tmp / "icon.html"
        k = size / 512
        page.write_text(ICON_HTML.format(w=size, a=round(150 * k), ls=round(-2 * k, 1), cw=round(230 * k),
                                         ch=max(2, round(10 * k)), m1=round(18 * k), b=round(78 * k),
                                         m2=round(14 * k)), encoding="utf-8")
        work = run_browser(lambda w: ["--hide-scrollbars", f"--window-size={size},{size}",
                                      f"--screenshot={w / 'shot.png'}", page.as_uri()])
        out_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(work / "shot.png", out_path)
        shutil.rmtree(work, ignore_errors=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def write_repo_files():
    gi = ROOT / ".gitignore"
    if not gi.exists():
        gi.write_text("# Локальні копії і план продажу не публікуються\n/*.html\n/*.pdf\n/*.url\n__pycache__/\n",
                      encoding="utf-8")


def main():
    parts = sorted((SRC / "sheet").glob("[0-9][0-9]_*.md"))
    title, sections = render("\n\n".join(p.read_text(encoding="utf-8") for p in parts), split_h2=True)
    sec_by_num = {int(s["num"]): s for s in sections if s["num"]}
    lessons = parse_lessons(set(sec_by_num))
    services = parse_services({l["id"] for l in lessons})
    questions = parse_questions(SRC / "questions.md")
    learn_home, lesson_html, print_lessons, n_ltrg = build_learn(lessons, sec_by_num)
    ctx = {"title": title, "sections": sections, "lessons": lessons, "services": services, "questions": questions,
           "learn_home": learn_home, "lesson_html": lesson_html, "print_lessons": print_lessons}

    web_pdf = {k: v[0] for k, v in PDFS.items()}
    local_pdf = {k: urllib.parse.quote(v[1]) for k, v in PDFS.items()}
    head_web = ('<meta name="robots" content="noindex, nofollow">\n'
                '<link rel="manifest" href="manifest.webmanifest">\n'
                '<link rel="icon" type="image/png" href="icons/icon-192.png">\n'
                '<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">\n'
                '<meta name="mobile-web-app-capable" content="yes">\n'
                '<meta name="apple-mobile-web-app-capable" content="yes">\n'
                '<meta name="apple-mobile-web-app-title" content="SAA-C03">')
    head_local = '<link rel="icon" type="image/png" href="docs/icons/icon-192.png">'

    site_html = build_page(ctx, web_pdf, head_web)
    local_html = build_page(ctx, local_pdf, head_local)
    DOCS.mkdir(exist_ok=True)
    (DOCS / "index.html").write_text(site_html, encoding="utf-8")
    (ROOT / LOCAL_HTML).write_text(local_html, encoding="utf-8")
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")
    (DOCS / "manifest.webmanifest").write_text(json.dumps(MANIFEST, ensure_ascii=False, indent=2), encoding="utf-8")
    version = hashlib.sha1(site_html.encode("utf-8")).hexdigest()[:10]
    (DOCS / "sw.js").write_text(SW % version, encoding="utf-8")
    write_repo_files()
    n_fig = sum(s["figs"] for s in sections) + sum(l["figs"] for l in lessons)
    print(f"Сайт: docs/index.html — уроків {len(lessons)}, розділів {len(sec_by_num)}, "
          f"тригерів {sum(s['trg'] for s in sections)} (+{n_ltrg} в уроках), схем {n_fig}, "
          f"сервісів {len(services)}, питань {len(questions)}, {len(site_html) // 1024} KB, версія {version}")

    if "--no-pdf" in sys.argv:
        return
    for size, name in ((192, "icon-192.png"), (512, "icon-512.png"), (180, "apple-touch-icon.png")):
        render_icon(size, DOCS / "icons" / name)
    print("Іконки: docs/icons/")
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="saa_build_"))
    try:
        variants = [("lessons", build_page(ctx, local_pdf, "", "lessons")),
                    ("full", local_html),
                    ("quick", build_page(ctx, local_pdf, "", "quick")),
                    ("test", build_test_print(questions))]
        for key, page in variants:
            path = tmp / f"{key}.html"
            path.write_text(page, encoding="utf-8")
            print_pdf(path.as_uri(), [DOCS / PDFS[key][0], ROOT / PDFS[key][1]])
            print(f"PDF: {PDFS[key][1]}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
