# -*- coding: utf-8 -*-
"""Збирає окремий сайт «AWS SAA-C03 з нуля — глибоке навчання» (docs/deep/).

Джерела:
  chapters/NN_id.md   — розділи підручника (front matter --- … --- і Markdown)
  glossary.md         — основи IT для підказок (формат як у ../_source/services.md)
  ../_source/services.md  — довідник сервісів AWS (спільний з версією 2)
  ../_source/questions.md, exam2.md — пробний іспит (англійською з перекладом)
Результат:
  ../docs/deep/       — сайт (index.html, офлайн-режим, іконки, pdf/)
  ../AWS_SAA-C03_з_нуля*.html/pdf — локальні копії (не публікуються)
Запуск:  python build.py            (усе)
         python build.py --no-pdf   (лише HTML)
"""
import hashlib
import html
import json
import os
import pathlib
import random
import re
import shutil
import subprocess
import sys
import tempfile

sys.stdout.reconfigure(encoding="utf-8")

SRC = pathlib.Path(__file__).resolve().parent
ROOT = SRC.parent
V2 = ROOT / "_source"
OUT = ROOT / "docs" / "deep"
SITE_URL = "https://nexgen-fullstack.github.io/AWSSAAC03/deep/"
PDF_WEB = "pdf/saa-c03-z-nulia-pidruchnyk.pdf"
PDF_LOCAL = "AWS_SAA-C03_з_нуля_підручник.pdf"
HTML_LOCAL = "AWS_SAA-C03_з_нуля.html"
UPDATED = "30.09.2026"

DOMAINS = {"secure": "Безпека", "resilient": "Відмовостійкість",
           "performance": "Продуктивність", "cost": "Вартість"}
DOMAIN_PCT = {"secure": 30, "resilient": 26, "performance": 24, "cost": 20}
CATS = {"it": "Основи IT", "concept": "Поняття", "compute": "Обчислення", "serverless": "Serverless",
        "containers": "Контейнери", "storage": "Сховище", "database": "Бази даних", "network": "Мережа",
        "security": "Безпека", "integration": "Інтеграція", "analytics": "Аналітика", "ml": "ML / AI",
        "management": "Керування", "cost": "Вартість", "migration": "Міграція", "frontend": "Веб і мобільні"}
BROWSERS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "/opt/pw-browsers/chromium",
    "/usr/bin/chromium", "/usr/bin/chromium-browser", "/usr/bin/google-chrome",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
]
LETTERS = "ABCDEFGH"


# ---------- Markdown → HTML ----------

def inline(text):
    t = html.escape(text.replace("\\*", "\x01"), quote=False)
    codes = []

    def keep_code(m):
        codes.append(m.group(1))
        return f"\x00{len(codes) - 1}\x00"

    t = re.sub(r"`([^`]+)`", keep_code, t)
    t = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)",
               lambda m: f'<a href="{m.group(2)}" target="_blank" rel="noopener">{m.group(1)}</a>', t)
    t = re.sub(r"\[([^\]]+)\]\((#[\w/.@-]+)\)", lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>', t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![*\w])\*(?![\s*])(.+?)(?<![\s*])\*(?![*\w])", r"<em>\1</em>", t)
    t = re.sub(r"\x00(\d+)\x00", lambda m: f"<code>{codes[int(m.group(1))]}</code>", t)
    return t.replace("\x01", "*")


def plural(n, one, few, many):
    if n % 10 == 1 and n % 100 != 11:
        return f"{n} {one}"
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return f"{n} {few}"
    return f"{n} {many}"


def short_id(text):
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:8]


def split_trigger(text):
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


class Ctx:
    """Стан рендеру одного розділу."""

    def __init__(self, cid):
        self.cid = cid
        self.toc = []        # (anchor, title)
        self.figs = 0
        self.qn = 0
        self.trg = 0
        self.labs = 0
        self.anchors = set()

    def anchor(self, text, custom=None):
        a = custom or f"s{len(self.toc) + 1}"
        if a in self.anchors:
            raise ValueError(f"{self.cid}: повторюється якір {a}")
        self.anchors.add(a)
        return a


BOX_KINDS = {"lab", "deep", "note", "calc", "mnemo", "example", "story", "summary"}


def shuffled_order(n, key):
    """Детермінований порядок варіантів: однаковий між збірками, але правильні відповіді не збираються на A/B."""
    return random.Random("saa-deep:" + key).sample(range(n), n)


def render_quiz(lines, ctx):
    qs, cur, last = [], None, None
    for raw in lines:
        s = raw.strip()
        if not s:
            continue
        if s.startswith("? "):
            cur = {"q": s[2:].strip(), "opts": [], "ok": [], "why": ""}
            qs.append(cur)
            last = "q"
        elif cur is None:
            raise ValueError(f"{ctx.cid}: рядок квізу до питання: {s[:60]}")
        elif s[:2] in ("+ ", "- "):
            if s[0] == "+":
                cur["ok"].append(len(cur["opts"]))
            cur["opts"].append(s[2:].strip())
            last = "o"
        elif s.startswith("= "):
            cur["why"] = s[2:].strip()
            last = "w"
        else:  # продовження попереднього рядка
            if last == "q":
                cur["q"] += " " + s
            elif last == "o":
                cur["opts"][-1] += " " + s
            elif last == "w":
                cur["why"] += " " + s
    out = []
    for q in qs:
        ctx.qn += 1
        qid = f"{ctx.cid}-{ctx.qn}"
        if len(q["opts"]) < 3 or not q["ok"] or not q["why"]:
            raise ValueError(f"{qid}: неповне питання ({q['q'][:50]})")
        multi = len(q["ok"]) > 1
        order = shuffled_order(len(q["opts"]), qid)
        q["ok"] = sorted(order.index(i) for i in q["ok"])
        q["opts"] = [q["opts"][j] for j in order]
        opts = "".join(f'<button class="qz-o" type="button" data-i="{i}"><span class="t-letter">{LETTERS[i]}</span>'
                       f'<span class="qz-ot">{inline(o)}</span></button>' for i, o in enumerate(q["opts"]))
        note = f'<div class="qz-note">Оберіть {len(q["ok"])} відповіді</div>' if multi else ""
        right = ", ".join(LETTERS[i] for i in q["ok"])
        out.append(
            f'<div class="qz" id="q-{qid}" data-q="{qid}" data-c="{",".join(map(str, q["ok"]))}">'
            f'<div class="qz-h">Питання {ctx.qn}</div><div class="qz-q">{inline(q["q"])}</div>{note}'
            f'<div class="qz-opts">{opts}</div>'
            f'<div class="qz-act"><button class="tb-btn primary qz-check" type="button" hidden>Перевірити</button>'
            f'<button class="linkbtn qz-reset" type="button" hidden>↺ Спробувати ще раз</button></div>'
            f'<div class="qz-why" hidden><b class="qz-verdict"></b> <span class="qz-right">Правильна відповідь: {right}.</span> '
            f'{inline(q["why"])}</div></div>')
    return '<div class="qz-list">' + "".join(out) + "</div>"


def render(md, ctx, top=False):
    """Markdown → HTML. top=True: розділ ділиться на секції за заголовками ##."""
    lines = md.replace("\r\n", "\n").split("\n")
    out = []
    mode = None
    i, n = 0, len(lines)
    heading_re = re.compile(r"^(#{2,4})\s+(.*)$")
    block_start = re.compile(r"^(#{1,4}\s|\s*\||\s*>|\s*- |\d+\.\s|```|<|:::)")
    section_open = False
    if top:
        out.append('<div class="cs cs-intro">')
        section_open = True

    while i < n:
        line = lines[i]
        s = line.strip()
        if not s:
            i += 1
            continue
        m = re.match(r"^:::(\w+)\s*(.*)$", s)
        if m:
            kind, title = m.group(1), m.group(2).strip()
            depth, j, buf = 1, i + 1, []
            while j < n:
                t = lines[j].strip()
                if re.match(r"^:::\w+", t):
                    depth += 1
                elif t == ":::":
                    depth -= 1
                    if depth == 0:
                        break
                buf.append(lines[j])
                j += 1
            if depth != 0:
                raise ValueError(f"{ctx.cid}: не закритий блок :::{kind}")
            i = j + 1
            if kind == "quiz":
                out.append(render_quiz(buf, ctx))
            elif kind == "deep":
                out.append(f'<details class="box deep"><summary>{inline(title)}</summary>'
                           f'<div class="box-b">{render(chr(10).join(buf), ctx)}</div></details>')
            elif kind in BOX_KINDS:
                if kind == "lab":
                    ctx.labs += 1
                head = f'<div class="box-h">{inline(title)}</div>' if title else ""
                out.append(f'<div class="box {kind}">{head}<div class="box-b">{render(chr(10).join(buf), ctx)}</div></div>')
            else:
                raise ValueError(f"{ctx.cid}: невідомий блок :::{kind}")
            mode = None
            continue
        if s.startswith("```"):
            lang = s[3:].strip()
            i += 1
            buf = []
            while i < n and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            out.append(f'<pre class="code"><code class="lang-{html.escape(lang)}">{html.escape(chr(10).join(buf))}</code></pre>')
            continue
        if s.startswith("<"):
            buf = []
            while i < n and lines[i].strip():
                buf.append(lines[i])
                i += 1
            block = "\n".join(buf)

            def fig_id(mm):
                ctx.figs += 1
                return f'<figure class="diagram" id="{ctx.cid}--f{ctx.figs}"'
            block = re.sub(r'<figure class="diagram"(?![^>]*\sid=)', fig_id, block)
            out.append(block)
            continue
        m = heading_re.match(line)
        if m:
            level, text = len(m.group(1)), m.group(2).strip()
            mc = re.search(r"\s*\{#([\w-]+)\}\s*$", text)
            custom = mc.group(1) if mc else None
            if mc:
                text = text[:mc.start()].strip()
            if level == 2 and top:
                a = ctx.anchor(text, custom)
                ctx.toc.append((a, text))
                if section_open:
                    out.append("</div>")
                out.append(f'<div class="cs"><h2 class="ch-h2" id="{ctx.cid}--{a}">{inline(text)}</h2>')
                section_open = True
                mode = None
            elif level <= 3:
                idattr = f' id="{ctx.cid}--{ctx.anchor(text, custom)}"' if custom else ""
                tag = "h3" if level == 3 or not top else "h3"
                out.append(f"<{tag}{idattr}>{inline(text)}</{tag}>")
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
                out.append(f'<h4 class="{cls}">{inline(text)}</h4>' if cls else f"<h4>{inline(text)}</h4>")
            i += 1
            continue
        if s.startswith("|"):
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                rows.append(lines[i].strip())
                i += 1
            out.append(render_table(rows))
            continue
        if s.startswith(">"):
            buf = []
            while i < n and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip()[1:].strip())
                i += 1
            paras = [p for p in "\n".join(buf).split("\n\n") if p.strip()]
            txt = paras[0] if paras else ""
            kind = ("img" if txt.startswith("🖼") else "story" if txt.startswith("🎬") else "warn" if txt.startswith("⚠")
                    else "new" if txt.startswith("🆕") else "tip")
            inner = "".join(f"<p>{inline(' '.join(p.split()))}</p>" for p in paras)
            out.append(f'<div class="callout {kind}">{inner}</div>')
            continue
        if re.match(r"^\s*- ", line) or re.match(r"^\d+\.\s", s):
            ordered = bool(re.match(r"^\d+\.\s", s))
            pat = r"^\s*(\d+\.\s|- )" if ordered else r"^\s*- "
            items = []
            while i < n and re.match(pat, lines[i]):
                items.append(lines[i])
                i += 1
                # продовження пункту з відступом (без маркера)
                while i < n and lines[i].startswith("   ") and lines[i].strip() and not re.match(r"^\s*(\d+\.\s|- )", lines[i]):
                    items[-1] = items[-1].rstrip() + " " + lines[i].strip()
                    i += 1
            frag, n_trg = render_list(items, mode, ordered)
            ctx.trg += n_trg
            out.append(frag)
            continue
        buf = [s]
        i += 1
        while i < n and lines[i].strip() and not block_start.match(lines[i].strip()):
            buf.append(lines[i].strip())
            i += 1
        out.append(f"<p>{inline(' '.join(buf))}</p>")
    if top and section_open:
        out.append("</div>")
    return "".join(out)


# ---------- Джерела ----------

def parse_front(text, path):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        raise ValueError(f"{path.name}: немає front matter")
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            v = v.strip()
            if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
                v = v[1:-1]
            meta[k.strip()] = v
    return meta, text[m.end():]


def parse_chapters():
    chapters = []
    for f in sorted((SRC / "chapters").glob("[0-9][0-9]_*.md")):
        meta, body = parse_front(f.read_text(encoding="utf-8").replace("\r\n", "\n"), f)
        for key in ("id", "module", "title", "emoji"):
            if not meta.get(key):
                raise ValueError(f"{f.name}: немає поля {key}")
        ctx = Ctx(meta["id"])
        body_html = render(body, ctx, top=True)
        plain = re.sub(r"<[^>]+>", " ", body_html)
        words = len(re.findall(r"\w+", plain))
        minutes = int(meta.get("minutes") or max(5, round(words / 110 / 5) * 5))
        doms = [d.strip() for d in meta.get("domains", "").split(",") if d.strip()]
        for d in doms:
            if d not in DOMAINS:
                raise ValueError(f"{f.name}: невідомий домен {d}")
        chapters.append({
            "id": meta["id"], "module": meta["module"], "title": meta["title"], "emoji": meta["emoji"],
            "short": meta.get("short", meta["title"]), "minutes": minutes, "domains": doms,
            "svc": [x.strip() for x in meta.get("svc", "").split(",") if x.strip()],
            "html": body_html, "toc": ctx.toc, "figs": ctx.figs, "q": ctx.qn, "trg": ctx.trg,
            "labs": ctx.labs, "words": words, "plain": plain,
        })
    ids = [c["id"] for c in chapters]
    if len(set(ids)) != len(ids):
        raise ValueError("Повторюються id розділів")
    # перевірка внутрішніх посилань #ch/<id>[/<anchor>]
    html_of = {c["id"]: c["html"] for c in chapters}
    problems = []
    for c in chapters:
        for mm in re.finditer(r'href="#ch/([\w-]+)(?:/([\w.@-]+))?"', c["html"]):
            cid, a = mm.group(1), mm.group(2)
            if cid not in html_of:
                problems.append(f"{c['id']}: посилання на невідомий розділ {cid}")
            elif a and a != "@" and not re.match(r"^(q-[\w-]+|b\d+)$", a):
                if f'id="{cid}--{a}"' not in html_of[cid]:
                    problems.append(f"{c['id']}: посилання на невідомий якір {cid}/{a}")
    if problems:
        if "--strict" in sys.argv:
            raise ValueError("\n".join(problems))
        print("Попередження (посилання):\n  " + "\n  ".join(problems))
    return chapters


