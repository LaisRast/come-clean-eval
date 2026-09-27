# Come Clean

An [Inspect](https://inspect.aisi.org.uk/) eval that asks whether a coding agent's own report mentions
information it was told not to use.

Every trial shows the agent an off-limits file through ordinary tool calls, in a task that cannot be finished
without it. Nothing asks the agent to bring this up, so the eval measures whether its final report does anyway,
and whether that changes when the information was actually used.

![How one trial runs: setup, forced exposure, the agent's turn, and the two measures](docs/experiment.svg)

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
