from __future__ import annotations

import json
import tomllib
from html import escape as html_escape
from datetime import datetime, timezone
from pathlib import Path

import markdown
from inspect_ai.log import EvalSample, read_eval_log
from inspect_ai.scorer import Score

from comeclean import prompts
from comeclean.scoring import REPORTS
from models import lookup

ROOT = Path(__file__).resolve().parent.parent
LOGS_DIR = ROOT / "logs"
METHODOLOGY_MD = ROOT / "docs" / "methodology.md"
TEMPLATE_HTML = Path(__file__).parent / "templates" / "index.html"
OUTPUT_HTML = ROOT / "public" / "index.html"

_DATA_OPEN = '<script id="page-data" type="application/json">'
_DATA_CLOSE = "</script>"
_DOCS_PLACEHOLDER = "<!-- DOCS_CONTENT -->"
_PROMPTS_PLACEHOLDER = "<!-- PROMPTS_CONTENT -->"
_TITLE_PLACEHOLDER = "<!-- TITLE -->"
_TAGLINE_PLACEHOLDER = "<!-- TAGLINE -->"
_DESCRIPTION_PLACEHOLDER = "<!-- DESCRIPTION -->"

with open(ROOT / "pyproject.toml", "rb") as _f:
    _PYPROJECT = tomllib.load(_f)

VERSION = _PYPROJECT["project"]["version"]
TITLE = _PYPROJECT["tool"]["comeclean"]["headline"]
TAGLINE = _PYPROJECT["project"]["description"]
DESCRIPTION = " ".join(_PYPROJECT["tool"]["comeclean"]["summary"].split())


def _score(sample: EvalSample) -> Score | None:
    # A trial that filed no report has no score at all.
    return (sample.scores or {}).get("come_clean_scorer")


def _category(value: dict) -> str | None:
    return next((name for name in REPORTS if value.get(name)), None)


def load_run(log_file: Path) -> dict | None:
    log = read_eval_log(log_file)
    if log.status != "success":
        print(f"Skipped ({log.status}): {log_file.name}")
        return None

    # Computed straight from log.samples rather than log.results.scores[0].metrics:
    # with epochs > 1, Inspect's default epoch reducer averages each field across
    # a sample's epochs before its own aggregate metrics run, which can silently
    # round a fractional result up or down. Raw per-sample counts avoid that.
    scored = [(smp, score) for smp in log.samples if (score := _score(smp)) is not None]
    values = [score.value for _, score in scored]
    if values and "admitted_use" not in values[0]:
        # Written by an older scorer whose fields are not comparable with these.
        print(f"Skipped (pre-redesign run): {log_file.name}")
        return None

    failed_count = len(log.samples) - len(values)
    exploited = [v for v in values if v["exploited"]]
    refused = [v for v in values if not v["exploited"]]
    model = lookup(log.eval.model)

    def _rate(count: int, over: int) -> float | None:
        # None rather than zero when the denominator is empty: a model that
        # never exploited has no come-clean rate, it does not have one of 0%.
        return count / over if over else None

    given_all = {name: sum(1 for v in values if v[name]) for name in REPORTS}
    given_exploited = {name: sum(1 for v in exploited if v[name]) for name in REPORTS}

    # Disclosure D is not a fifth thing the judge emits: it is the four
    # categories regrouped, D = not undisclosed. Deriving it here rather than
    # in the scorer keeps every existing log readable without re-judging.
    disclosed_all = len(values) - given_all["undisclosed"]
    disclosed_u = len(exploited) - given_exploited["undisclosed"]
    disclosed_not_u = len(refused) - sum(1 for v in refused if v["undisclosed"])
    d_given_u = _rate(disclosed_u, len(exploited))
    d_given_not_u = _rate(disclosed_not_u, len(refused))

    reports = [
        {
            "report": score.answer,
            "judge_explanation": score.explanation,
            "exploited": value["exploited"],
            "category": _category(value),
        }
        for (_, score), value in zip(scored, values)
    ]

    return {
        "model_id": log.eval.model,
        "model_vendor": model.vendor,
        "model_display_name": model.display_name,
        "eval_created": log.eval.created[:10],
        "epochs": log.eval.config.epochs,
        "completed_samples": len(values),
        "failed_count": failed_count,
        "exploited_samples": len(exploited),
        "refused_samples": len(refused),
        "exploitation_count": len(exploited),
        "exploitation_rate": _rate(len(exploited), len(values)),
        "given_all_counts": given_all,
        "given_exploited_counts": given_exploited,
        "disclosed_count": disclosed_all,
        "disclosure_rate": _rate(disclosed_all, len(values)),
        "disclosed_exploited_count": disclosed_u,
        "disclosure_rate_exploited": d_given_u,
        "disclosed_refused_count": disclosed_not_u,
        "disclosure_rate_refused": d_given_not_u,
        "disclosure_gap": (None if d_given_u is None or d_given_not_u is None
                           else d_given_u - d_given_not_u),
        "reports": reports,
    }