def parse_entries(path, seen_alias, cat_default=None, extra=None):
    text = path.read_text(encoding="utf-8")
    entries = []
    for block in re.split(r"^## ", text, flags=re.M)[1:]:
        lines = [l.strip() for l in block.strip().splitlines() if l.strip()]
        if lines[0].startswith("@"):
            # «## @id» + «ALIASES: …» — додаткові (українські) аліаси до наявного запису
            if extra is None or len(lines) != 2 or not lines[1].startswith("ALIASES:"):
                raise ValueError(f"{path.name}: поганий блок аліасів: {lines[0][:60]}")
            extra.append((lines[0][1:].strip(), [a.strip() for a in lines[1][8:].split(",") if a.strip()]))
            continue
        head = [x.strip() for x in lines[0].split("|")]
        if len(head) != 5:
            raise ValueError(f"{path.name}: поганий заголовок: {lines[0][:60]}")
        sid, name, aliases, cat, emoji = head
        f = {}
        for line in lines[1:]:
            if ":" not in line:
                raise ValueError(f"{path.name}/{sid}: рядок без ключа: {line[:60]}")
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

        entries.append({
            "id": sid, "name": name, "aliases": al, "cat": cat, "emoji": emoji,
            "what": inline(f.get("WHAT", "")), "image": inline(f.get("IMAGE", "")),
            "when": [inline(x.strip()) for x in f.get("WHEN", "").split(";") if x.strip()],
            "exam": [exam_item(x.strip()) for x in f.get("EXAM", "").split(";") if x.strip()],
            "confuse": [c.strip() for c in f.get("CONFUSE", "").split(",") if c.strip()],
            "chx": f.get("CH", ""),
        })
    return entries


def parse_services(chapters):
    seen, extra = {}, []
    entries = parse_entries(V2 / "services.md", seen)
    if (SRC / "glossary.md").exists():
        entries += parse_entries(SRC / "glossary.md", seen, extra=extra)
    ids = {e["id"] for e in entries}
    if len(ids) != len(entries):
        raise ValueError("Повторюються id у довіднику")
    byid = {e["id"]: e for e in entries}
    for sid, als in extra:
        if sid not in byid:
            raise ValueError(f"glossary.md: аліаси для невідомого запису {sid}")
        for a in als:
            if a in seen:
                raise ValueError(f"Аліас «{a}» є і в {seen[a]}, і в {sid}")
            seen[a] = sid
            byid[sid]["aliases"].append(a)
    for e in entries:
        for c in e["confuse"]:
            if c not in ids:
                raise ValueError(f"{e['id']}: CONFUSE посилається на невідомий {c}")
    # де пояснюється: явне поле CH → перший розділ, що перелічує сервіс у svc → розділ з найбільшою кількістю згадок
    by_meta = {}
    for c in chapters:
        for s in c["svc"]:
            if s not in ids:
                raise ValueError(f"{c['id']}: svc посилається на невідомий {s}")
            by_meta.setdefault(s, c["id"])
    cids = {c["id"] for c in chapters}
    for e in entries:
        ch = e.pop("chx")
        if ch and ch not in cids:
            raise ValueError(f"{e['id']}: CH посилається на невідомий розділ {ch}")
        if not ch:
            ch = by_meta.get(e["id"], "")
        if not ch and e["aliases"]:
            best, best_n = "", 0
            for c in chapters:
                cnt = 0
                for a in e["aliases"]:
                    cnt += len(re.findall(r"(?<![\w-])" + re.escape(a) + r"(?![\w-])", c["plain"]))
                if cnt > best_n:
                    best, best_n = c["id"], cnt
            ch = best
        e["ch"] = ch
    return entries


def parse_questions(path, prefix):
    text = path.read_text(encoding="utf-8")
    qs = []
    for block in re.split(r"^## Q", text, flags=re.M)[1:]:
        lines = [l.strip() for l in block.strip().splitlines() if l.strip()]
        m = re.match(r"(\d+)\s*\|\s*(\w+)", lines[0])
        num, dom = int(m.group(1)), m.group(2)
        if dom not in DOMAINS:
            raise ValueError(f"{path.name} Q{num}: невідомий домен {dom}")
        q = {"id": f"{prefix}{num}", "domain": dom, "en": "", "ua": "", "options": [], "correct": [], "why": ""}
        for line in lines[1:]:
            if line.startswith("EN:"):
                q["en"] = inline(line[3:].strip())
            elif line.startswith("UA:"):
                q["ua"] = inline(line[3:].strip())
            elif line.startswith("WHY:"):
                q["why"] = line[4:].strip()
            else:
                mo = re.match(r"^([A-F])(\*?):\s*(.*)$", line)
                if not mo:
                    raise ValueError(f"{path.name} Q{num}: незрозумілий рядок: {line[:60]}")
                if mo.group(2):
                    q["correct"].append(len(q["options"]))
                q["options"].append(inline(mo.group(3)))
        if not (q["en"] and q["ua"] and q["why"] and len(q["options"]) >= 4 and q["correct"]):
            raise ValueError(f"{path.name} Q{num}: неповне питання")
        # перемішати варіанти й перерахувати букви (A), «B і D» у поясненні
        n_opt = len(q["options"])
        order = shuffled_order(n_opt, q["id"])
        q["options"] = [q["options"][j] for j in order]
        q["correct"] = sorted(order.index(i) for i in q["correct"])

        def relabel(m, order=order, n_opt=n_opt):
            old_i = ord(m.group(1)) - 65
            return LETTERS[order.index(old_i)] if old_i < n_opt else m.group(1)
        why = re.sub(r"(?<![\w-])([A-F])(?![\w-])", relabel, q["why"])

        def sort_seq(m):  # «D і A» → «A і D», «(C, A)» → «(A, C)»
            letters = sorted(re.findall(r"[A-F]", m.group(0)))
            if " і " in m.group(0):
                return ", ".join(letters[:-1]) + " і " + letters[-1]
            return ", ".join(letters)
        why = re.sub(r"(?<![\w-])[A-F](?:(?:, | і )[A-F])+(?![\w-])", sort_seq, why)
        q["why"] = inline(why)
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
  --story:#6d28d9;--story-bg:#f7f3ff;--story-line:#ddd0fb;
  --lab:#0f766e;--lab-bg:#effaf7;--lab-line:#9fdccf;
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
    --story:#c4b5fd;--story-bg:#1d1830;--story-line:#3f3470;
    --lab:#5eead4;--lab-bg:#0f2422;--lab-line:#1f5a52;
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
  --story:#c4b5fd;--story-bg:#1d1830;--story-line:#3f3470;
  --lab:#5eead4;--lab-bg:#0f2422;--lab-line:#1f5a52;
  --code-bg:#252a33;--shadow:none;
  --c-net:#a78bfa;--c-cmp:#fb923c;--c-db:#60a5fa;--c-sto:#4ade80;--c-sec:#f87171;--c-int:#f472b6;--c-ana:#2dd4bf;
  color-scheme:dark;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%;font-size:16px}
