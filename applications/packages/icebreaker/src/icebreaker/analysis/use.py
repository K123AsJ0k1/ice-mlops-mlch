
def anaysis_line_share(
    code: str, 
    pattern: any
) -> float:
    lines = [l for l in code.splitlines() if l.strip() and not l.strip().startswith("#")]
    if not lines:
        return 0.0
    return sum(bool(pattern.match(l)) for l in lines) / len(lines)

def analysis_guess_format(
    code: str, 
    min_share: float = 0.5
) -> str | None:
    import re
    
    if re.match(r"\s*#!/(usr/)?bin/(env )?(ba)?sh", code):
        return "bash"

    # Line-level heuristics for code that is NOT inside a tagged fence.
    PYTHON_LINE_RE = re.compile(
        r"^\s*(def \w+\(|class \w+[:(]|import \w|from [\w.]+ import |if __name__ ==|"
        r"return\b|for \w+ in .+:|while .+:|@\w+|print\(|\w+\s*=\s*[\w\[{(\"'])"
    )
    BASH_LINE_RE = re.compile(
        r"^\s*(#!/(usr/)?bin/(env )?(ba)?sh|\$ |sudo |apt(-get)? |pip3? install |"
        r"cd |ls\b|echo |export \w+=|chmod |chown |grep |curl |wget |mkdir |rm |"
        r"systemctl |docker |git |for \w+ in .*; do|if \[)"
    )
    # bare "- item" lines are left out on purpose: they are also markdown bullets
    YAML_LINE_RE = re.compile(r"^\s*(-\s+)?[\w.\"'-]+:(\s+\S.*)?\s*$|^---\s*$")
    
    shares = {
        "python": anaysis_line_share(code, PYTHON_LINE_RE),
        "bash": anaysis_line_share(code, BASH_LINE_RE),
        "yaml": anaysis_line_share(code, YAML_LINE_RE),
    }
    fmt, share = max(shares.items(), key=lambda kv: kv[1])
    return fmt if share >= min_share else None

def analysis_classify_output(
    answer: str
) -> str:
    import re
    
    FENCE_RE = re.compile(r"```[ \t]*([\w+.-]*)[^\n]*\n(.*?)```", re.DOTALL)

    LANG_ALIASES = {
        "python": {"python", "py", "python3", "ipython", "pycon"},
        "yaml": {"yaml", "yml"},
        "bash": {"bash", "sh", "shell", "zsh", "console", "shell-session", "shellsession"},
    }

    MARKDOWN_RE = re.compile(
        r"^\s{0,3}#{1,6}\s"              # headings
        r"|^\s*[-*+]\s+\S"                # bullet lists
        r"|^\s*\d+[.)]\s+\S"              # numbered lists
        r"|^\s*\|.*\|\s*$"                # table rows
        r"|^\s*>\s"                       # block quotes
        r"|\*\*[^*\n]+\*\*"               # bold
        r"|\[[^\]\n]+\]\([^)\s]+\)",      # links
        re.MULTILINE,
    )

    blocks = FENCE_RE.findall(answer)

    if blocks:
        sizes: dict[str, int] = {}
        snippets: dict[str, list[str]] = {}
        for tag, code in blocks:
            tag = tag.lower()
            fmt = next((f for f, al in LANG_ALIASES.items() if tag in al), None)
            if fmt is None and tag in ("", "text", "plaintext"):
                fmt = analysis_guess_format(code)          # untagged fence
            if fmt is None:
                continue                                # e.g. ```json, ```sql
            sizes[fmt] = sizes.get(fmt, 0) + len(code)
            snippets.setdefault(fmt, []).append(code)

        if len(sizes) > 1:
            return "mixed"
        if len(sizes) == 1:
            fmt = next(iter(sizes))
            return fmt
        return "other"                                  # only unsupported languages

    if len(MARKDOWN_RE.findall(answer)) >= 2:
        return "markdown"
    return "other"
