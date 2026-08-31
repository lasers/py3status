"""
Generates docs/modules.md from every module's own docstring (see
docstrings.py for docstring -> Markdown conversion) plus its screenshots
(see screenshots.py). Zensical has no build-hook system, so this runs as
its own explicit step before `zensical build`/`zensical serve` - see
generate() below.

Pipeline per module, in create_module_docs(): the raw Markdown a
docstring converts to is a flat wall of text (a summary, a longer
description, then "Configuration parameters:"-style sections written as
plain indented bullets/prose). wrap_module_details() and its helpers
(wrap_listings, wrap_notes, wrap_example_header, wrap_data_lines,
fence_prose) turn that into properly styled Markdown: definition lists
for the option-reference sections, a fenced block for the free-text
description, bolded section headers throughout.
"""

import re
import sys
from pathlib import Path

from py3status.docstrings import core_module_docstrings

# screenshots.py pulls in Pillow/fontTools, needed only for the actual
# screenshot-generation step - imported lazily (inside generate() and
# create_module_docs() below) so importing this module's text-transform
# utilities (eg for tests) doesn't require those to be installed.


def write_if_changed(path, content):
    """Write generated documentation only when its content changed."""
    path = Path(path)
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return
    path.write_text(content, encoding="utf-8")


def file_sort(my_list):
    """
    Sort a list of files in a nice way.
    eg item-10 will be after item-9
    """

    def alphanum_key(key):
        """
        Split the key into str/int parts
        """
        return [int(s) if s.isdigit() else s for s in re.split("([0-9]+)", key)]

    my_list.sort(key=alphanum_key)
    return my_list


def screenshots(config, screenshots_data, module_name):
    """
    Create .md output for any screenshots a module may have - all on one
    paragraph (single newlines, no blank lines between them) tagged
    `.module-screenshots` via attr_list, so CSS can give them a tight,
    list-like gap instead of full paragraph spacing between each shot.
    """
    shots = screenshots_data.get(module_name)
    if not shots:
        return ""

    out = []
    for index, shot in enumerate(file_sort(shots)):
        if not Path(f"{config['docs_dir']}/screenshots/{shot}.png").exists():
            continue
        out.append(f"![{module_name} example {index}](/screenshots/{shot}.png)")
    if not out:
        return ""
    return "\n" + "\n".join(out) + "\n{: .module-screenshots }\n"


# a "Header:" line followed by "- `name` description..." bullets (each
# bullet optionally continued on 4-space-indented lines) - the
# "Configuration parameters:" shape. Consumed by wrap_listings().
LISTING_BLOCK_RE = re.compile(r"(^\w[^\n]*:\n)((?:\n*[ ]{0,2}- .*(?:\n {4}.*)*)+)", re.MULTILINE)
# one bullet within a LISTING_BLOCK_RE match: "- `name` rest of line...",
# plus any 4-space-indented continuation lines. Consumed by wrap_listings().
BULLET_NAME_RE = re.compile(r"^- `([^`]+)`(.*(?:\n {4}.*)*)", re.MULTILINE)
# a trailing "*(default ...)*" marker at the end of a bullet's text (the
# value can itself span multiple lines, eg a list of tuples). Consumed by
# wrap_listings().
DEFAULT_RE = re.compile(r"\s*\*\(default (.*)\)\*\s*$", re.DOTALL)
# a "Header:" line followed by plain 4-space-indented prose (no `- `
# bullets) - the "Note:"/"Requires:"/"Color options:" shape. Consumed by
# wrap_notes().
NOTE_BLOCK_RE = re.compile(r"(^\w[^\n]*:\n)((?:\n*^ {4}.*\n?)+)", re.MULTILINE)
# pymdownx.blocks.admonition's built-in types (aliases omitted - not
# seen in any module docstring so far). A NOTE_BLOCK_RE header naming
# one of these (singular or plural, eg "Note:"/"Notes:") becomes a real
# `/// type ... ///` admonition in wrap_notes() instead of a plain
# bold header.
ADMONITION_TYPES = {
    "note",
    "abstract",
    "info",
    "tip",
    "success",
    "question",
    "warning",
    "failure",
    "danger",
    "bug",
    "example",
    "quote",
}
# the run of trailing "**author** ..." / "**license** ..." / "**source** ..."
# lines every module docstring ends with. Consumed by wrap_data_lines().
DATA_BLOCK_RE = re.compile(r"(?:^\*\*(?:author|license|source)\*\* .*$\n?\n?)+", re.MULTILINE)
# one "**label** value" line within a DATA_BLOCK_RE match. Consumed by
# wrap_data_lines().
DATA_LINE_RE = re.compile(r"^\*\*([^*]+)\*\* (.*)$", re.MULTILINE)
# a standalone "Examples:"/"Example:" line directly introducing a fenced
# code block. Consumed by wrap_example_header().
EXAMPLE_HEADER_RE = re.compile(r"^(Examples?:)\n(?=```)", re.MULTILINE)
# a pymdownx.blocks.admonition fence, eg "/// warning\n...\n///" - some
# modules' long descriptions embed one directly (eg aws_bill's).
# Consumed by fence_prose(), which must keep these live and out of its
# prose fence.
ADMONITION_RE = re.compile(r"^///\s*\S+\n.*?\n///\s*$\n?", re.MULTILINE | re.DOTALL)


