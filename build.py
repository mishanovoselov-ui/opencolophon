#!/usr/bin/env python3
"""
build.py — render methodology.md to methodology.html.

The markdown file stays the source of truth, so the page and the git
history of the page are the same object. That is the changelog until
there is a reason for a separate one.

No dependencies. Handles the subset the document actually uses:
headings, paragraphs, bullet lists, tables, rules, bold, italic.

  python3 build.py
"""

import html
import re
import sys
from pathlib import Path

SRC = Path("methodology.md")
OUT = Path("methodology.html")

TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Methodology — Open Colophon</title>
<meta name="description" content="How Open Colophon decides what to record, who writes a status, and what is never inferred.">
<link rel="stylesheet" href="style.css">
<link rel="canonical" href="https://opencolophon.org/methodology.html">
</head>
<body>

<header class="masthead">
  <p class="wordmark"><a href="/">Open Colophon</a></p>
</header>

<main class="prose">
{body}
</main>

<footer class="footer">
  <p><a href="/">Back to the registry</a></p>
  <p class="footer__disclosure">Run by Michael Novoselov, who also operates verificai.shop, a commercial business. No place in this registry is for sale and no outcome in it can be paid for.</p>
  <p><a href="mailto:contact@opencolophon.org">contact@opencolophon.org</a></p>
</footer>

</body>
</html>
"""


def inline(text):
    """Escape, then re-apply the inline marks. Order matters."""
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<![\w*])\*([^*\n]+?)\*(?![\w*])", r"<em>\1</em>", text)
    text = re.sub(r"`([^`]+?)`", r"<code>\1</code>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    # bare email in the contact line
    text = re.sub(r"(?<![\">])\b([\w.+-]+@[\w.-]+\.\w+)\b",
                  r'<a href="mailto:\1">\1</a>', text)
    return text


def split_row(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def render(md):
    out, lines, i = [], md.splitlines(), 0
    while i < len(lines):
        line = lines[i].rstrip()

        if not line.strip():
            i += 1
            continue

        # horizontal rule
        if re.fullmatch(r"-{3,}", line.strip()):
            out.append("<hr>")
            i += 1
            continue

        # heading
        m = re.match(r"^(#{1,4})\s+(.*)$", line)
        if m:
            lvl = len(m.group(1))
            out.append(f"<h{lvl}>{inline(m.group(2))}</h{lvl}>")
            i += 1
            continue

        # table
        if line.lstrip().startswith("|") and i + 1 < len(lines) \
           and re.fullmatch(r"\|[\s:|-]+\|", lines[i + 1].strip()):
            head = split_row(line)
            i += 2
            body = []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                body.append(split_row(lines[i]))
                i += 1
            out.append("<table><thead><tr>"
                       + "".join(f"<th>{inline(c)}</th>" for c in head)
                       + "</tr></thead><tbody>")
            for row in body:
                out.append("<tr>" + "".join(f"<td>{inline(c)}</td>"
                                            for c in row) + "</tr>")
            out.append("</tbody></table>")
            continue

        # bullet or ordered list
        m = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)$", line)
        if m:
            ordered = bool(re.match(r"\d+\.", m.group(2)))
            tag = "ol" if ordered else "ul"
            items = []
            while i < len(lines):
                mm = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)$", lines[i].rstrip())
                if not mm:
                    if lines[i].strip() and lines[i].startswith("  "):
                        items[-1] += " " + lines[i].strip()   # continuation
                        i += 1
                        continue
                    break
                items.append(mm.group(3))
                i += 1
            out.append(f"<{tag}>")
            out.extend(f"<li>{inline(t)}</li>" for t in items)
            out.append(f"</{tag}>")
            continue

        # paragraph
        buf = []
        while i < len(lines) and lines[i].strip() \
                and not re.match(r"^(#{1,4}\s|\||\s*[-*]\s|\s*\d+\.\s)",
                                 lines[i]) \
                and not re.fullmatch(r"-{3,}", lines[i].strip()):
            buf.append(lines[i].strip())
            i += 1
        if buf:
            text = " ".join(buf).strip()
            if text.startswith("*Version"):
                out.append(f'<p class="version">{inline(text.strip("*"))}</p>')
            else:
                out.append(f"<p>{inline(text)}</p>")

    return "\n".join(out)


def main():
    if not SRC.exists():
        sys.exit(f"{SRC} not found")
    body = render(SRC.read_text(encoding="utf-8"))
    OUT.write_text(TEMPLATE.format(body=body), encoding="utf-8")
    print(f"{OUT} — {len(body):,} bytes of body", file=sys.stderr)


if __name__ == "__main__":
    main()