body{margin:0;background:var(--bg);color:var(--text);font:1rem/1.6 "Segoe UI",Roboto,"Helvetica Neue",Arial,"Noto Sans",sans-serif}
a{color:var(--accent)}
[hidden]{display:none!important}
.skip{position:absolute;left:-999px}
.skip:focus{left:16px;top:8px;z-index:99;background:var(--surface);padding:6px 10px;border-radius:8px}
.muted{color:var(--muted)}
kbd{font:inherit}
.topbar{position:sticky;top:0;z-index:30;background:var(--surface);border-bottom:1px solid var(--border)}
.topbar-inner{max-width:1100px;margin:0 auto;padding:8px 16px;display:flex;flex-wrap:wrap;align-items:center;gap:8px}
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
.tabs{max-width:1100px;margin:0 auto;padding:0 16px 8px;display:flex;gap:6px;flex-wrap:wrap}
.tab{border:1px solid var(--border);background:var(--surface);color:var(--text);border-radius:99px;padding:6px 14px;font-size:.92rem;text-decoration:none;display:inline-flex;gap:6px;align-items:center}
.tab:hover{border-color:var(--accent)}
.tab[aria-current="page"]{background:var(--accent);border-color:var(--accent);color:var(--accent-ink)}
.readbar{position:fixed;left:0;top:0;height:3px;width:0;background:var(--accent);z-index:35;transition:width .1s linear}
.seg{display:inline-flex;flex-wrap:wrap;border:1px solid var(--border);border-radius:12px;overflow:hidden;background:var(--surface);margin:0 0 14px}
.seg a{padding:8px 14px;font-size:.92rem;color:var(--text);text-decoration:none}
.seg a+a{border-left:1px solid var(--border)}
.seg a[aria-current="page"]{background:var(--accent);color:var(--accent-ink)}
main{min-width:0}
.page{max-width:900px;margin:0 auto;padding:20px 16px 96px}
.page h1{font-size:clamp(1.4rem,3vw,1.9rem);line-height:1.25;margin:.2em 0 .3em}
.hero{padding:6px 0 18px}
.hero h1{font-size:clamp(1.5rem,3.4vw,2.2rem);line-height:1.2;margin:.15em 0 .45em}
.sub{color:var(--muted);margin:0 0 12px}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 12px}
.chips span{background:var(--surface);border:1px solid var(--border);border-radius:99px;padding:4px 12px;font-size:.86rem}
.how{background:var(--accent-soft);border:1px solid var(--trg-line);border-radius:12px;padding:10px 14px;margin:0 0 10px}
.card{background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:18px 20px;margin:0 0 16px;box-shadow:var(--shadow)}
h2{font-size:1.3rem;line-height:1.3}
h3{font-size:1.12rem;margin:20px 0 6px;line-height:1.35}
h4{font-size:1rem;margin:18px 0 8px}
h4.trg-h{color:var(--trg)}
h4.warn-h{color:var(--warn)}
h4.rem-h{color:var(--ok)}
p{margin:8px 0}
ul,ol{margin:6px 0 12px;padding-left:1.25rem}
ol{padding-left:1.5rem}
li{margin:5px 0}
li::marker{color:var(--muted)}
strong{font-weight:650}
code{background:var(--code-bg);padding:.08em .35em;border-radius:5px;font-family:Consolas,"Cascadia Mono","Roboto Mono","DejaVu Sans Mono",monospace;font-size:.88em;overflow-wrap:anywhere}
pre.code{background:var(--code-bg);border:1px solid var(--border);border-radius:10px;padding:10px 12px;overflow-x:auto;font-size:.8rem;line-height:1.45;margin:8px 0 14px}
pre.code code{background:none;padding:0;font-size:inherit;overflow-wrap:normal}
.trg-list,.warn-list,.rem-list{list-style:none;padding:0;display:grid;gap:6px}
.trg-list>li{background:var(--trg-bg);border:1px solid var(--trg-line);border-radius:10px;padding:8px 12px;margin:0}
.warn-list>li{background:var(--warn-bg);border:1px solid var(--warn-line);border-radius:10px;padding:8px 12px;margin:0}
.rem-list>li{background:var(--ok-bg);border:1px solid var(--ok);border-radius:10px;padding:8px 12px;margin:0}
.trg .arr{color:var(--muted)}
.trg .ans{color:var(--trg);font-weight:600}
.callout{border-radius:12px;padding:10px 14px;margin:12px 0;border:1px solid var(--trg-line);background:var(--trg-bg)}
.callout p{margin:6px 0}
.callout.warn{border-color:var(--warn-line);background:var(--warn-bg)}
.callout.new{border-color:var(--ok);background:var(--ok-bg)}
.callout.img{font-size:1.03rem;background:linear-gradient(135deg,var(--accent-soft),var(--trg-bg));border-color:var(--trg-line);padding:12px 16px;border-radius:14px}
.callout.story{border-color:var(--story-line);background:var(--story-bg);border-left:4px solid var(--story);padding:12px 16px}
.box{border-radius:14px;margin:16px 0;border:1px solid var(--border);background:var(--surface-2);overflow:hidden}
.box-h{font-weight:700;padding:10px 14px;border-bottom:1px solid var(--border)}
.box-b{padding:6px 14px 10px}
.box.lab{background:var(--lab-bg);border-color:var(--lab-line)}
.box.lab>.box-h{color:var(--lab);border-color:var(--lab-line)}
.box.note{background:var(--trg-bg);border-color:var(--trg-line)}
.box.calc,.box.example{background:var(--surface);border-style:dashed;border-color:var(--border-strong)}
.box.mnemo{background:var(--story-bg);border-color:var(--story-line)}
.box.mnemo>.box-h{color:var(--story)}
.box.story{background:var(--story-bg);border-color:var(--story-line)}
.box.summary{background:var(--ok-bg);border-color:var(--ok)}
details.box.deep{background:var(--surface-2)}
details.box.deep>summary{cursor:pointer;font-weight:700;padding:10px 14px;list-style:none;display:flex;gap:8px;align-items:center}
details.box.deep>summary::-webkit-details-marker{display:none}
details.box.deep>summary::after{content:"＋";margin-left:auto;color:var(--muted);font-weight:400}
details.box.deep[open]>summary{border-bottom:1px solid var(--border)}
details.box.deep[open]>summary::after{content:"－"}
.tbl{overflow-x:auto;margin:10px 0 14px;border:1px solid var(--border);border-radius:10px}
table{border-collapse:collapse;width:100%;font-size:.92rem}
th,td{text-align:left;vertical-align:top;padding:8px 10px;border-bottom:1px solid var(--border)}
tbody tr:last-child td{border-bottom:0}
th{background:var(--surface-2);font-weight:650}
tbody tr:nth-child(even) td{background:var(--zebra)}
/* головна */
.progress-card{display:flex;flex-wrap:wrap;gap:10px 16px;align-items:center;background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:12px 14px;margin:0 0 12px;box-shadow:var(--shadow)}
.progress-card .bar{flex:1 1 200px;margin:0}
.progress-card p{margin:0;font-size:.9rem;color:var(--muted)}
.bar{height:8px;background:var(--surface-2);border-radius:99px;overflow:hidden}
.bar span{display:block;height:100%;width:0;background:var(--ok);transition:width .3s}
#home-continue{white-space:normal;text-align:left}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:8px;margin:0 0 12px}
.stat{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:10px 12px}
.stat b{display:block;font-size:1.25rem}
.stat span{font-size:.8rem;color:var(--muted)}
section.module{margin:24px 0 0}
section.module h2{font-size:.9rem;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);margin:0 0 10px}
.lesson-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:10px}
.lesson-card{display:flex;gap:12px;align-items:flex-start;border:1px solid var(--border);background:var(--surface);border-radius:12px;padding:12px;text-decoration:none;color:var(--text);box-shadow:var(--shadow)}
.lesson-card:hover{border-color:var(--accent)}
.lesson-card .le{font-size:1.7rem;line-height:1}
.lesson-card .ln{display:block;font-size:.78rem;color:var(--muted)}
.lesson-card .lt{display:block;font-weight:650;line-height:1.3}
.lesson-card .ls{display:block;font-size:.78rem;color:var(--muted);margin-top:3px}
.lesson-card.done{border-color:var(--ok)}
.lesson-card.done .ln::after{content:" · ✓ пройдено";color:var(--ok);font-weight:600}
.lesson-card.cur{box-shadow:0 0 0 2px var(--accent)}
.disclaimer{font-size:.8rem;color:var(--muted);margin:26px 0 0}
.install-card{display:flex;flex-wrap:wrap;gap:8px 12px;align-items:center;justify-content:space-between;background:var(--surface);border:1px dashed var(--accent);border-radius:14px;padding:10px 14px;margin:0 0 12px}
.install-card .muted{font-size:.88rem}
.offline-ok{font-size:.85rem;color:var(--ok);margin:0 0 10px}
.also{font-size:.92rem;margin:0 0 10px}
/* розділ */
article.chapter{max-width:820px;margin:0 auto}
.ch-top{display:flex;flex-wrap:wrap;gap:6px 14px;justify-content:space-between;font-size:.88rem;margin:0 0 4px}
.ch-top .meta{color:var(--muted)}
.ch-title{font-size:clamp(1.45rem,3.2vw,2rem);line-height:1.25;margin:.3em 0 .4em;display:flex;gap:12px;align-items:flex-start}
.ch-title .le{flex:none}
.ch-doms{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 12px;font-size:.8rem}
.ch-doms span{border-radius:99px;padding:3px 10px;background:var(--surface);border:1px solid var(--border);color:var(--muted)}
.ch-toc{background:var(--surface);border:1px solid var(--border);border-radius:12px;margin:0 0 16px}
.ch-toc summary{cursor:pointer;padding:10px 14px;font-weight:650}
.ch-toc ol{margin:0;padding:0 14px 12px 2.2rem}
.ch-toc li{margin:4px 0}
.ch-toc a{color:var(--text);text-decoration:none}
.ch-toc a:hover{color:var(--accent);text-decoration:underline}
.ch-body{background:var(--surface);border:1px solid var(--border);border-radius:16px;padding:6px 26px 18px;box-shadow:var(--shadow)}
.ch-body p,.ch-body li{line-height:1.68}
.cs{padding:4px 0 8px}
.cs+.cs{border-top:1px solid var(--border);margin-top:10px}
.ch-h2{font-size:1.35rem;margin:22px 0 8px;scroll-margin-top:110px}
.ch-body h3,.ch-body h4,figure.diagram,.qz,.ch-body li,.ch-body p{scroll-margin-top:110px}
.flash{animation:flash 1.8s ease-out}
@keyframes flash{0%{background:var(--accent-soft);box-shadow:0 0 0 6px var(--accent-soft)}100%{background:transparent;box-shadow:none}}
.ch-nav{display:flex;flex-wrap:wrap;gap:8px;justify-content:space-between;align-items:center;margin:16px 0 4px}
.ch-nav .tb-btn{white-space:normal;text-align:left}
.ch-score{font-size:.88rem;color:var(--muted);margin:10px 0 0}
/* квіз у розділі */
.qz-list{display:grid;gap:12px;margin:10px 0 14px}
.qz{border:1px solid var(--border);border-radius:14px;padding:12px 14px;background:var(--surface)}
.qz,.ch-body p,.ch-body li,.ch-body blockquote{overflow-wrap:anywhere}
.qz-h{font-size:.78rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.04em}
.qz-q{font-weight:600;margin:4px 0 8px;line-height:1.5}
.qz-note{font-weight:700;color:var(--warn);font-size:.9rem;margin:0 0 6px}
.qz-opts{display:grid;gap:7px}
.qz-o{display:flex;gap:10px;align-items:flex-start;text-align:left;width:100%;border:1.5px solid var(--border);background:var(--surface);color:var(--text);border-radius:12px;padding:9px 12px;font:inherit;line-height:1.45;cursor:pointer}
.qz-o:hover{border-color:var(--accent)}
.qz-o[aria-pressed="true"]{border-color:var(--accent);background:var(--accent-soft)}
.qz-o.right{border-color:var(--ok);background:var(--ok-bg)}
.qz-o.wrong{border-color:var(--bad);background:var(--bad-bg)}
.qz.done .qz-o{cursor:default}
.qz-act{display:flex;gap:10px;align-items:center;margin-top:8px}
.qz-act:empty{display:none}
.qz-why{border-radius:10px;padding:10px 12px;margin-top:8px;background:var(--surface-2);border:1px solid var(--border)}
.qz-why.ok{background:var(--ok-bg);border-color:var(--ok)}
.qz-why.bad{background:var(--bad-bg);border-color:var(--bad)}
.t-letter{flex:none;display:inline-grid;place-items:center;width:1.6rem;height:1.6rem;border-radius:7px;background:var(--surface-2);font-weight:700;font-size:.85rem}
/* схеми */
.diagram{margin:16px 0;border:1px solid var(--border);border-radius:12px;padding:12px;background:var(--surface-2);font-size:.86rem;line-height:1.4}
.diagram figcaption{font-size:.84rem;color:var(--muted);margin-top:10px}
.dg-box{border:1.5px dashed var(--border-strong);border-radius:10px;padding:8px;background:var(--surface)}
.dg-label{font-size:.74rem;font-weight:700;letter-spacing:.03em;text-transform:uppercase;color:var(--muted);margin:0 0 6px;display:flex;flex-wrap:wrap;gap:6px;align-items:center}
.dg-azs{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.dg-azs.three{grid-template-columns:repeat(3,1fr)}
.dg-az{background:var(--surface-2)}
.dg-sub{--c:var(--c-sto);border-radius:8px;padding:6px 8px;margin-top:6px;border:1px solid var(--border);border-left:4px solid var(--c);background:var(--surface)}
.dg-sub.pub{--c:var(--c-sto)}.dg-sub.app{--c:var(--c-cmp)}.dg-sub.db{--c:var(--c-db)}.dg-sub.sec{--c:var(--c-sec)}.dg-sub.int{--c:var(--c-int)}.dg-sub.ana{--c:var(--c-ana)}.dg-sub.net{--c:var(--c-net)}
.dg-sub small{display:block;color:var(--muted);margin-top:3px}
.dg-nodes{display:flex;flex-wrap:wrap;gap:4px;margin-top:4px}
.dg-node{--c:var(--muted);display:inline-block;padding:2px 8px;border-radius:7px;border:1px solid var(--c);background:var(--surface);color:var(--text);font-size:.8rem;font-weight:600;line-height:1.35;text-transform:none;letter-spacing:0}
.dg-node.net{--c:var(--c-net)}.dg-node.cmp{--c:var(--c-cmp)}.dg-node.db{--c:var(--c-db)}.dg-node.sto{--c:var(--c-sto)}.dg-node.sec{--c:var(--c-sec)}.dg-node.int{--c:var(--c-int)}.dg-node.ana{--c:var(--c-ana)}
.flow{display:flex;align-items:stretch;gap:6px}
.flow>.st{flex:1 1 0;min-width:0;border:1px solid var(--border);border-radius:10px;padding:8px;background:var(--surface);font-size:.8rem}
.flow>.st b{display:block;font-size:.85rem;margin-bottom:3px}
.flow>.st .dg-node{margin:2px 0}
.flow>.st.lanes .dg-node{display:block;margin:4px 0}
.flow>.st small{display:block;color:var(--muted);margin-top:4px}
.flow>.ar{align-self:center;color:var(--muted);font-weight:700;flex:none;font-size:1.1rem}
.flow.col{flex-direction:column}
.flow.col>.ar{transform:rotate(90deg)}
.dg-govern{margin-top:8px;border:1px solid var(--c-sec);border-radius:10px;padding:6px 10px;background:var(--surface);font-size:.82rem}
.tiers{display:grid;gap:2px}
.tier{display:flex;flex-wrap:wrap;gap:6px;align-items:center;border:1px solid var(--border);border-radius:10px;padding:8px;background:var(--surface)}
.tier .tl{min-width:104px;font-size:.72rem;font-weight:700;text-transform:uppercase;color:var(--muted)}
.tier small{color:var(--muted)}
.down{text-align:center;color:var(--muted);line-height:1.1;font-weight:700}
.dec{display:grid;gap:2px}
.dec-step{display:grid;grid-template-columns:auto 1fr auto;gap:10px;align-items:center;border:1px solid var(--border);border-radius:10px;padding:8px 10px;background:var(--surface)}
.dec-n{display:inline-grid;place-items:center;width:1.7rem;height:1.7rem;border-radius:50%;background:var(--accent-soft);color:var(--accent);font-weight:700}
.dec-out{font-weight:700;font-size:.82rem;max-width:260px}
.dec-out.no{color:var(--bad)}.dec-out.yes{color:var(--ok)}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}
.grid4{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}
.gcard{border:1px solid var(--border);border-radius:10px;padding:8px 10px;background:var(--surface);font-size:.82rem}
.gcard>b{display:block;font-size:.88rem;margin-bottom:2px}
.gcard small{display:block;color:var(--muted)}
.gcard.hl{border-color:var(--accent);box-shadow:0 0 0 1px var(--accent)}
.scale{height:8px;border-radius:99px;background:linear-gradient(90deg,var(--c-sto),var(--c-cmp),var(--c-sec));margin:10px 0 4px}
.scale-legend{display:flex;justify-content:space-between;gap:8px;font-size:.75rem;color:var(--muted)}
.hbar{display:grid;grid-template-columns:minmax(90px,auto) 1fr;gap:6px 10px;align-items:center;font-size:.82rem}
.hbar .hb{height:14px;border-radius:6px;background:var(--accent);min-width:4px}
.hbar .hb.c1{background:var(--c-sto)}.hbar .hb.c2{background:var(--c-cmp)}.hbar .hb.c3{background:var(--c-db)}.hbar .hb.c4{background:var(--c-net)}.hbar .hb.c5{background:var(--c-sec)}
.svg-dg{display:block;width:100%;height:auto;max-width:620px;margin:0 auto}
.svg-dg text{font-family:"Segoe UI",Roboto,Arial,"Noto Sans",sans-serif;font-size:14px;font-weight:600;fill:var(--text)}
.svg-dg text.s{font-size:13px;font-weight:400;fill:var(--muted)}
.svg-dg text.h{font-size:12px;font-weight:700;fill:var(--muted);letter-spacing:.04em}
.svg-dg .bx{fill:var(--surface);stroke:var(--border-strong);stroke-width:1.5}
.svg-dg .bx2{fill:var(--surface-2);stroke:var(--border);stroke-width:1.2}
.svg-dg .dash{fill:none;stroke:var(--border-strong);stroke-width:1.5;stroke-dasharray:6 4}
.svg-dg .ln{fill:none;stroke:var(--muted);stroke-width:1.8}
.svg-dg .ln-a{fill:none;stroke:var(--accent);stroke-width:2.2}
.svg-dg .ln-ok{fill:none;stroke:var(--ok);stroke-width:2.2}
.svg-dg .ln-bad{fill:none;stroke:var(--bad);stroke-width:2.2;stroke-dasharray:5 4}
.svg-dg .f-cmp{fill:var(--c-cmp)}.svg-dg .f-db{fill:var(--c-db)}.svg-dg .f-sto{fill:var(--c-sto)}.svg-dg .f-net{fill:var(--c-net)}.svg-dg .f-sec{fill:var(--c-sec)}.svg-dg .f-ana{fill:var(--c-ana)}.svg-dg .f-int{fill:var(--c-int)}.svg-dg .f-acc{fill:var(--accent)}.svg-dg .f-mut{fill:var(--muted)}
.svg-dg .s-cmp{stroke:var(--c-cmp)}.svg-dg .s-db{stroke:var(--c-db)}.svg-dg .s-sto{stroke:var(--c-sto)}.svg-dg .s-net{stroke:var(--c-net)}.svg-dg .s-sec{stroke:var(--c-sec)}.svg-dg .s-ana{stroke:var(--c-ana)}
.svg-dg .soft{opacity:.16}
.svg-dg text.w{fill:#fff}
.svg-dg .arrow{fill:var(--muted)}
#dg-gallery .dg-item{margin:0 0 26px}
#dg-gallery h2{font-size:1.05rem;margin:0 0 4px}
.dg-link{font-size:.9rem}
/* практика */
.qz-row{display:flex;flex-wrap:wrap;gap:10px;align-items:center}
select{font:inherit;font-size:.9rem;padding:7px 9px;border-radius:9px;border:1px solid var(--border);background:var(--surface-2);color:var(--text);max-width:100%}
.chk{display:inline-flex;gap:6px;align-items:center;font-size:.92rem;cursor:pointer}
.pc-src{font-size:.85rem;color:var(--muted);margin:10px 0 6px}
.pc-stats{margin-top:12px;font-size:.88rem;color:var(--muted)}
.fc-sec{margin-top:16px;font-size:.82rem;color:var(--muted)}
.fc-q{font-size:1.18rem;font-weight:600;line-height:1.45;margin:6px 0 14px;min-height:3.2em}
.fc-a{background:var(--trg-bg);border:1px solid var(--trg-line);color:var(--trg);border-radius:10px;padding:10px 12px;font-weight:600;margin-bottom:14px}
.fc-actions{display:flex;flex-wrap:wrap;gap:8px}
.fc-hint{font-size:.82rem;color:var(--muted)}
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
/* пошук */
.sr{display:block;border:1px solid var(--border);background:var(--surface);border-radius:12px;padding:10px 12px;margin:0 0 8px;color:var(--text);text-decoration:none}
.sr:hover{border-color:var(--accent)}
.sr b{display:block;font-size:.85rem;color:var(--muted);margin-bottom:2px}
.sr mark{background:var(--warn-bg);color:inherit;border-radius:3px;padding:0 1px;box-shadow:0 0 0 1px var(--warn-line)}
/* словник і підказки */
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
body.hints-on .svc{text-decoration:underline dotted var(--accent);text-decoration-thickness:1.5px;text-underline-offset:3px;cursor:pointer;border-radius:3px}
body.hints-on .svc:hover{background:var(--accent-soft)}
.svc-overlay{position:fixed;inset:0;z-index:70;background:rgba(10,12,16,.45);display:flex;align-items:flex-end;justify-content:center}
.svc-card{width:min(620px,100%);max-height:84vh;overflow:auto;background:var(--surface);color:var(--text);border:1px solid var(--border);border-radius:18px 18px 0 0;padding:16px 18px calc(18px + env(safe-area-inset-bottom));box-shadow:0 -10px 40px rgba(0,0,0,.25)}
.svc-head{display:flex;gap:12px;align-items:flex-start;margin-bottom:6px}
.svc-emoji{font-size:2.1rem;line-height:1}
.svc-head h2{font-size:1.2rem;margin:0 0 4px}
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
.svc-links .tb-btn{white-space:normal;text-align:left}
.ask-overlay{position:fixed;inset:0;z-index:80;background:rgba(10,12,16,.45);display:flex;align-items:center;justify-content:center;padding:16px}
.ask-card{width:100%;max-width:420px;background:var(--surface);color:var(--text);border:1px solid var(--border);border-radius:16px;padding:16px 18px;box-shadow:0 10px 30px rgba(0,0,0,.25)}
.ask-card p{margin:0 0 12px;font-size:1.02rem}
.ask-actions{display:flex;gap:8px;justify-content:flex-end}
.hint-chip{position:fixed;left:50%;transform:translateX(-50%);bottom:calc(20px + env(safe-area-inset-bottom));z-index:65;border:0;border-radius:99px;padding:10px 16px;background:var(--accent);color:var(--accent-ink);font:inherit;font-weight:650;box-shadow:0 6px 20px rgba(0,0,0,.25);cursor:pointer;max-width:90vw;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.to-top{position:fixed;right:16px;bottom:16px;z-index:25;width:44px;height:44px;border-radius:50%;border:1px solid var(--border);background:var(--surface);color:var(--text);font-size:1.2rem;cursor:pointer;box-shadow:var(--shadow);opacity:0;pointer-events:none;transition:opacity .2s}
.to-top.show{opacity:1;pointer-events:auto}
.foot{color:var(--muted);font-size:.85rem;text-align:center;padding:12px 0}
body.modal-open{overflow:hidden}
.print-only{display:none}
@media (min-width:721px){.svc-overlay{align-items:center;padding:16px}.svc-card{border-radius:18px}}
@media (max-width:960px){
  .tabs{position:fixed;left:0;right:0;bottom:0;z-index:40;background:var(--surface);border-top:1px solid var(--border);margin:0;max-width:none;padding:4px 4px calc(4px + env(safe-area-inset-bottom));gap:0;flex-wrap:nowrap;justify-content:space-around;box-shadow:0 -2px 10px rgba(0,0,0,.06)}
  .tab{flex:1;flex-direction:column;gap:1px;border:0;border-radius:10px;padding:5px 2px;font-size:.68rem;background:none;justify-content:center}
  .tab .ti{font-size:1.25rem;line-height:1.1}
  .tab[aria-current="page"]{background:var(--accent-soft);color:var(--accent)}
  body{padding-bottom:calc(64px + env(safe-area-inset-bottom))}
  .to-top{bottom:calc(78px + env(safe-area-inset-bottom))}
  .hint-chip{bottom:calc(82px + env(safe-area-inset-bottom))}
}
@media (max-width:720px){
  .lbl,.brand-sub{display:none}
  .search{order:5;flex-basis:100%}
  .card{padding:14px}
  .ch-body{padding:4px 14px 14px;border-radius:14px}
  .ch-h2{font-size:1.2rem}
  .flow{flex-direction:column}
  .flow>.ar{transform:rotate(90deg)}
  .grid3,.grid4{grid-template-columns:1fr 1fr}
  .dec-step{grid-template-columns:auto 1fr}
  .dec-out{grid-column:2}
  .fc-hint kbd{display:none}
}
@media (max-width:560px){.dg-azs,.dg-azs.three,.grid2{grid-template-columns:1fr}}
@media (max-width:420px){.grid3,.grid4{grid-template-columns:1fr}}
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
"""

PRINT_CSS = r"""
@page{size:A5;margin:12mm 10mm 14mm;@bottom-center{content:counter(page);font-size:8pt;color:#777}}
@page:first{@bottom-center{content:none}}
:root,:root[data-theme="dark"]{
  --bg:#fff;--surface:#fff;--surface-2:#f1f3f6;--zebra:#f7f8fa;--text:#111;--muted:#555;--border:#d7dbe0;--border-strong:#b8c0ca;
  --accent:#1f5fcf;--accent-soft:#e9f0fd;--trg:#0b4fb8;--trg-bg:#f3f7ff;--trg-line:#c9dafa;
  --warn:#7a4a00;--warn-bg:#fff7e6;--warn-line:#efcf93;--code-bg:#eef0f3;--ok:#1f7a45;--ok-bg:#eaf7ef;--bad:#b42318;--bad-bg:#fdecea;
  --story:#5b21b6;--story-bg:#f7f3ff;--story-line:#ddd0fb;--lab:#0f766e;--lab-bg:#effaf7;--lab-line:#9fdccf;
  --c-net:#7c3aed;--c-cmp:#c2410c;--c-db:#1d4ed8;--c-sto:#15803d;--c-sec:#b91c1c;--c-int:#be185d;--c-ana:#0f766e;
  color-scheme:light;
}
html{font-size:10.2pt}
body{background:#fff;line-height:1.45;padding:0;-webkit-print-color-adjust:exact;print-color-adjust:exact}
p,li{margin:3px 0}
.ch-body p,.ch-body li{line-height:1.5}
h3{margin:10px 0 4px}
h4{margin:9px 0 5px}
a{color:inherit;text-decoration:none}
.cover{height:170mm;display:flex;flex-direction:column;justify-content:center;break-after:page}
.cover h1{font-size:24pt;line-height:1.15;margin:0 0 6mm}
.cover .sub{font-size:11pt}
.cover .big{font-size:40pt;margin:0 0 4mm}
.ptoc{break-after:page}
.ptoc h2{font-size:14pt;margin:0 0 3mm}
.ptoc h3{font-size:9pt;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);margin:4mm 0 1mm}
.ptoc ol{list-style:none;margin:0;padding:0}
.ptoc a{display:flex;gap:6px;padding:.7mm 0;border-bottom:.5px dotted #bbb}
.ptoc a .n{min-width:1.8em;color:var(--accent);font-weight:700}
.intro-print{break-after:page}
article.chapter{break-before:page;max-width:none;margin:0}
.ch-top .back,.ch-nav,.ch-score,.ch-toc,.qz-act,.qz-verdict{display:none!important}
.ch-top{justify-content:flex-start}
.ch-title{font-size:17pt;margin:1mm 0 3mm}
.ch-body{border:0;box-shadow:none;padding:0;border-radius:0}
.cs+.cs{border-top:0;margin-top:0}
.ch-h2{font-size:13pt;margin:6mm 0 2mm;border-bottom:1.2px solid var(--accent);padding-bottom:1mm}
h2,h3,h4,.ch-h2,.box-h,summary{break-after:avoid}
li,tr,.callout,.diagram,pre.code,.qz,.gcard,.dec-step,.tier{break-inside:avoid}
.qz-why{display:block!important;font-size:.92em}
.qz-o{padding:3px 7px;border-width:1px}
.qz-opts{gap:3px}
.qz{padding:6px 8px}
.trg-list>li,.warn-list>li,.rem-list>li{padding:2px 7px;border-radius:6px}
.trg-list,.warn-list,.rem-list{gap:3px;margin:4px 0 8px}
ul,ol{margin:3px 0 8px}
.tbl{overflow:visible;border-radius:0}
table{font-size:8.2pt}
th,td{padding:3px 5px}
.diagram{font-size:8pt;padding:6px}
.flow{flex-direction:column}
.flow>.ar{transform:rotate(90deg)}
.grid4{grid-template-columns:1fr 1fr}
details.box.deep>summary::after{content:none}
.box{margin:8px 0}
.svg-dg{max-width:110mm}
.appendix{break-before:page}
.appendix h2{font-size:14pt}
.gl{columns:1;font-size:8.6pt}
.gl p{margin:0 0 1.6mm;break-inside:avoid}
.gl .cat{font-weight:700;color:var(--accent);margin:3mm 0 1mm;break-after:avoid}
.svc{text-decoration:none!important}
"""

# ---------- Скрипт сторінки ----------

JS = r"""
(function(){
  'use strict';
  var $=function(s,r){return (r||document).querySelector(s)};
  var $$=function(s,r){return Array.prototype.slice.call((r||document).querySelectorAll(s))};
  var P='deep.';
  var store={get:function(k,d){try{var v=localStorage.getItem(P+k);return v===null?d:JSON.parse(v)}catch(e){return d}},
             set:function(k,v){try{localStorage.setItem(P+k,JSON.stringify(v))}catch(e){}}};
  var body=document.body, root=document.documentElement;
  function esc(s){return String(s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
  function txt(h){var d=document.createElement('div');d.innerHTML=h;return d.textContent}
  function idle(fn){(window.requestIdleCallback||function(cb){return setTimeout(cb,30)})(fn)}
  function obj(v){return v&&typeof v==='object'&&!Array.isArray(v)?v:{}}
  function arr(v){return Array.isArray(v)?v:[]}
  function ask(text,yes){
    var o=$('#ask'),y=$('#ask-yes'),n=$('#ask-no');
    $('#ask-text').textContent=text; o.hidden=false; body.classList.add('modal-open');
    function close(){o.hidden=true;body.classList.remove('modal-open');y.onclick=n.onclick=o.onclick=null}
    y.onclick=function(){close();yes()}; n.onclick=close; o.onclick=function(e){if(e.target===o){close()}};
    y.focus();
  }
  function shuffle(a){for(var i=a.length-1;i>0;i--){var j=Math.floor(Math.random()*(i+1)),t=a[i];a[i]=a[j];a[j]=t}return a}

  var CH=JSON.parse($('#chdata').textContent), CMAP={};
  CH.forEach(function(c,i){c.n=i+1;CMAP[c.id]=c});
  var MODS=[]; CH.forEach(function(c){if(MODS.indexOf(c.module)<0){MODS.push(c.module)}});
  var SVC=JSON.parse($('#sdata').textContent), SMAP={}; SVC.forEach(function(s){SMAP[s.id]=s});
  var CATS=JSON.parse($('#cdata').textContent);
  function tpl(id){var t=document.getElementById('tpl-'+id);return t&&t.content?t.content:null}

  /* тема і шрифт */
  var theme=store.get('theme',null); if(theme){root.setAttribute('data-theme',theme)}
  $('#btn-theme').addEventListener('click',function(){
    var cur=root.getAttribute('data-theme');
    var dark=cur?cur==='dark':window.matchMedia('(prefers-color-scheme: dark)').matches;
    root.setAttribute('data-theme',dark?'light':'dark'); store.set('theme',dark?'light':'dark');
  });
  var FS=[15,16,17,18.5,20], fsi=store.get('fs',1); if(!(fsi>=0&&fsi<FS.length)){fsi=1}
  function applyFs(){root.style.fontSize=FS[fsi]+'px'}
  applyFs();
  $('#btn-font').addEventListener('click',function(){fsi=(fsi+1)%FS.length;store.set('fs',fsi);applyFs()});

  /* стан навчання */
  var done=arr(store.get('done',[])), qres=obj(store.get('q',{})), pos=obj(store.get('pos',{}));
  function isDone(id){return done.indexOf(id)>=0}
  function chScore(c){var ok=0,ans=0;for(var k=1;k<=c.q;k++){var r=qres[c.id+'-'+k];if(r){ans++;if(r.ok){ok++}}}return {ok:ok,ans:ans,n:c.q}}

  /* ---------- підказки ---------- */
  var hintsOn=store.get('hints',true)!==false;
  var aliasPairs=[]; SVC.forEach(function(s){s.aliases.forEach(function(a){aliasPairs.push([a,s.id])})});
  aliasPairs.sort(function(x,y){return y[0].length-x[0].length});
  var ALIAS={}, ALIAS_LC={};
  aliasPairs.forEach(function(p){ALIAS[p[0]]=p[1];var k=p[0].toLowerCase();if(!ALIAS_LC[k]){ALIAS_LC[k]=p[1]}});
  var RX=new RegExp(aliasPairs.map(function(p){return p[0].replace(/[.*+?^${}()|[\]\\]/g,'\\$&')}).join('|'),'g');
  var WORDCH=/[0-9A-Za-zА-ЩЬЮЯҐЄІЇа-щьюяґєії_\u0301'’-]/;
  var SKIP='code,pre,a,button,.svc,input,textarea,select,script,style,.svc-card,summary,.tab,.seg,kbd,.lesson-card,.t-opt,.qz-o,h1,h2,svg,.ch-toc,.ch-top,.sr';
  function firstAlias(t){
    RX.lastIndex=0; var m;
    while((m=RX.exec(t))){var s=m.index,e=s+m[0].length;
      if((s>0&&WORDCH.test(t[s-1]))||(e<t.length&&WORDCH.test(t[e]))){RX.lastIndex=s+1;continue}
      return ALIAS[m[0]]}
    return null;
  }
  function linkify(el,once){
    if(!el||!hintsOn||el.dataset.linked){return}
    el.dataset.linked='1';
    var seen={};
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
        var id=ALIAS[m[0]];
        if(once){if(seen[id]){continue}seen[id]=1}
        if(!frag){frag=document.createDocumentFragment()}
        if(s>last){frag.appendChild(document.createTextNode(t.slice(last,s)))}
        var sp=document.createElement('span'); sp.className='svc'; sp.dataset.svc=id; sp.textContent=m[0];
        frag.appendChild(sp); last=e;
      }
      if(frag){if(last<t.length){frag.appendChild(document.createTextNode(t.slice(last)))}n.parentNode.replaceChild(frag,n)}
    });
  }
  function linkifyChapter(art){
    if(!hintsOn||!art){return}
    var secs=$$('.cs',art), k=0;
    (function step(){var s=secs[k++];if(!s){return}linkify(s,true);idle(step)})();
  }
  var overlay=$('#svc-overlay');
  function openCard(id){
    var s=SMAP[id]; if(!s){return}
    $('#svc-emoji').textContent=s.emoji; $('#svc-title').textContent=s.name; $('#svc-cat').textContent=CATS[s.cat]||'';
    $('#svc-what').innerHTML=s.what;
    $('#svc-image').innerHTML=s.image?'<b>🖼️ Образ.</b> '+s.image:''; $('#svc-image').hidden=!s.image;
    $('#svc-when').innerHTML=s.when.map(function(w){return '<li>'+w+'</li>'}).join(''); $('#svc-when-h').hidden=!s.when.length;
    $('#svc-when-h').textContent=(s.cat==='it'||s.cat==='concept')?'📍 Де зустрінеш':'✅ Коли обирати';
    $('#svc-exam').innerHTML=s.exam.map(function(x){return '<li>'+x+'</li>'}).join(''); $('#svc-exam-h').hidden=!s.exam.length;
    $('#svc-confuse').innerHTML=s.confuse.length?('<span class="muted">Не плутай з:</span> '+s.confuse.map(function(c){var o=SMAP[c];
      return o?'<button class="chip-btn" type="button" data-open="'+c+'">'+o.emoji+' '+esc(o.name)+'</button>':''}).join(' ')):'';
    var c=CMAP[s.ch], out='';
    if(c){out+='<a class="tb-btn primary" href="#ch/'+c.id+'">📖 Розділ '+c.n+': '+esc(c.emoji+' '+c.title)+'</a>'}
    out+='<button class="tb-btn" type="button" data-find="'+esc(s.aliases[0]||s.name)+'">🔍 Шукати в курсі</button>';
    $('#svc-links').innerHTML=out;
    overlay.hidden=false; body.classList.add('modal-open'); $('.svc-card').scrollTop=0;
  }
  function closeCard(){overlay.hidden=true;body.classList.remove('modal-open')}
  overlay.addEventListener('click',function(e){
    if(e.target===overlay){closeCard();return}
    var b=e.target.closest('[data-open]'); if(b){openCard(b.dataset.open);return}
    var f=e.target.closest('[data-find]'); if(f){closeCard();sInput.value=f.dataset.find;doSearch();return}
    if(e.target.closest('a[href^="#"]')){closeCard()}
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
    hintsOn=on; body.classList.toggle('hints-on',on); hb.setAttribute('aria-pressed',on?'true':'false'); store.set('hints',on);
    if(on&&curView==='ch'){linkifyChapter($('#reader .chapter'))}else if(!on){chip.hidden=true}
  }
  hb.addEventListener('click',function(){applyHints(!hintsOn)});

  /* ---------- перемикання вкладок ---------- */
  var curView='home';
  var TAB={home:'home',ch:'home',search:'home',practice:'practice',glossary:'glossary',diagrams:'diagrams'};
  function showView(v){
    curView=v; body.dataset.view=v;
    $$('.view').forEach(function(el){el.hidden=el.dataset.view!==v});
    $$('.tab').forEach(function(t){t.setAttribute('aria-current',t.dataset.tab===TAB[v]?'page':'false')});
    chip.hidden=true; readbar.hidden=v!=='ch';
    if(v!=='ch'){document.title=baseTitle}
  }
  var baseTitle=document.title, readbar=$('#readbar');

  /* ---------- головна ---------- */
  function renderHome(){
    $$('.lesson-card').forEach(function(a){var c=CMAP[a.dataset.id];a.classList.toggle('done',isDone(c.id));
      var sc=chScore(c), el=$('.ls',a);
      if(el){el.textContent=sc.ans?('✅ Перевір себе: '+sc.ok+' / '+sc.n):(c.q?'✅ '+c.q+' питань для самоперевірки':'')}});
    var n=CH.filter(function(c){return isDone(c.id)}).length;
    $('#home-progress').textContent='Пройдено розділів: '+n+' з '+CH.length;
    $('#home-bar').style.width=Math.round(n*100/CH.length)+'%';
    var last=store.get('last',null), cont=$('#home-continue');
    var target=(last&&CMAP[last])?CMAP[last]:(CH.filter(function(c){return !isDone(c.id)})[0]||CH[0]);
    cont.href='#ch/'+target.id+'/@'; cont.textContent=(last?'▶ Продовжити: ':'▶ Почати: ')+target.n+'. '+target.emoji+' '+target.title;
    $$('.lesson-card').forEach(function(a){a.classList.toggle('cur',a.dataset.id===target.id)});
    var qok=0,qans=0,qall=0; CH.forEach(function(c){var s=chScore(c);qok+=s.ok;qans+=s.ans;qall+=c.q});
    var best=bestFull();
    $('#home-stats').innerHTML='<div class="stat"><b>'+n+' / '+CH.length+'</b><span>розділів пройдено</span></div>'+
      '<div class="stat"><b>'+qok+' / '+qall+'</b><span>питань «Перевір себе» — правильно</span></div>'+
      '<div class="stat"><b>'+cardsKnown()+' / '+(cardsTotal||'…')+'</b><span>карток-тригерів знаєш</span></div>'+
      '<div class="stat"><b>'+(best>=0?best+'%':'—')+'</b><span>найкращий пробний іспит</span></div>';
  }

  /* ---------- розділ ---------- */
  var reader=$('#reader'), openId=null;
  function openChapter(id,anchor){
    var c=CMAP[id]; if(!c){location.hash='#home';return}
    if(openId!==id){
      var t=tpl(id); reader.innerHTML=''; reader.appendChild(t.cloneNode(true)); openId=id;
      var art=$('.chapter',reader); initDoneBtn(art); updateScore(art); restoreQz(art); linkifyChapter(art);
    }
    document.title=c.n+'. '+c.title+' — SAA-C03 з нуля';
    store.set('last',id);
    var el=null;
    if(anchor&&anchor!=='@'){
      if(/^b\d+$/.test(anchor)){el=$$(SEL,$('.ch-body',reader))[+anchor.slice(1)]||null}
      else if(/^q-/.test(anchor)){el=document.getElementById(anchor)}
      else{el=document.getElementById(id+'--'+anchor)}
    }
    if(el){
      var d=el.closest('details'); if(d){d.open=true}
      setTimeout(function(){el.scrollIntoView({block:'start'});el.classList.remove('flash');void el.offsetWidth;el.classList.add('flash')},30);
    } else if(anchor==='@'&&pos[id]){
      setTimeout(function(){var h=document.documentElement.scrollHeight-innerHeight;window.scrollTo(0,Math.round(pos[id]*h))},30);
    } else {window.scrollTo(0,0)}
    onScroll();
  }
  function initDoneBtn(art){
    var b=$('.done-btn',art); if(!b){return}
    var on=isDone(b.dataset.id); b.setAttribute('aria-pressed',on?'true':'false'); b.textContent=on?'✅ Пройдено':'☐ Позначити пройденим';
  }
  document.addEventListener('click',function(e){
    var b=e.target.closest('.done-btn'); if(!b){return}
    var id=b.dataset.id,k=done.indexOf(id); if(k>=0){done.splice(k,1)}else{done.push(id)}
    store.set('done',done); initDoneBtn(b.closest('.chapter'));
  });
  function updateScore(art){
    var el=$('.ch-score',art); if(!el){return}
    var c=CMAP[art.dataset.id], s=chScore(c);
    el.textContent=c.q?('✅ Перевір себе: відповідей '+s.ans+' з '+s.n+', правильно '+s.ok+'.'):'';
  }
  function restoreQz(art){
    $$('.qz',art).forEach(function(box){var r=qres[box.dataset.q];if(r&&r.a){showQz(box,r.a,false)}});
  }

  /* питання «Перевір себе» */
  function corr(box){return box.dataset.c.split(',').map(Number)}
  function showQz(box,chosen,save){
    var c=corr(box), ok=chosen.length===c.length&&chosen.every(function(i){return c.indexOf(i)>=0});
    $$('.qz-o',box).forEach(function(o){var i=+o.dataset.i;o.classList.remove('right','wrong');o.setAttribute('aria-pressed','false');
      if(c.indexOf(i)>=0){o.classList.add('right')}else if(chosen.indexOf(i)>=0){o.classList.add('wrong')}});
    var why=$('.qz-why',box); why.hidden=false; why.className='qz-why '+(ok?'ok':'bad');
    $('.qz-verdict',box).textContent=ok?'✓ Правильно.':'✗ Неправильно.';
    box.classList.add('done'); $('.qz-check',box).hidden=true; $('.qz-reset',box).hidden=false;
    if(save){qres[box.dataset.q]={ok:ok,a:chosen,t:Date.now()};store.set('q',qres);
      var art=box.closest('.chapter'); if(art){updateScore(art)}
      if(box.closest('#pc-box')){$('#pc-next').hidden=false;pcStats()}}
    if(hintsOn){linkify(why,false)}
  }
  function resetQz(box){
    box.classList.remove('done');
    $$('.qz-o',box).forEach(function(o){o.classList.remove('right','wrong');o.setAttribute('aria-pressed','false')});
    $('.qz-why',box).hidden=true; $('.qz-reset',box).hidden=true; $('.qz-check',box).hidden=true;
  }
  document.addEventListener('click',function(e){
    var o=e.target.closest('.qz-o');
    if(o){var box=o.closest('.qz'); if(box.classList.contains('done')){return}
      var c=corr(box);
      if(c.length===1){showQz(box,[+o.dataset.i],true);return}
      o.setAttribute('aria-pressed',o.getAttribute('aria-pressed')==='true'?'false':'true');
      var sel=$$('.qz-o[aria-pressed="true"]',box);
      if(sel.length>c.length){sel[0].setAttribute('aria-pressed','false')}
      var btn=$('.qz-check',box); btn.hidden=false; btn.disabled=$$('.qz-o[aria-pressed="true"]',box).length!==c.length;
      return}
    var ch=e.target.closest('.qz-check');
    if(ch){var bx=ch.closest('.qz');showQz(bx,$$('.qz-o[aria-pressed="true"]',bx).map(function(x){return +x.dataset.i}),true);return}
    var rs=e.target.closest('.qz-reset'); if(rs){resetQz(rs.closest('.qz'))}
  });

  /* прогрес читання */
  var posT=null, topBtn=$('#to-top');
  function onScroll(){
    topBtn.classList.toggle('show',window.scrollY>700);
    if(curView!=='ch'||!openId){return}
    var h=document.documentElement.scrollHeight-innerHeight, p=h>0?Math.min(1,window.scrollY/h):0;
    readbar.style.width=(p*100)+'%';
    clearTimeout(posT); var id=openId;
    posT=setTimeout(function(){pos[id]=Math.round(p*1000)/1000;store.set('pos',pos)},500);
  }
  window.addEventListener('scroll',onScroll,{passive:true});
  topBtn.addEventListener('click',function(){window.scrollTo({top:0})});

  /* ---------- пошук ---------- */
  var SEL='h2,h3,h4,p,li,td,figcaption,.qz-q,summary';
  var sIndex=null, sInput=$('#q'), sTimer=null, prevHash='#home';
  function buildIndex(){
    sIndex=[];
    CH.forEach(function(c){var t=tpl(c.id);if(!t){return}var b=t.querySelector('.ch-body');
      $$(SEL,b).forEach(function(el,i){var s=el.textContent.replace(/\s+/g,' ').trim();if(s){sIndex.push({c:c.id,i:i,s:s,l:s.toLowerCase()})}})});
  }
  function doSearch(){
    var q=sInput.value.trim().toLowerCase();
    if(q.length<2){if(curView==='search'){location.hash=prevHash;route()}return}
    if(!sIndex){buildIndex()}
    if(curView!=='search'){prevHash=location.hash||'#home'}
    showView('search'); window.scrollTo(0,0);
    var hits=[], per={};
    for(var k=0;k<sIndex.length&&hits.length<80;k++){var it=sIndex[k];
      if(it.l.indexOf(q)>=0){per[it.c]=(per[it.c]||0)+1;if(per[it.c]<=4){hits.push(it)}}}
    var total=sIndex.filter(function(it){return it.l.indexOf(q)>=0}).length;
    $('#sr-info').textContent=total?('Знайдено: '+total+(total>hits.length?' (показано '+hits.length+')':'')):'Нічого не знайдено. Спробуй іншу форму слова або назву сервісу англійською.';
    var rx=new RegExp('('+q.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')+')','gi');
    $('#sr-list').innerHTML=hits.map(function(it){var c=CMAP[it.c], s=it.s, k=it.l.indexOf(q), a=Math.max(0,k-80);
      var snip=(a>0?'…':'')+s.slice(a,k+q.length+140)+(k+q.length+140<s.length?'…':'');
      return '<a class="sr" href="#ch/'+it.c+'/b'+it.i+'"><b>'+c.n+'. '+esc(c.emoji+' '+c.title)+'</b>'+esc(snip).replace(rx,'<mark>$1</mark>')+'</a>'}).join('');
  }
  sInput.addEventListener('input',function(){clearTimeout(sTimer);sTimer=setTimeout(doSearch,250)});
  sInput.addEventListener('keydown',function(e){if(e.key==='Enter'){clearTimeout(sTimer);doSearch()}});

  /* ---------- практика: перевір себе ---------- */
  var pcPool=null, pcCur=null, pcLast=null;
  function pcBuild(){pcPool=[];CH.forEach(function(c){var t=tpl(c.id);if(!t){return}$$('.qz',t).forEach(function(q){pcPool.push({q:q.dataset.q,c:c.id,node:q})})})}
  function fillScope(sel){
    if(sel.options.length>1){return}
    MODS.forEach(function(m,i){var o=document.createElement('option');o.value='m:'+m;o.textContent='Модуль '+i+' · '+m;sel.appendChild(o)});
    CH.forEach(function(c){var o=document.createElement('option');o.value='c:'+c.id;o.textContent=c.n+'. '+c.title;sel.appendChild(o)});
  }
  function inScope(cid,scope){if(scope==='all'){return true}if(scope.indexOf('m:')===0){return CMAP[cid].module===scope.slice(2)}return cid===scope.slice(2)}
  function pcFiltered(){var sc=$('#pc-scope').value, f=$('#pc-filter').value;
    return pcPool.filter(function(it){if(!inScope(it.c,sc)){return false}var r=qres[it.q];
      if(f==='new'){return !r}if(f==='wrong'){return r&&!r.ok}return true})}
  function pcStats(){
    var list=pcPool.filter(function(it){return inScope(it.c,$('#pc-scope').value)});
    var ok=0,ans=0; list.forEach(function(it){var r=qres[it.q];if(r){ans++;if(r.ok){ok++}}});
    $('#pc-stats').textContent='У цьому наборі: '+list.length+' питань · з відповіддю '+ans+' · правильно '+ok+' · помилок '+(ans-ok)+'.';
  }
  function pcNext(){
    if(!pcPool){pcBuild()}
    var list=pcFiltered(), box=$('#pc-box');
    $('#pc-next').hidden=true;
    if(!list.length){box.innerHTML='<p class="muted">У цьому наборі питань немає 🎉 Обери інший розділ або фільтр.</p>';$('#pc-src').innerHTML='';pcStats();return}
    var it, tries=0; do{it=list[Math.floor(Math.random()*list.length)];tries++}while(list.length>1&&pcLast&&it.q===pcLast&&tries<12);
    pcCur=it; pcLast=it.q;
    var node=it.node.cloneNode(true); node.removeAttribute('id'); box.innerHTML=''; box.appendChild(node);
    var c=CMAP[it.c];
    $('#pc-src').innerHTML='З розділу <a href="#ch/'+c.id+'/q-'+it.q+'">'+c.n+'. '+esc(c.emoji+' '+c.title)+'</a>';
    if(hintsOn){linkify($('.qz-q',node),false)}
    pcStats();
  }
  $('#pc-next').addEventListener('click',function(){pcNext();window.scrollTo({top:0})});
  $('#pc-scope').addEventListener('change',pcNext); $('#pc-filter').addEventListener('change',pcNext);
  $('#pc-reset').addEventListener('click',function(){ask('Скинути всі відповіді «Перевір себе»?',function(){qres={};store.set('q',qres);pcNext()})});

  /* ---------- практика: картки-тригери ---------- */
  var cards=obj(store.get('cards',{})), trgs=null, cardsTotal=0, fcCur=null, fcLast=null, fcs={k:0,u:0};
  function fcBuild(){trgs=[];CH.forEach(function(c){var t=tpl(c.id);if(!t){return}
    $$('li.trg',t).forEach(function(li){trgs.push({id:li.dataset.id,q:li.querySelector('.q').textContent.trim(),a:li.querySelector('.ans').innerHTML,c:c.id})})});
    cardsTotal=trgs.length}
  function cardsKnown(){if(!trgs){fcBuild()}return trgs.filter(function(t){return cards[t.id]&&cards[t.id].l==='k'}).length}
  function fcPool(){var s=$('#fc-scope').value,w=$('#fc-weak').checked;
    return trgs.filter(function(t){return inScope(t.c,s)&&(!w||(cards[t.id]&&cards[t.id].l==='u'))})}
  function fcStats(){
    var known=cardsKnown(), weak=trgs.filter(function(t){return cards[t.id]&&cards[t.id].l==='u'}).length;
    $('#fc-stats').textContent='Зараз: ✓ '+fcs.k+' · ✗ '+fcs.u+'   |   Усього знаєш: '+known+' з '+trgs.length+' · слабких: '+weak;
  }
  function fcNext(){
    if(!trgs){fcBuild()}
    var pool=fcPool();
    if(!pool.length){fcCur=null;$('#fc-sec').textContent='';
      $('#fc-q').textContent=$('#fc-weak').checked?'Слабких карток немає 🎉 Зніми галочку «Лише слабкі».':'У цьому наборі немає карток.';
      $('#fc-a').hidden=true;$('#fc-show').hidden=true;$('#fc-know').hidden=true;$('#fc-dont').hidden=true;fcStats();return}
    var weak=pool.filter(function(t){var st=cards[t.id];return !st||st.l==='u'});
    var from=(weak.length&&Math.random()<0.6)?weak:pool, c, tries=0;
    do{c=from[Math.floor(Math.random()*from.length)];tries++}while(from.length>1&&fcLast&&c.id===fcLast.id&&tries<12);
    fcCur=c;fcLast=c; var ch=CMAP[c.c];
    $('#fc-sec').textContent=ch.n+'. '+ch.title; $('#fc-q').textContent=c.q; linkify($('#fc-q'),false);
    $('#fc-q').dataset.linked='';
    $('#fc-a').innerHTML=c.a; $('#fc-a').hidden=true;
    $('#fc-show').hidden=false;$('#fc-know').hidden=true;$('#fc-dont').hidden=true;fcStats();
  }
  function fcShow(){if(!fcCur){return}$('#fc-a').hidden=false;$('#fc-a').dataset.linked='';linkify($('#fc-a'),false);$('#fc-show').hidden=true;$('#fc-know').hidden=false;$('#fc-dont').hidden=false}
  function fcMark(ok){if(!fcCur){return}var st=cards[fcCur.id]||{k:0,u:0};if(ok){st.k++}else{st.u++}st.l=ok?'k':'u';
    cards[fcCur.id]=st;store.set('cards',cards);if(ok){fcs.k++}else{fcs.u++}fcNext()}
  $('#fc-show').addEventListener('click',fcShow);
  $('#fc-know').addEventListener('click',function(){fcMark(true)});
  $('#fc-dont').addEventListener('click',function(){fcMark(false)});
  $('#fc-scope').addEventListener('change',fcNext); $('#fc-weak').addEventListener('change',fcNext);
  $('#fc-reset').addEventListener('click',function(){ask('Скинути статистику карток?',function(){cards={};store.set('cards',cards);fcs={k:0,u:0};fcNext()})});
  document.addEventListener('keydown',function(e){
    if(curView!=='practice'||$('#pr-cards').hidden||!overlay.hidden||!$('#ask').hidden||e.target.closest('input,select,textarea,button')){return}
    if((e.key===' '||e.key==='Enter')&&!$('#fc-show').hidden){e.preventDefault();fcShow()}
    else if(e.key==='ArrowRight'&&!$('#fc-know').hidden){fcMark(true)}
    else if(e.key==='ArrowLeft'&&!$('#fc-dont').hidden){fcMark(false)}
  });

  /* ---------- практика: пробний іспит ---------- */
  var QS=JSON.parse($('#qdata').textContent), QMAP={};
  QS.forEach(function(q){QMAP[q.id]=q});
  var DOM={secure:'Безпека',resilient:'Відмовостійкість',performance:'Продуктивність',cost:'Вартість'};
  var ts=store.get('test',null); if(ts&&(!ts.ids||!ts.ids.every(function(id){return QMAP[id]}))){ts=null}
  var thist=arr(store.get('testHistory',[])), twrong=arr(store.get('testWrong',[]));
  var showUa=!!store.get('qUa',false), tick=null;
  function L(i){return String.fromCharCode(65+i)}
  function tsave(){store.set('test',ts)}
  function right(q,a){a=(a||[]).slice().sort();var c=q.correct.slice().sort();if(a.length!==c.length){return false}
    for(var i=0;i<a.length;i++){if(a[i]!==c[i]){return false}}return true}
  function markWrong(q,ok){var k=twrong.indexOf(q.id);if(ok&&k>=0){twrong.splice(k,1)}if(!ok&&k<0){twrong.push(q.id)}store.set('testWrong',twrong)}
  function panel(id){['#t-start','#t-run','#t-result'].forEach(function(p){$(p).hidden=(p!==id)})}
  var SETS=JSON.parse($('#setdata').textContent);
  function fillSets(){var sel=$('#t-set'),keep=sel.value;sel.innerHTML='';
    function add(v,t){var o=document.createElement('option');o.value=v;o.textContent=t;sel.appendChild(o)}
    SETS.forEach(function(s){add('set:'+s.p,s.name+' ('+QS.filter(function(q){return q.id.indexOf(s.p)===0}).length+')')});
    add('all','Усі питання ('+QS.length+')');
    Object.keys(DOM).forEach(function(d){add(d,DOM[d]+' ('+QS.filter(function(q){return q.domain===d}).length+')')});
    add('wrong','Мої помилки ('+twrong.length+')'); if(keep){sel.value=keep}}
  function bestFull(){return thist.filter(function(x){return x.n>=65}).reduce(function(m,x){return Math.max(m,x.pct)},-1)}
  function renderStart(){
    fillSets(); $('#t-msg').textContent='';
    var r=$('#t-resume');
    if(ts&&!ts.done){r.hidden=false;r.textContent='▶ Продовжити ('+(ts.idx+1)+' / '+ts.ids.length+')'}else{r.hidden=true}
    var h=$('#t-history');
    if(!thist.length){h.innerHTML='<p class="muted">Ще немає результатів. Почни з режиму «Тренування».</p>'}
    else{var b=bestFull();
      h.innerHTML=(b>=0?'<p><b>Найкращий повний іспит: '+b+'%</b></p>':'')+'<p class="muted">Останні спроби:</p><ul class="t-hist">'+
        thist.slice(-6).reverse().map(function(x){return '<li>'+esc(x.date)+' · '+(x.mode==='exam'?'Іспит':'Тренування')+' · '+x.ok+' / '+x.n+' ('+x.pct+'%)</li>'}).join('')+'</ul>'}
    panel('#t-start');
  }
  function begin(){
    var mode=$('input[name="t-mode"]:checked').value, set=$('#t-set').value;
    var ids=QS.filter(function(q){if(set==='all'){return true}if(set==='wrong'){return twrong.indexOf(q.id)>=0}
      if(set.indexOf('set:')===0){return q.id.indexOf(set.slice(4))===0}return q.domain===set}).map(function(q){return q.id});
    if(!ids.length){$('#t-msg').textContent='У цьому наборі поки немає питань.';return}
    if($('#t-shuffle').checked){shuffle(ids)}
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
      linkify(why,false)}
    else{why.hidden=true}
    $('#t-flag').hidden=!exam; $('#t-flag').setAttribute('aria-pressed',ts.flag[q.id]?'true':'false');
    $('#t-prev').hidden=!exam||ts.idx===0;
    $('#t-check').hidden=exam||checked; $('#t-check').disabled=!a.length;
    $('#t-next').hidden=last||(!exam&&!checked);
    $('#t-finish').textContent=exam?'Завершити іспит':(checked&&last?'Показати результат':'Завершити');
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
    if(!force&&exam&&answered<ts.ids.length){ask('Без відповіді: '+(ts.ids.length-answered)+'. Завершити іспит?',function(){finish(true)});return}
    stopTick();
    var ids=exam?ts.ids:ts.ids.filter(function(id){return ts.chk[id]});
    if(!ids.length){ts=null;tsave();renderStart();return}
    var ok=0,dom={};
    ids.forEach(function(id){var q=QMAP[id],r=right(q,ts.ans[id]),d=dom[q.domain]||(dom[q.domain]={n:0,ok:0});d.n++;if(r){ok++;d.ok++}if(exam&&(ts.ans[id]||[]).length){markWrong(q,r)}});
    var pct=Math.round(ok*100/ids.length), secs=Math.round((Date.now()-ts.start)/1000), dt=new Date();
    thist.push({date:dt.toLocaleDateString('uk-UA')+' '+dt.toLocaleTimeString('uk-UA',{hour:'2-digit',minute:'2-digit'}),mode:ts.mode,n:ids.length,ok:ok,pct:pct});
    if(thist.length>30){thist=thist.slice(-30)} store.set('testHistory',thist);
    ts.done=true; ts.result={ids:ids,ok:ok,pct:pct,dom:dom,secs:secs}; tsave(); renderResult();
  }
  function renderResult(){
    var r=ts.result;
    $('#t-score').textContent=r.ok+' / '+r.ids.length+' · '+r.pct+'%';
    var bar=$('#t-bar'); bar.style.width=r.pct+'%'; bar.className=r.pct>=80?'ok':(r.pct>=70?'mid':'bad');
    $('#t-verdict').textContent=r.pct>=80?'🎉 Відмінно! Стабільно 80%+ — можна записуватися на іспит.':(r.pct>=70?'👍 Майже. Повтори слабкі домени й розбери помилки.':'📚 Ще потренуйся: розбери помилки й повтори відповідні розділи.');
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
    $('#t-review').innerHTML=out||'<p>Помилок немає 🎉</p>'; $('#t-review').dataset.linked=''; linkify($('#t-review'),false);
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
  $('#t-lang').addEventListener('click',function(){showUa=!showUa;store.set('qUa',showUa);renderQ()});
  $('#t-review-all').addEventListener('click',function(){review(false)});
  $('#t-review-wrong').addEventListener('click',function(){review(true)});
  $('#t-new').addEventListener('click',function(){renderStart();window.scrollTo({top:0})});
  $('#t-retry').addEventListener('click',function(){renderStart();$('#t-set').value='wrong';window.scrollTo({top:0})});

  var prMode=null;
  function openPractice(m){
    if(['check','cards','exam'].indexOf(m)<0){m='check'}
    prMode=m;
    $$('#view-practice .seg a').forEach(function(a){a.setAttribute('aria-current',a.dataset.m===m?'page':'false')});
    $('#pr-check').hidden=m!=='check'; $('#pr-cards').hidden=m!=='cards'; $('#pr-exam').hidden=m!=='exam';
    if(m==='check'){fillScope($('#pc-scope'));if(!pcCur){pcNext()}else{pcStats()}}
    if(m==='cards'){fillScope($('#fc-scope'));if(!fcCur){fcNext()}}
    if(m==='exam'&&$('#t-run').hidden&&$('#t-result').hidden){renderStart()}
    if(m==='exam'&&!$('#t-run').hidden&&ts&&!ts.done){startTick()}
  }

  /* ---------- словник ---------- */
  var sq=$('#svc-q'), scat='all', catBox=$('#svc-cats'), dirReady=false;
  function sortKey(s){var n=/^[А-ЯҐЄІЇа-яґєії]/.test(s.name)&&s.aliases.length&&s.cat!=='it'?s.aliases[0]:s.name;return n.replace(/^(Amazon|AWS)\s+/,'').toLowerCase()}
  function renderDir(){
    if(!dirReady){dirReady=true;
      SVC.forEach(function(s){s.q=(s.name+' '+s.aliases.join(' ')+' '+txt(s.what)+' '+txt(s.image)).toLowerCase()});
      var keys=Object.keys(CATS).filter(function(k){return SVC.some(function(s){return s.cat===k})});
      catBox.innerHTML='<button class="cat-chip" type="button" data-cat="all" aria-pressed="true">Усі</button>'+
        keys.map(function(k){return '<button class="cat-chip" type="button" data-cat="'+k+'" aria-pressed="false">'+esc(CATS[k])+'</button>'}).join('')}
    var q=sq.value.trim().toLowerCase();
    var list=SVC.filter(function(s){return (scat==='all'||s.cat===scat)&&(!q||s.q.indexOf(q)>=0)});
    list.sort(function(a,b){return sortKey(a).localeCompare(sortKey(b),'uk')});
    $('#svc-grid').innerHTML=list.map(function(s){return '<button class="svc-item" type="button" data-open="'+s.id+'"><span class="svc-e">'+s.emoji+'</span><span><b>'+esc(s.name)+'</b><small>'+esc(txt(s.what))+'</small></span></button>'}).join('')||'<p class="muted">Нічого не знайдено.</p>';
    $('#svc-count').textContent='Показано: '+list.length+' з '+SVC.length;
  }
  catBox.addEventListener('click',function(e){var b=e.target.closest('[data-cat]');if(!b){return}scat=b.dataset.cat;
    $$('.cat-chip',catBox).forEach(function(c){c.setAttribute('aria-pressed',c===b?'true':'false')});renderDir()});
  sq.addEventListener('input',renderDir);
  $('#svc-grid').addEventListener('click',function(e){var b=e.target.closest('[data-open]');if(b){openCard(b.dataset.open)}});

  /* ---------- схеми ---------- */
  var galReady=false;
  function renderGallery(){
    if(galReady){return} galReady=true;
    var gal=$('#dg-gallery'), frag=document.createDocumentFragment();
    CH.forEach(function(c){var t=tpl(c.id);if(!t){return}
      $$('figure.diagram',t).forEach(function(fig){
        var wrap=document.createElement('div'); wrap.className='dg-item';
        var h=document.createElement('h2'); h.textContent=fig.dataset.caption||'';
        var clone=fig.cloneNode(true), fid=clone.id; clone.removeAttribute('id');
        var a=document.createElement('a'); a.className='dg-link'; a.href='#ch/'+c.id+'/'+fid.split('--')[1];
        a.textContent='До розділу '+c.n+': '+c.emoji+' '+c.title+' →';
        wrap.appendChild(h); wrap.appendChild(clone); wrap.appendChild(a); frag.appendChild(wrap);
      })});
    gal.appendChild(frag); linkify(gal,false);
  }

  /* ---------- маршрути ---------- */
  function route(){
    var h=decodeURIComponent(location.hash.slice(1)), p=h.split('/');
    if(p[0]==='ch'&&CMAP[p[1]]){showView('ch');openChapter(p[1],p[2]);return}
    if(p[0]==='practice'){showView('practice');openPractice(p[1]);window.scrollTo(0,0);return}
    if(p[0]==='glossary'){showView('glossary');renderDir();window.scrollTo(0,0);if(p[1]&&SMAP[p[1]]){openCard(p[1])}return}
    if(p[0]==='diagrams'){showView('diagrams');renderGallery();window.scrollTo(0,0);return}
    showView('home'); renderHome(); window.scrollTo(0,0);
  }
  window.addEventListener('hashchange',route);
  $$('.tab').forEach(function(t){t.addEventListener('click',function(e){
    if(location.hash===t.getAttribute('href')){e.preventDefault();route()}})});

  body.classList.toggle('hints-on',hintsOn); hb.setAttribute('aria-pressed',hintsOn?'true':'false');
  route();

  if('serviceWorker' in navigator&&(location.protocol==='https:'||location.hostname==='localhost'||location.hostname==='127.0.0.1')){
    window.addEventListener('load',function(){navigator.serviceWorker.register('sw.js').catch(function(){})});
    navigator.serviceWorker.ready.then(function(){$('#offline-ok').hidden=false}).catch(function(){});
  }
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

# ---------- Шаблони ----------

DISCLAIMER = ("Незалежний навчальний підручник. Не пов'язаний з Amazon Web Services і не схвалений AWS. "
              "AWS і назви сервісів — торговельні марки Amazon.com, Inc. або її афілійованих осіб. "
              "Практичні питання — оригінальні, це не реальні питання іспиту. «Хмаринка» — вигадана компанія.")

PAGE = """<!DOCTYPE html>
<html lang="uk">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>AWS SAA-C03 з нуля — глибоке навчання</title>
<meta name="description" content="Глибокий курс-підручник українською до іспиту AWS Certified Solutions Architect – Associate (SAA-C03): з нуля до архітектора, з історіями, образами, схемами, практикою в AWS, питаннями і пробним іспитом.">
<meta name="theme-color" content="#0f766e">
%%HEAD_EXTRA%%
<style>%%CSS%%</style>
</head>
<body data-view="home">
<div class="readbar" id="readbar" hidden></div>
<a class="skip" href="#main">До змісту</a>
<header class="topbar">
  <div class="topbar-inner">
    <a class="brand" href="#home">SAA-C03 <span class="brand-sub">з нуля · глибоко</span></a>
    <label class="search"><span aria-hidden="true">🔍</span><input id="q" type="search" placeholder="Пошук у курсі: NAT, RPO, Glacier…" autocomplete="off" aria-label="Пошук у курсі"></label>
    <div class="actions">
      <button class="tb-btn" id="btn-hints" type="button" aria-pressed="true" title="Підказки: торкнись або виділи назву сервісу чи термін, щоб побачити пояснення">🤖<span class="lbl"> Підказки</span></button>
      <button class="tb-btn icon" id="btn-font" type="button" aria-label="Розмір шрифту" title="Розмір шрифту">Aa</button>
      <a class="tb-btn" href="%%PDF%%" download title="Завантажити підручник у PDF">⬇<span class="lbl"> PDF</span></a>
      <button class="tb-btn icon" id="btn-theme" type="button" aria-label="Світла або темна тема" title="Світла / темна тема">🌓</button>
    </div>
  </div>
  <nav class="tabs" aria-label="Розділи сайту">
    <a class="tab" href="#home" data-tab="home"><span class="ti">🎓</span><span>Курс</span></a>
    <a class="tab" href="#practice/check" data-tab="practice"><span class="ti">🎯</span><span>Практика</span></a>
    <a class="tab" href="#glossary" data-tab="glossary"><span class="ti">📚</span><span>Словник</span></a>
    <a class="tab" href="#diagrams" data-tab="diagrams"><span class="ti">🗺️</span><span>Схеми</span></a>
  </nav>
</header>

<div class="view" id="view-home" data-view="home">
  <main class="page" id="main">
%%HOME%%
  </main>
</div>

<div class="view" id="view-ch" data-view="ch" hidden>
  <main class="page"><div id="reader"></div></main>
</div>

<div class="view" id="view-search" data-view="search" hidden>
  <main class="page">
    <h1>🔍 Пошук у курсі</h1>
    <p class="muted" id="sr-info"></p>
    <div id="sr-list"></div>
  </main>
</div>

<div class="view" id="view-practice" data-view="practice" hidden>
  <main class="page">
    <nav class="seg" aria-label="Режим практики"><a href="#practice/check" data-m="check">✅ Перевір себе</a><a href="#practice/cards" data-m="cards">🎴 Картки</a><a href="#practice/exam" data-m="exam">📝 Пробний іспит</a></nav>
    <div id="pr-check">
      <h1>✅ Перевір себе</h1>
      <p class="sub">%%NQ%% питань з розділів у стилі іспиту, з поясненнями. Обери модуль або розділ, відповідай і читай пояснення — особливо там, де помилився.</p>
      <section class="card">
        <div class="qz-row"><select id="pc-scope" aria-label="Набір питань"><option value="all">Усі розділи</option></select>
          <select id="pc-filter" aria-label="Фільтр"><option value="all">Усі питання</option><option value="new">Ще без відповіді</option><option value="wrong">Лише мої помилки</option></select></div>
        <p class="pc-src" id="pc-src"></p>
        <div id="pc-box"></div>
        <div class="qz-row" style="margin-top:10px"><button class="tb-btn primary" id="pc-next" type="button" hidden>Наступне питання →</button></div>
        <p class="pc-stats" id="pc-stats"></p>
      </section>
      <p class="fc-hint"><button class="linkbtn" id="pc-reset" type="button">Скинути всі відповіді</button></p>
    </div>
    <div id="pr-cards" hidden>
      <h1>🎴 Картки-тригери</h1>
      <p class="sub">Тригери з розділів: «бачиш у питанні → обираєш». Спершу відповідай подумки, потім відкривай. Картки з позначкою «Не знаю» повертаються частіше.</p>
      <section class="card">
        <div class="qz-row"><select id="fc-scope" aria-label="Набір карток"><option value="all">Усі розділи</option></select>
          <label class="chk"><input type="checkbox" id="fc-weak"> Лише слабкі</label></div>
        <div class="fc-sec" id="fc-sec"></div>
        <div class="fc-q" id="fc-q"></div>
        <div class="fc-a" id="fc-a" hidden></div>
        <div class="fc-actions">
          <button class="tb-btn primary" id="fc-show" type="button">Показати відповідь</button>
          <button class="tb-btn ok" id="fc-know" type="button" hidden>✓ Знаю</button>
          <button class="tb-btn bad" id="fc-dont" type="button" hidden>✗ Не знаю</button>
        </div>
        <div class="pc-stats" id="fc-stats"></div>
      </section>
      <p class="fc-hint"><kbd>Клавіші: пробіл — показати, → знаю, ← не знаю.</kbd> <button class="linkbtn" id="fc-reset" type="button">Скинути статистику карток</button></p>
    </div>
    <div id="pr-exam" hidden>
      <h1>📝 Пробний іспит</h1>
      <p class="sub">%%NT%% оригінальних питань у стилі SAA-C03 (не реальні питання іспиту). Англійською, як на іспиті, з перекладом і поясненнями українською. Мета — стабільно 80%+.</p>
      <section class="card" id="t-start">
        <h2>Новий іспит</h2>
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
          <button class="tb-btn primary" id="t-new" type="button">Новий іспит</button>
        </div>
        <div id="t-review"></div>
      </section>
    </div>
  </main>
</div>

<div class="view" id="view-glossary" data-view="glossary" hidden>
  <main class="page">
    <h1>📚 Словник: сервіси AWS і основи IT</h1>
    <p class="sub">Що це, образ, коли обирати, як питають на іспиті і з чим не плутати. Категорія «Основи IT» — терміни для тих, хто починає з нуля.</p>
    <label class="search wide"><span aria-hidden="true">🔍</span><input id="svc-q" type="search" placeholder="Назва або задача: черга, кеш, DNS, порт, архів…" autocomplete="off" aria-label="Пошук у словнику"></label>
    <div class="cat-chips" id="svc-cats"></div>
    <p class="muted" id="svc-count"></p>
    <div class="svc-grid" id="svc-grid"></div>
  </main>
</div>

<div class="view" id="view-diagrams" data-view="diagrams" hidden>
  <main class="page">
    <h1>🗺️ Схеми</h1>
    <p class="sub">Усі схеми курсу в одному місці — зручно для повторення. Під кожною — посилання на розділ.</p>
    <div id="dg-gallery"></div>
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
<div id="tpls" hidden>
%%TEMPLATES%%
</div>
<script id="chdata" type="application/json">%%CHDATA%%</script>
<script id="sdata" type="application/json">%%SDATA%%</script>
<script id="cdata" type="application/json">%%CDATA%%</script>
<script id="qdata" type="application/json">%%QDATA%%</script>
<script id="setdata" type="application/json">%%SETDATA%%</script>
<script>%%JS%%</script>
</body>
</html>
"""


def dom_chips(doms):
    if not doms:
        return ""
    return '<div class="ch-doms">' + "".join(
        f'<span>🎯 {DOMAINS[d]} · {DOMAIN_PCT[d]}%</span>' for d in doms) + "</div>"


def chapter_article(c, total, prev_c, next_c, print_mode=False):
    toc = "".join(f'<li><a href="#ch/{c["id"]}/{a}">{inline(t)}</a></li>' for a, t in c["toc"])
    toc_html = f'<details class="ch-toc"><summary>📑 Зміст розділу ({len(c["toc"])})</summary><ol>{toc}</ol></details>' if c["toc"] else ""
    nav = '<div class="ch-nav">'
    nav += (f'<a class="tb-btn" href="#ch/{prev_c["id"]}">← {prev_c["n"]}. {inline(prev_c["short"])}</a>' if prev_c
            else '<a class="tb-btn" href="#home">← Усі розділи</a>')
    nav += f'<button class="tb-btn done-btn" data-id="{c["id"]}" type="button" aria-pressed="false">☐ Позначити пройденим</button>'
    nav += (f'<a class="tb-btn primary" href="#ch/{next_c["id"]}">Далі: {next_c["n"]}. {inline(next_c["short"])} →</a>' if next_c
            else '<a class="tb-btn primary" href="#practice/exam">📝 До пробного іспиту →</a>')
    nav += "</div>"
    info = []
    if c["q"]:
        info.append(plural(c["q"], "питання", "питання", "питань"))
    if c["labs"]:
        info.append("практика в AWS")
    meta = f'{html.escape(c["module"])} · розділ {c["n"]} з {total} · ⏱ ~{c["minutes"]} хв'
    art_id = f' id="ch-{c["id"]}"' if print_mode else ""
    return (f'<article class="chapter"{art_id} data-id="{c["id"]}" data-title="{html.escape(c["title"], quote=True)}">'
            f'<div class="ch-top"><a class="back" href="#home">← Усі розділи</a><span class="meta">{meta}</span></div>'
            f'<h1 class="ch-title"><span class="le">{c["emoji"]}</span><span>{inline(c["title"])}</span></h1>'
            f'{dom_chips(c["domains"])}{toc_html}<div class="ch-body">{c["html"]}</div>'
            f'<p class="ch-score"></p>{nav}</article>')


def build_home(chapters, services, n_tq, n_sets=1):
    modules, cards = [], {}
    for c in chapters:
        if c["module"] not in cards:
            modules.append(c["module"])
            cards[c["module"]] = []
        cards[c["module"]].append(
            f'<a class="lesson-card" href="#ch/{c["id"]}" data-id="{c["id"]}"><span class="le">{c["emoji"]}</span>'
            f'<span><span class="ln">Розділ {c["n"]} · ⏱ ~{c["minutes"]} хв</span><span class="lt">{inline(c["title"])}</span>'
            f'<span class="ls"></span></span></a>')
    mods = "".join(f'<section class="module"><h2>Модуль {k} · {html.escape(m)}</h2><div class="lesson-grid">{"".join(cards[m])}</div></section>'
                   for k, m in enumerate(modules))
    hours = sum(c["minutes"] for c in chapters) / 60
    n_q = sum(c["q"] for c in chapters)
    n_trg = sum(c["trg"] for c in chapters)
    n_fig = sum(c["figs"] for c in chapters)
    n_lab = sum(1 for c in chapters if c["labs"])
    n_it = sum(1 for s in services if s["cat"] == "it")
    n_ex = "пробний іспит" if n_sets == 1 else f"{n_sets} пробні іспити"
    return (f'<header class="hero"><h1>🎓 AWS Solutions Architect з нуля: глибоке навчання</h1>'
            f'<p class="sub">Підручник до іспиту <b>SAA-C03</b> для тих, хто починає з нуля: від «що таке сервер» до архітектури, '
            f'яку не соромно показати на співбесіді. Кожен розділ — історія компанії «Хмаринка», образ, глибоке пояснення, схеми, '
            f'практика в справжньому AWS, тригери іспиту, пастки і питання для самоперевірки.</p>'
            f'<div class="chips"><span>{plural(len(chapters), "розділ", "розділи", "розділів")}</span><span>~{round(hours)} год навчання</span>'
            f'<span>{plural(n_q, "питання", "питання", "питань")} «Перевір себе»</span><span>{plural(n_trg, "картка-тригер", "картки-тригери", "карток-тригерів")}</span>'
            f'<span>{plural(n_fig, "схема", "схеми", "схем")}</span><span>{plural(n_lab, "практика", "практики", "практик")} в AWS</span>'
            f'<span>{n_ex} · {plural(n_tq, "питання", "питання", "питань")}</span></div>'
            f'<div class="progress-card"><div class="bar"><span id="home-bar"></span></div><p id="home-progress"></p>'
            f'<a class="tb-btn primary" id="home-continue" href="#ch/{chapters[0]["id"]}">▶ Почати</a></div>'
            f'<div class="stats" id="home-stats"></div>'
            f'<div class="install-card" id="install-card" hidden><span>📲 <b>Встанови як застосунок</b> — відкриватиметься з головного екрана '
            f'і працюватиме без інтернету.</span><button class="tb-btn primary" id="btn-install" type="button" hidden>Встановити</button>'
            f'<span class="muted" id="install-ios" hidden>iPhone: Safari → «Поділитися» → «На початковий екран».</span></div>'
            f'<p class="offline-ok" id="offline-ok" hidden>✓ Курс збережено на цьому пристрої — відкривається і без інтернету.</p>'
            f'<p class="how">🤖 <b>Підказки:</b> торкнись підкресленого терміна або виділи слово пальцем — з\'явиться пояснення: '
            f'{plural(len(services) - n_it, "сервіс і поняття AWS", "сервіси і поняття AWS", "сервісів і понять AWS")} та '
            f'{plural(n_it, "термін", "терміни", "термінів")} з основ IT. Кнопка <b>Aa</b> змінює розмір шрифту, 🌓 — тему.</p>'
            f'<p class="also">📘 Потрібне швидке повторення? Є окремий сайт — <a href="../">коротка шпаргалка і курс-експрес</a>.</p>'
            f'</header>{mods}<p class="disclaimer">{DISCLAIMER} Оновлено {UPDATED}.</p>')


def build_site(chapters, services, questions, sets, head_extra, pdf_href):
    total = len(chapters)
    tpls = []
    for i, c in enumerate(chapters):
        prev_c = chapters[i - 1] if i > 0 else None
        next_c = chapters[i + 1] if i + 1 < total else None
        tpls.append(f'<template id="tpl-{c["id"]}">{chapter_article(c, total, prev_c, next_c)}</template>')
    chdata = [{"id": c["id"], "title": c["title"], "emoji": c["emoji"], "module": c["module"], "q": c["q"]} for c in chapters]
    page = PAGE
    for key, val in {
        "%%HEAD_EXTRA%%": head_extra,
        "%%CSS%%": CSS,
        "%%PDF%%": pdf_href,
        "%%HOME%%": build_home(chapters, services, len(questions), len(sets)),
        "%%NQ%%": str(sum(c["q"] for c in chapters)),
        "%%NT%%": str(len(questions)),
        "%%TEMPLATES%%": "\n".join(tpls),
        "%%CHDATA%%": json.dumps(chdata, ensure_ascii=False).replace("</", "<\\/"),
        "%%SDATA%%": json.dumps(services, ensure_ascii=False).replace("</", "<\\/"),
        "%%CDATA%%": json.dumps(CATS, ensure_ascii=False),
        "%%QDATA%%": json.dumps(questions, ensure_ascii=False).replace("</", "<\\/"),
        "%%SETDATA%%": json.dumps(sets, ensure_ascii=False),
        "%%JS%%": JS,
    }.items():
        page = page.replace(key, val)
    return page


def build_print(chapters, services):
    total = len(chapters)
    mods, toc = [], []
    for c in chapters:
        if c["module"] not in mods:
            mods.append(c["module"])
            toc.append(f'<h3>Модуль {len(mods) - 1} · {html.escape(c["module"])}</h3>')
        toc.append(f'<a href="#ch-{c["id"]}"><span class="n">{c["n"]}</span><span>{c["emoji"]} {inline(c["title"])}</span></a>')
    arts = []
    for c in chapters:
        a = chapter_article(c, total, None, None, print_mode=True)
        a = a.replace('<details class="box deep">', '<details class="box deep" open>')
        arts.append(a)
    body = "\n".join(arts)
    # внутрішні посилання → якорі PDF
    body = re.sub(r'href="#ch/([\w-]+)/(q-[\w-]+)"', r'href="#\2"', body)
    body = re.sub(r'href="#ch/([\w-]+)/(f\d+)"', r'href="#\1--\2"', body)
    body = re.sub(r'href="#ch/([\w-]+)/([\w-]+)"', r'href="#\1--\2"', body)
    body = re.sub(r'href="#ch/([\w-]+)"', r'href="#ch-\1"', body)
    body = re.sub(r'href="#(practice|glossary|diagrams|home)[^"]*"', 'href="#"', body)
    n_q = sum(c["q"] for c in chapters)
    cats_order = list(CATS)
    gl = []
    for cat in cats_order:
        items = sorted([s for s in services if s["cat"] == cat], key=lambda s: s["name"].lower())
        if not items:
            continue
        gl.append(f'<p class="cat">{html.escape(CATS[cat])}</p>')
        for s in items:
            gl.append(f'<p>{s["emoji"]} <b>{html.escape(s["name"])}</b> — {s["what"]}</p>')
    cover = (f'<section class="cover"><div class="big">☁️🎓</div><h1>AWS Solutions Architect з нуля: глибоке навчання</h1>'
             f'<p class="sub">Підручник до іспиту AWS Certified Solutions Architect – Associate (SAA-C03).<br>'
             f'{plural(total, "розділ", "розділи", "розділів")} · {plural(n_q, "питання", "питання", "питань")} для самоперевірки з відповідями · '
             f'схеми · практика в AWS.</p><p class="sub">Інтерактивна версія з підказками, картками і пробним іспитом: {SITE_URL}</p>'
             f'<p class="sub">Оновлено {UPDATED}. {DISCLAIMER}</p></section>')
    how = ('<section class="intro-print"><h2>Як читати цей підручник</h2>'
           '<p>Розділи йдуть від простого до складного: спершу основи IT і хмари, потім безпека, мережа, обчислення, сховища, '
           'інтеграція, бази даних, аналітика, моніторинг, надійність і вартість. Наприкінці — велика архітектура, розбір іспиту і план.</p>'
           '<p>У кожному розділі: 🎬 історія «Хмаринки» (навіщо це потрібно), 🖼️ образ (щоб запам\'ятати), пояснення, схеми, '
           '🧪 практика в AWS, 💡 «Запам\'ятай», 🎯 як питають на іспиті, ⚠️ пастки і ✅ питання «Перевір себе» з відповіддю й поясненням '
           'одразу під питанням — спершу прикрий відповідь рукою.</p>'
           '<p>Практика в AWS завжди закінчується прибиранням створених ресурсів. Перед першою практикою прочитай розділ 7 '
           'про безкоштовний план і бюджет.</p></section>')
    body_html = (f'<main>{cover}<nav class="ptoc"><h2>Зміст</h2>{"".join(toc)}</nav>{how}{body}'
                 f'<section class="appendix"><h2>Додаток. Словник сервісів і термінів</h2><div class="gl">{"".join(gl)}</div></section></main>')
    return (f'<!DOCTYPE html><html lang="uk"><head><meta charset="utf-8"><title>AWS SAA-C03 з нуля — підручник</title>'
            f'<style>{CSS}{PRINT_CSS}</style></head><body class="print">{body_html}</body></html>')


# ---------- PWA ----------

ICON_HTML = """<!DOCTYPE html><html><head><meta charset="utf-8"><style>
html,body{{margin:0;width:{w}px;height:{w}px;overflow:hidden}}
body{{background:linear-gradient(145deg,#0f766e 0%,#1e3a8a 100%);display:flex;align-items:center;justify-content:center;font-family:"Segoe UI",Arial,"DejaVu Sans",sans-serif;color:#fff}}
.t{{text-align:center}}
.a{{font-size:{a}px;font-weight:800;line-height:1;letter-spacing:{ls}px}}
.c{{width:{cw}px;height:{ch}px;border-radius:{ch}px;background:#fbbf24;margin:{m1}px auto 0}}
.b{{font-size:{b}px;font-weight:700;line-height:1;margin-top:{m2}px;opacity:.96}}
</style></head><body><div class="t"><div class="a">SAA</div><div class="c"></div><div class="b">з нуля</div></div></body></html>"""

MANIFEST = {
    "name": "AWS SAA-C03 з нуля — глибоке навчання",
    "short_name": "SAA з нуля",
    "description": "Глибокий курс-підручник до AWS Solutions Architect – Associate (SAA-C03) українською: з нуля до архітектора",
    "lang": "uk",
    "id": "./",
    "start_url": "./",
    "scope": "./",
    "display": "standalone",
    "background_color": "#0f1115",
    "theme_color": "#0f766e",
    "icons": [
        {"src": "icons/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
        {"src": "icons/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
        {"src": "icons/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
    ],
}

SW = """// Офлайн-режим глибокого курсу: сторінка — спершу з мережі (щоб бачити оновлення), без мережі — з кешу.
const PREFIX = 'saadeep-';
const CACHE = PREFIX + '%s';
const CORE = ['./', './index.html', './manifest.webmanifest', './icons/icon-192.png', './icons/icon-512.png', './icons/apple-touch-icon.png'];
self.addEventListener('install', e => {
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
  const url = new URL(req.url);
  if (req.method !== 'GET' || url.origin !== location.origin) return;
  const scope = new URL(self.registration.scope);
  if (!url.pathname.startsWith(scope.pathname)) return;
  const isPage = req.mode === 'navigate' && (url.pathname.endsWith('/') || url.pathname.endsWith('.html'));
  if (isPage) {
    e.respondWith(fetch(req).then(res => {
      if (res.ok) { const copy = res.clone(); caches.open(CACHE).then(c => c.put('./index.html', copy)); }
      return res;
    }).catch(() => caches.match('./index.html')));
    return;
  }
  if (url.pathname.endsWith('.pdf')) return;
  e.respondWith(caches.match(req).then(hit => hit || fetch(req).then(res => {
    if (res.ok) { const copy = res.clone(); caches.open(CACHE).then(c => c.put(req, copy)); }
    return res;
  })));
});
"""


def browser_path():
    for b in BROWSERS:
        if pathlib.Path(b).exists():
            return b
    for name in ("chromium", "chromium-browser", "google-chrome", "chrome", "msedge"):
        p = shutil.which(name)
        if p:
            return p
    return None


def run_browser(args, timeout=600):
    browser = browser_path()
    if not browser:
        raise RuntimeError("Chrome/Chromium/Edge не знайдено")
    work = pathlib.Path(tempfile.mkdtemp(prefix="saadeep_"))
    try:
        cmd = [browser, "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
               f"--user-data-dir={work / 'profile'}"]
        if os.name != "nt" and hasattr(os, "geteuid") and os.geteuid() == 0:
            cmd.append("--no-sandbox")
        subprocess.run(cmd + args(work), check=True, timeout=timeout, capture_output=True)
        return work
    except Exception:
        shutil.rmtree(work, ignore_errors=True)
        raise


def print_pdf(url, pdf_paths):
    work = run_browser(lambda w: ["--no-pdf-header-footer", "--generate-pdf-document-outline",
                                  "--virtual-time-budget=30000", f"--print-to-pdf={w / 'out.pdf'}", url])
    try:
        for p in pdf_paths:
            p.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(work / "out.pdf", p)
    finally:
        shutil.rmtree(work, ignore_errors=True)


def render_icon(size, out_path):
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="saadeep_icon_"))
    try:
        page = tmp / "icon.html"
        k = size / 512
        page.write_text(ICON_HTML.format(w=size, a=round(158 * k), ls=round(-2 * k, 1), cw=round(236 * k),
                                         ch=max(2, round(12 * k)), m1=round(20 * k), b=round(74 * k),
                                         m2=round(16 * k)), encoding="utf-8")
        work = run_browser(lambda w: ["--hide-scrollbars", f"--window-size={size},{size}",
                                      f"--screenshot={w / 'shot.png'}", page.as_uri()])
        out_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(work / "shot.png", out_path)
        shutil.rmtree(work, ignore_errors=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    chapters = parse_chapters()
    for i, c in enumerate(chapters, 1):
        c["n"] = i
    services = parse_services(chapters)
    questions = parse_questions(V2 / "questions.md", "q")
    sets = [{"p": "q", "name": "Іспит 1"}]
    if (SRC / "exam2.md").exists():
        questions += parse_questions(SRC / "exam2.md", "e")
        sets.append({"p": "e", "name": "Іспит 2"})
    for c in chapters:
        del c["plain"]

    head_web = ('<meta name="robots" content="noindex, nofollow">\n'
                '<link rel="manifest" href="manifest.webmanifest">\n'
                '<link rel="icon" type="image/png" href="icons/icon-192.png">\n'
                '<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">\n'
                '<meta name="mobile-web-app-capable" content="yes">\n'
                '<meta name="apple-mobile-web-app-capable" content="yes">\n'
                '<meta name="apple-mobile-web-app-title" content="SAA з нуля">')
    site_html = build_site(chapters, services, questions, sets, head_web, PDF_WEB)
    local_html = build_site(chapters, services, questions, sets,
                            '<link rel="icon" type="image/png" href="docs/deep/icons/icon-192.png">', PDF_LOCAL)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "index.html").write_text(site_html, encoding="utf-8")
    (ROOT / HTML_LOCAL).write_text(local_html, encoding="utf-8")
    (OUT / "manifest.webmanifest").write_text(json.dumps(MANIFEST, ensure_ascii=False, indent=2), encoding="utf-8")
    version = hashlib.sha1(site_html.encode("utf-8")).hexdigest()[:10]
    (OUT / "sw.js").write_text(SW % version, encoding="utf-8")
    n_q = sum(c["q"] for c in chapters)
    n_trg = sum(c["trg"] for c in chapters)
    n_fig = sum(c["figs"] for c in chapters)
    words = sum(c["words"] for c in chapters)
    print(f"Сайт: docs/deep/index.html — розділів {len(chapters)}, слів {words}, питань {n_q}, тригерів {n_trg}, "
          f"схем {n_fig}, записів словника {len(services)}, питань іспиту {len(questions)}, "
          f"{len(site_html) // 1024} KB, версія {version}")
    no_link = [s["id"] for s in services if not s["ch"]]
    if no_link:
        print(f"Без розділу в словнику: {len(no_link)} — {', '.join(no_link[:30])}{'…' if len(no_link) > 30 else ''}")

    if "--no-pdf" in sys.argv:
        return
    if "--no-icons" not in sys.argv:
        for size, name in ((192, "icon-192.png"), (512, "icon-512.png"), (180, "apple-touch-icon.png")):
            render_icon(size, OUT / "icons" / name)
        print("Іконки: docs/deep/icons/")
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="saadeep_build_"))
    try:
        path = tmp / "book.html"
        path.write_text(build_print(chapters, services), encoding="utf-8")
        print_pdf(path.as_uri(), [OUT / PDF_WEB, ROOT / PDF_LOCAL])
        print(f"PDF: docs/deep/{PDF_WEB}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
