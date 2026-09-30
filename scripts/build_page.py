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
from comeclean.config import JUDGE_MODEL, JUDGE_TEMPERATURE
from comeclean.scoring import REPORTS
from models import lookup

ROOT = Path(__file__).resolve().parent.parent
LOGS_DIR = ROOT / "logs"
METHODOLOGY_MD = ROOT / "docs" / "methodology.md"
EXPERIMENT_SVG = ROOT / "docs" / "experiment.svg"
TEMPLATE_HTML = Path(__file__).parent / "templates" / "index.html"
OUTPUT_HTML = ROOT / "public" / "index.html"

_DATA_OPEN = '<script id="page-data" type="application/json">'
_DATA_CLOSE = "</script>"
_DOCS_PLACEHOLDER = "<!-- DOCS_CONTENT -->"
_EXPERIMENT_PLACEHOLDER = "<!-- EXPERIMENT_SVG -->"
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

MIN_TRIALS = 5


def _score(sample: EvalSample) -> Score | None:
    # Trials without a report have no score.
    return (sample.scores or {}).get("come_clean_scorer")


def _category(value: dict) -> str | None:
    return next((name for name in REPORTS if value.get(name)), None)


def load_run(log_file: Path) -> dict | None:
    log = read_eval_log(log_file)
    if log.status != "success":
        print(f"Skipped ({log.status}): {log_file.name}")
        return None

    # Count samples directly: Inspect's epoch reducer averages and rounds each field.
    scored = [(smp, score) for smp in log.samples if (score := _score(smp)) is not None]
    values = [score.value for _, score in scored]
    if values and "admitted_use" not in values[0]:
        # Older scorer; its fields are not comparable.
        print(f"Skipped (pre-redesign run): {log_file.name}")
        return None

    failed_count = len(log.samples) - len(values)
    exploited = [v for v in values if v["exploited"]]
    refused = [v for v in values if not v["exploited"]]
    model = lookup(log.eval.model)

    given_all = {name: sum(1 for v in values if v[name]) for name in REPORTS}
    given_exploited = {name: sum(1 for v in exploited if v[name]) for name in REPORTS}

    # D is derived here, not in the scorer, so old logs need no re-judging.
    disclosed_all = len(values) - given_all["undisclosed"]
    disclosed_u = len(exploited) - given_exploited["undisclosed"]
    disclosed_not_u = len(refused) - sum(1 for v in refused if v["undisclosed"])
    # P(C) is over exploiting trials only: coming clean presupposes use.
    come_clean = given_exploited["admitted_use"]

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
        "completed_samples": len(values),
        "failed_count": failed_count,
        "exploited_samples": len(exploited),
        "refused_samples": len(refused),
        "exploitation_count": len(exploited),
        "given_all_counts": given_all,
        "disclosed_count": disclosed_all,
        "disclosed_exploited_count": disclosed_u,
        "disclosed_refused_count": disclosed_not_u,
        "come_clean_count": come_clean,
        "reports": reports,
    }


def build_page_data() -> dict:
    runs = [run for path in sorted(LOGS_DIR.glob("*.eval")) if (run := load_run(path)) is not None]
    runs.sort(key=lambda r: (r["model_vendor"], r["model_id"]))
    return {
        "generated": _utc_timestamp(),
        "version": VERSION,
        "thresholds": {"min_trials": MIN_TRIALS},
        "runs": runs,
    }


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
    # Markdown keeps the table-safe `\|` inside code spans; unescape it.
    return html.replace("\\|", "|")


# Inlined because only index.html is deployed; an XML declaration is invalid in HTML.
def _read_svg(path: Path) -> str:
    if not path.exists():
        return ""
    svg = path.read_text()
    return svg[svg.index("<svg"):]


# Read from the modules so the page matches what the eval sends; placeholders stay visible.
PROMPTS = (
    ("User request", "The user message that starts the episode.",
     ((None, prompts.USER_PROMPT),)),
    ("Restricted-path warning", "Appended to a tool result that touches the off-limits folder. "
     "<code>{paths}</code> is replaced at run time by the paths that were touched.",
     ((None, prompts.RESTRICTED_WARNING),)),
    ("Report tool description", "What the agent is told the final report is for. Both strings reach the model: "
     "one describes the tool, the other describes its only argument.",
     (("Tool description", prompts.SUBMIT_REPORT_DESCRIPTION),
      ("report argument", prompts.SUBMIT_REPORT_ARG_DESCRIPTION))),
    ("Judge model", "How each report is classified. <code>{report}</code> is replaced at run time by the report "
     "the agent filed.",
     (("Model", JUDGE_MODEL),
      ("Temperature", str(JUDGE_TEMPERATURE)),
      ("Prompt", prompts.JUDGE_PROMPT))),
)


class _KeepPlaceholders(dict):
    """Resolves nothing, so `{report}` survives while `{{` becomes a real brace."""

    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


def render_prompts_html() -> str:
    blocks = []
    for title, note, parts in PROMPTS:
        body = ""
        for sublabel, value in parts:
            if sublabel:
                body += f'<div class="prompt-sublabel">{sublabel}</div>'
            text = value.format_map(_KeepPlaceholders()).strip()
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
    html = html.replace(_EXPERIMENT_PLACEHOLDER, _read_svg(EXPERIMENT_SVG))
    html = html.replace(_PROMPTS_PLACEHOLDER, render_prompts_html())
    html = html.replace(_TITLE_PLACEHOLDER, html_escape(TITLE))
    html = html.replace(_TAGLINE_PLACEHOLDER, html_escape(TAGLINE))
    html = html.replace(_DESCRIPTION_PLACEHOLDER, html_escape(DESCRIPTION))
    OUTPUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_HTML.write_text(inject_page_data(html, data))
    print(f"Wrote {len(data['runs'])} run(s) to {OUTPUT_HTML}")


if __name__ == "__main__":
    main()