def format_definition(name, text, bold=False):
    """
    Format one `name`/:   text definition-list entry (the def_list
    markdown extension) - every line is re-indented to exactly 4 spaces
    regardless of whatever indentation it arrived with (some callers
    pass already-4-space-indented continuation lines, others pass plain
    dedented text), so multi-paragraph text stays part of the same
    definition without doubling up on indentation.
    """
    dt = f"**`{name}`**" if bold else f"`{name}`"
    lines = [line.strip() for line in text.strip().splitlines()] or [""]
    out = f"{dt}\n:   {lines[0]}"
    for line in lines[1:]:
        out += f"\n    {line}" if line else "\n    "
    return out


def bold_header(header):
    """
    Bold a "Configuration parameters:"-style section header line.
    """
    return f"**{header.strip()}**"


def _bullet_definition(name, rest, bold):
    """Format one BULLET_NAME_RE match as a definition, pulling any
    trailing "*(default ...)*" marker (can span multiple lines, eg a
    list of tuples) onto its own, single-line form."""
    rest = rest.lstrip(" ")
    dm = DEFAULT_RE.search(rest)
    if dm:
        value = " ".join(dm.group(1).split())
        rest = f"{rest[: dm.start()].rstrip()}\n\n*Default: `{value}`*"
    return format_definition(name, rest, bold=bold)


def wrap_listings(content):
    """
    Turn each "Configuration parameters:"-style bullet listing (a line
    ending in `:` followed by `- ...` bullets, each optionally preceded
    by a blank line) into a real Markdown definition list - a manpage-like
    option reference for free, using def_list instead of hand-built HTML.

    A bullet with nothing after its name (eg weather_owm's `format_clouds:`
    or xkb_input's `swaymsg:`) is a sub-heading grouping the bulleted
    entries that follow it, not a real definition - folding it into the
    same flat list would render as a confusing, description-less entry.
    Instead, each such run of bullets becomes its own definition list,
    titled "<header> (<names>):".
    """

    def repl(match):
        header, bullets = match.group(1), match.group(2)
        header_text = header.strip().rstrip(":")
        # placeholders (eg `{icon}`) are code, not a config option name -
        # keep the term as plain code instead of bolding it like a
        # Configuration parameters/Metadata/etc name
        bold = "placeholder" not in header_text.lower()

        segments = []  # [(sub_heading_names_or_None, [(name, rest), ...]), ...]
        pending_names, names, body = [], None, []
        for bm in BULLET_NAME_RE.finditer(bullets):
            name, rest = bm.group(1), bm.group(2).lstrip(" ")
            if rest.strip():
                if pending_names:
                    names, pending_names = pending_names, []
                body.append((name, rest))
            else:
                if body:
                    segments.append((names, body))
                    body = []
                pending_names.append(name)
        if body:
            segments.append((names, body))

        if len(segments) == 1 and segments[0][0] is None:
            definitions = "\n\n".join(_bullet_definition(n, r, bold) for n, r in segments[0][1])
            return f"{bold_header(header)}\n\n{definitions}\n"

        out = []
        for sub_names, items in segments:
            title = f"{header_text} ({', '.join(sub_names)}):" if sub_names else f"{header_text}:"
            definitions = "\n\n".join(_bullet_definition(n, r, bold) for n, r in items)
            out.append(f"{bold_header(title)}\n\n{definitions}\n")
        return "\n\n".join(out)

    return LISTING_BLOCK_RE.sub(repl, content)


