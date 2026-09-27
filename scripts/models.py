from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Model:
    provider: str
    vendor: str
    model: str
    display_name: str
    created: str = ""

    @property
    def id(self) -> str:
        return f"{self.provider}/{self.vendor}/{self.model}"


REGISTRY: list[Model] = [

    Model("openrouter", "anthropic", "claude-opus-5", "Claude Opus 5", "2026-07-24"),
    Model("openrouter", "anthropic", "claude-opus-4.8", "Claude Opus 4.8", "2026-05-27"),
    Model("openrouter", "anthropic", "claude-sonnet-5", "Claude Sonnet 5", "2026-06-30"),
    Model("openrouter", "anthropic", "claude-sonnet-4.6", "Claude Sonnet 4.6", "2026-02-17"),
    Model("openrouter", "anthropic", "claude-haiku-4.5", "Claude Haiku 4.5", "2025-10-15"),

    Model("openrouter", "deepseek", "deepseek-v4.1-flash", "DeepSeek V4.1 Flash", "2026-09-10"),
    Model("openrouter", "deepseek", "deepseek-v4-pro-0813", "DeepSeek V4 Pro 0813", "2026-08-12"),

    Model("openrouter", "google", "gemini-3.8-flash", "Gemini 3.8 Flash", "2026-09-02"),
    Model("openrouter", "google", "gemma-4-31b-it", "Gemma 4 31B", "2026-04-02"),

    Model("openrouter", "minimax", "minimax-m3", "MiniMax M3", "2026-05-31"),

    Model("openrouter", "moonshotai", "kimi-k3", "Kimi K3"),

    Model("openrouter", "openai", "gpt-4o-mini", "GPT-4o-mini", "2024-07-18"),
    Model("openrouter", "openai", "gpt-5-mini", "GPT-5 Mini", "2025-08-07"),
    Model("openrouter", "openai", "gpt-oss-120b", "gpt-oss-120b", "2025-08-05"),
    Model("openrouter", "openai", "gpt-5.5", "GPT-5.5", "2026-04-24"),
    Model("openrouter", "openai", "gpt-5.6-luna", "GPT-5.6 Luna", "2026-07-09"),
    Model("openrouter", "openai", "gpt-5.6-sol", "GPT-5.6 Sol", "2026-07-09"),
    Model("openrouter", "openai", "gpt-5.6-terra", "GPT-5.6 Terra", "2026-07-09"),

    Model("openrouter", "tencent", "hy3", "Hy3", "2026-07-06"),
    Model("openrouter", "tencent", "hy4-preview", "Hy4 preview", "2026-08-28"),

    Model("openrouter", "upstage", "solar-pro4", "Solar Pro 4", "2026-08-10"),

    Model("openrouter", "xiaomi", "mimo-v2.5", "MiMo-V2.5", "2026-04-22"),

    Model("openrouter", "x-ai", "grok-4.6", "Grok 4.6", "2026-08-12"),

    Model("openrouter", "qwen", "qwen3.8-27b", "Qwen3.8 27B", "2026-08-14"),
    Model("openrouter", "qwen", "qwen3.8-flash", "Qwen3.8 Flash", "2026-08-26"),

    Model("openrouter", "z-ai", "glm-5.3", "GLM 5.3", "2026-08-18"),
    Model("openrouter", "z-ai", "glm-5.3-flash", "GLM 5.3 Flash", "2026-08-26"),
]

BY_ID: dict[str, Model] = {m.id: m for m in REGISTRY}


def lookup(model_id: str) -> Model:
    if m := BY_ID.get(model_id):
        return m
    provider, _, rest = model_id.partition("/")
    vendor, _, model = rest.partition("/")
    return Model(provider=provider, vendor=vendor, model=model, display_name=model)
