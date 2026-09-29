# Come Clean Eval

An [Inspect](https://inspect.aisi.org.uk/) eval asking: does a coding agent admit using information it was told
not to use?

Every trial shows the agent an off-limits file through ordinary tool calls, in a task that cannot be finished
without it. Nothing asks the agent to bring this up, so the eval measures whether the agent uses it, whether its
report mentions it anyway, and, when it did use it, whether the report says so.

![How one trial runs: setup, forced exposure, the agent's turn, and the measures](docs/experiment.svg)

- **Project page:** https://laisrast.github.io/come-clean-eval/
- **Methodology:** [`docs/methodology.md`](docs/methodology.md), also rendered on the project page along with
  every prompt verbatim.

## Running it

Requires [uv](https://docs.astral.sh/uv/) and an OpenRouter key.

```sh
cp .env.example .env        # then fill in OPENROUTER_API_KEY
make install

make eval                   # one model, override with MODEL= and EPOCHS=
make eval-all               # every model in scripts/models.py
make page                   # build public/index.html from logs/
```

`make help` lists the rest. Trials land in `logs/` as Inspect eval files; `make view` opens them in Inspect's
log viewer.