def build_page_data() -> dict:
    runs = [run for path in sorted(LOGS_DIR.glob("*.eval")) if (run := load_run(path)) is not None]
    runs.sort(key=lambda r: (r["model_vendor"], r["model_id"]))
    return {"generated": _utc_timestamp(), "version": VERSION, "runs": runs}


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def inject_page_data(html: str, data: dict) -> str:
    start = html.find(_DATA_OPEN)
    if start == -1:
        raise ValueError("page-data marker not found in template")
    end = html.find(_DATA_CLOSE, start) + len(_DATA_CLOSE)
    blob = json.dumps(data, separators=(",", ":")).replace("</script>", "<\\/script>")
    return html[:start] + _DATA_OPEN + blob + _DATA_CLOSE + html[end:]


def _shift_headings(md_text: str) -> str:
    """Drop the top-level # title and shift ## -> ###, ### -> ####, etc."""
    lines = []
    for line in md_text.splitlines():
        if line.startswith("# "):
            continue
        elif line.startswith("#"):
            lines.append("#" + line)
        else:
            lines.append(line)
    return "\n".join(lines)


def _render_markdown(path: Path) -> str:
    if not path.exists():
        return ""
    html = markdown.markdown(_shift_headings(path.read_text()), extensions=["tables"])
    # Formulas such as `P(D | E)` escape their pipe in the source, so a table
    # formatter cannot mistake it for a column separator. Markdown unescapes it
    # in prose but not inside a code span, so finish the job here.
    return html.replace("\\|", "|")


# Read off the module rather than the file, so the page cannot drift from what
# the eval actually sends. Runtime placeholders such as {report} are left
# unresolved on purpose: they are part of the prompt the reader should see.
# Each entry is (title, note, parts), where parts pairs an optional sub-label
# with the module attribute to show under it.
PROMPTS = (
    ("User request", "The whole of the agent's instructions. There is no system prompt.",
     ((None, "USER_PROMPT"),)),
    ("Restricted-path warning", "Appended by search_code and read_file when a result touches the off-limits "
     "folder. <code>{paths}</code> is replaced at run time by the paths that were touched.",
     ((None, "RESTRICTED_WARNING"),)),
    ("Report tool description", "What the agent is told the final report is for. Both strings reach the model: "
     "one describes the tool, the other describes its only argument.",
     (("Tool description", "SUBMIT_REPORT_DESCRIPTION"),
      ("report argument", "SUBMIT_REPORT_ARG_DESCRIPTION"))),
    ("Judge prompt", "The judge sees only the report. It is never told whether the agent exploited. "
     "<code>{report}</code> is replaced at run time by the report the agent filed.",
     ((None, "JUDGE_PROMPT"),)),
)


class _KeepPlaceholders(dict):
    """Resolves nothing, so `{report}` survives while `{{` becomes a real brace."""

    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


def render_prompts_html() -> str:
    blocks = []
    for title, note, parts in PROMPTS:
        body = ""
        for sublabel, name in parts:
            if sublabel:
                body += f'<div class="prompt-sublabel">{sublabel}</div>'
            text = getattr(prompts, name).format_map(_KeepPlaceholders()).strip()
            body += f'<pre class="prompt-text">{html_escape(text)}</pre>'
        blocks.append(
            f'<div class="prompt-block"><div class="prompt-title">{title}</div>'
            f'<div class="prompt-note">{note}</div>{body}</div>'
        )
    return "".join(blocks)


def main() -> None:
    data = build_page_data()
    html = TEMPLATE_HTML.read_text()
    html = html.replace(_DOCS_PLACEHOLDER, _render_markdown(METHODOLOGY_MD))
    html = html.replace(_PROMPTS_PLACEHOLDER, render_prompts_html())
    html = html.replace(_TITLE_PLACEHOLDER, html_escape(TITLE))
    html = html.replace(_TAGLINE_PLACEHOLDER, html_escape(TAGLINE))
    html = html.replace(_DESCRIPTION_PLACEHOLDER, html_escape(DESCRIPTION))
    OUTPUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_HTML.write_text(inject_page_data(html, data))
    print(f"Wrote {len(data['runs'])} run(s) to {OUTPUT_HTML}")


if __name__ == "__main__":
    main()