def _admonition_type(header):
    """
    Return the ADMONITION_TYPES member a NOTE_BLOCK_RE header names (eg
    "Warnings:" -> "warning"), or None if it doesn't name one.
    """
    key = header.strip().rstrip(":").lower()
    if key in ADMONITION_TYPES:
        return key
    # a single trailing "s" for the plural form (eg "Notes:") - not a
    # blind rstrip("s"), which would mangle "success" to "succe"
    if key.endswith("s") and key[:-1] in ADMONITION_TYPES:
        return key[:-1]
    return None


def wrap_notes(content):
    """
    Give plain-prose headed sections a treatment matching what they are:
    a header naming a real admonition type ("Note:"/"Notes:",
    "Warning:"/"Warnings:", etc - see ADMONITION_TYPES) becomes a real
    admonition (pymdownx.blocks.admonition's `///type ... ///` fence);
    everything else in this shape - "Requires:", "Color options:", etc -
    is just dedented back to plain prose under a bold header.
    """

    def repl(match):
        header, body = match.group(1), match.group(2)
        dedented = "\n".join(line[4:] for line in body.rstrip().splitlines())
        adm_type = _admonition_type(header)
        if adm_type:
            return f"/// {adm_type}\n{dedented}\n///\n"
        return f"{bold_header(header)}\n\n{dedented}\n"

    return NOTE_BLOCK_RE.sub(repl, content)


def wrap_example_header(content):
    """
    Bold a standalone "Examples:" (or "Example:") line that introduces a
    fenced code block - the one section header shape that's neither a
    bullet listing (wrap_listings) nor 4-space-indented prose
    (wrap_notes), so it falls through both untouched otherwise.
    """
    return EXAMPLE_HEADER_RE.sub(lambda m: f"{bold_header(m.group(1))}\n\n", content)


def wrap_data_lines(content):
    """
    Give the trailing `**author** ...` / `**license** ...` / `**source** ...`
    lines the same definition-list treatment as every other listing,
    instead of leaving them as plain bold text.
    """

    def repl(match):
        definitions = "\n\n".join(
            format_definition(m.group(1), m.group(2), bold=True)
            for m in DATA_LINE_RE.finditer(match.group(0))
        )
        return f"{bold_header('Metadata:')}\n\n{definitions}\n"

    return DATA_BLOCK_RE.sub(repl, content)


def _fence(part):
    """Fence one prose segment for fence_prose(), or "" if it's blank."""
    part = part.strip()
    if not part:
        return ""
    # docstrings.py HTML-escaped <, >, & for regular markdown rendering;
    # a fenced code block displays raw text verbatim and escapes it
    # itself, so pre-escaped entities would show up literally (eg
    # "&lt;" instead of "<") - undo that here.
    for entity, char in (("&lt;", "<"), ("&gt;", ">"), ("&amp;", "&")):
        part = part.replace(entity, char)
    # a 4-backtick fence: some modules' long descriptions already contain
    # their own 3-backtick example, which would otherwise prematurely
    # close this one. "text" avoids this site's default Python syntax
    # highlighting being applied to prose.
    return f"````text\n{part}\n````"


def fence_prose(text):
    """
    Wrap plain prose in a fenced text block, but leave any admonition
    section as a real, rendered admonition instead of swallowing it into
    the fence as inert literal text - both a raw /// warning ... ///
    fence and a "Warnings:"-style header (eg aws_bill's) are recognized.
    Unlike wrap_notes(), a non-admonition "Header:\n    text" shape is
    left completely alone: free prose often has an ordinary sentence
    ending in ":" that isn't a real section header.
    """

    def header_repl(match):
        adm_type = _admonition_type(match.group(1))
        if not adm_type:
            return match.group(0)
        dedented = "\n".join(line[4:] for line in match.group(2).rstrip().splitlines())
        return f"/// {adm_type}\n{dedented}\n///\n"

    text = NOTE_BLOCK_RE.sub(header_repl, text)
    out = []
    pos = 0
    for match in ADMONITION_RE.finditer(text):
        out.append(_fence(text[pos : match.start()]))
        out.append(match.group(0).strip())
        pos = match.end()
    out.append(_fence(text[pos:]))
    return "\n\n".join(part for part in out if part)


