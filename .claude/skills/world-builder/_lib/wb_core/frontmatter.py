"""Frontmatter parsing and wikilink extraction (port of gray-matter usage)."""

import re
import yaml

_FRONTMATTER_RE = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n?", re.DOTALL)
_WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")


def parse_markdown(content: str, path: str) -> dict:
    """Parse a markdown file with YAML frontmatter.

    Returns {"path": path, "frontmatter": dict, "body": str}.
    """
    m = _FRONTMATTER_RE.match(content)
    if m:
        raw_yaml = m.group(1)
        body = content[m.end():]
        try:
            frontmatter = yaml.safe_load(raw_yaml) or {}
        except yaml.YAMLError:
            frontmatter = {}
    else:
        frontmatter = {}
        body = content

    if not isinstance(frontmatter, dict):
        frontmatter = {}

    return {"path": path, "frontmatter": frontmatter, "body": body}


def serialize_markdown(frontmatter: dict, body: str) -> str:
    """Write YAML frontmatter + markdown body."""
    yaml_str = yaml.dump(
        frontmatter,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
        width=120,
    )
    # Ensure body is separated by a blank line
    sep = "\n" if body and not body.startswith("\n") else ""
    return f"---\n{yaml_str}---{sep}{body}"


def extract_wikilinks(text: str) -> list[str]:
    """Extract wikilink targets from body text. [[Foo|Bar]] -> 'Foo'."""
    results = []
    for match in _WIKILINK_RE.finditer(text):
        inner = match.group(1)
        target = inner.split("|")[0].strip()
        if target:
            results.append(target)
    return results


def extract_frontmatter_links(data: dict) -> list[str]:
    """Recursively find wikilinks embedded in frontmatter values."""
    links: list[str] = []
    _walk_value(data, links)
    return links


def _walk_value(value, links: list[str]) -> None:
    if isinstance(value, str):
        links.extend(extract_wikilinks(value))
    elif isinstance(value, list):
        for item in value:
            _walk_value(item, links)
    elif isinstance(value, dict):
        for v in value.values():
            _walk_value(v, links)


def strip_wikilink(link: str) -> str:
    """'[[Foo]]' -> 'Foo', '[[Foo|Bar]]' -> 'Foo', plain 'Foo' -> 'Foo'."""
    m = _WIKILINK_RE.search(link)
    if m:
        return m.group(1).split("|")[0].strip()
    return link.strip()


def wikilink(name: str, display: str = None) -> str:
    """Create wikilink syntax."""
    if display and display != name:
        return f"[[{name}|{display}]]"
    return f"[[{name}]]"