def wrap_module_details(content, screenshots_md=""):
    """
    Style one module's already-Markdown docstring body (`content`, from
    core_module_docstrings()) plus its screenshots block (`screenshots_md`,
    from screenshots() above) into the final content of its <div
    class="module-details"> - the div itself is added by the caller,
    create_module_docs().

    `content` is split at the first "Header:\\n- bullets" listing found
    (LISTING_BLOCK_RE): everything before that point is the free-text
    description (bolded summary + fenced long description, via
    fence_prose()); everything from that point on is run through the
    wrap_listings -> wrap_notes -> wrap_example_header -> wrap_data_lines
    pipeline, which turns each remaining "Header:"-shaped section into
    styled Markdown (definition lists, admonitions, or bolded headers,
    depending on the section's shape).
    """
    first_listing = LISTING_BLOCK_RE.search(content)
    split_at = first_listing.start() if first_listing else len(content)
    description, rest = content[:split_at], content[split_at:]

    out = screenshots_md.strip()
    description = description.strip()
    if description:
        # module docstring convention: a single-line summary, a blank
        # line, then a longer description - bold the summary as its own
        # paragraph (it's regular markdown, so the entity-escaping
        # docstrings.py already did for HTML rendering is correct here),
        # then fence the rest.
        short, _, long_desc = description.partition("\n\n")
        out += f"\n\n**{short.strip()}**\n"
        long_desc = long_desc.strip()
        if long_desc:
            out += "\n" + fence_prose(long_desc) + "\n"
    out = out.strip() + "\n"
    if rest:
        out += "\n" + wrap_data_lines(wrap_example_header(wrap_notes(wrap_listings(rest))))
    return out


def create_module_docs(config):
    """
    Write docs/modules.md: one "## module_name" section per core module,
    sorted alphabetically, each wrapping its styled detail text (see
    wrap_module_details()) in a `.module-details` div (md_in_html, so the
    Markdown inside still renders).
    """
    from py3status.screenshots import get_samples

    data = core_module_docstrings(format="md")
    # screenshot sample names are "<module>-<index>-..."; group them back
    # by module so screenshots() can look up a given module's shots.
    screenshots_data = {}
    samples = get_samples()
    for sample in samples:
        module = sample.split("-")[0]
        if module not in screenshots_data:
            screenshots_data[module] = []
        screenshots_data[module].append(sample)

    out = ["# Available modules"]
    # details
    for module in sorted(data):
        out.append(
            '\n## {name}\n\n<div class="module-details" markdown="1">\n\n'
            "{details}\n</div>\n".format(
                name=module,
                details=wrap_module_details(
                    "".join(data[module]).strip(),
                    screenshots_md=screenshots(config, screenshots_data, module),
                ),
            )
        )
    # write include file
    path = f"{config['docs_dir']}/modules.md"
    print(f"Writing modules documentation to {path}...")
    write_if_changed(path, "".join(out))
    return config


COPYRIGHT_RE = re.compile(r"(copyright = \"Copyright &copy; \d{4}-)\d{4}\b")


def sync_copyright_year(path="zensical.toml"):
    """
    Keep zensical.toml's footer copyright end year current. mkdocs-
    material supports a `{% now 'utc', '%Y' %}` Jinja tag directly in
    the copyright string for this, but Zensical (a separate Rust
    reimplementation) doesn't evaluate it - it's passed through as
    inert literal text - so the year is instead patched here, in the
    one place that already runs before every build/serve.
    """
    from datetime import date

    path = Path(path)
    content = path.read_text(encoding="utf-8")
    new_content = COPYRIGHT_RE.sub(rf"\g<1>{date.today().year}", content, count=1)
    write_if_changed(path, new_content)


def generate(docs_dir="docs", skip_screenshots=False):
    """
    Run the whole generation pipeline. Zensical has no hooks/plugin
    system to run this automatically during a build, so it's invoked as
    its own explicit step before `zensical build`/`zensical serve`.
    The Py3 API reference itself is no longer generated here - it's a
    static docs/py3-reference.md using a `::: py3status.py3.Py3`
    mkdocstrings directive instead.
    """
    sync_copyright_year()
    config = {"docs_dir": docs_dir}
    if not skip_screenshots:
        from py3status.screenshots import create_screenshots

        create_screenshots(config)
    create_module_docs(config)
    return config


if __name__ == "__main__":
    generate(skip_screenshots="--no-screenshots" in sys.argv[1:])
