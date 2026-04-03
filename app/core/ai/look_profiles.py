from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PromptExpansion:
    expanded_prompt: str
    added_intents: tuple[str, ...] = ()


_STYLE_REFERENCE_ALIASES: dict[str, tuple[str, ...]] = {
    "tim burton": (
        "gothic cinematic portrait",
        "whimsical dark fantasy mood",
        "pale skin",
        "cool shadows",
        "muted greens",
        "warm highlights",
    ),
    "steve mccurry": (
        "vivid documentary portrait",
        "rich reds",
        "warm earth tones",
        "natural skin",
        "crisp detail",
        "travel photography mood",
    ),
}

_TRAIT_INTENTS: dict[str, tuple[str, ...]] = {
    "gothic": ("gothic", "cinematic"),
    "dark fantasy": ("gothic", "cinematic"),
    "whimsical": ("stylized",),
    "documentary": ("documentary",),
    "travel photography": ("travel", "documentary"),
    "pale skin": ("portrait",),
    "natural skin": ("portrait",),
    "rich reds": ("vivid",),
}

_TRAIT_ADJUSTMENTS: dict[str, dict[str, str | int | float]] = {
    "gothic": {
        "Exposure": -0.25,
        "Contrast": 10,
        "Saturation": -4,
        "Clarity": 4,
        "Highlights": -10,
        "Shadows": 4,
        "WhiteBalanceTemperature": -250,
        "WhiteBalanceTint": -1,
        "ColorBalanceGreen": 4,
        "ColorBalanceBlue": 3,
        "ToneCurve": "Film Extra Shadow",
    },
    "dark fantasy": {
        "Contrast": 4,
        "Saturation": -2,
        "Highlights": -4,
        "ColorBalanceBlue": 2,
    },
    "whimsical": {
        "Highlights": -4,
        "Shadows": 4,
        "WhiteBalanceTint": 2,
        "ColorBalanceGreen": 2,
    },
    "pale skin": {
        "Highlights": -3,
        "Saturation": -2,
        "WhiteBalanceTint": 1,
    },
    "cool shadows": {
        "ColorBalanceBlue": 3,
        "WhiteBalanceTemperature": -150,
    },
    "muted greens": {
        "Saturation": -3,
        "ColorBalanceGreen": 2,
    },
    "warm highlights": {
        "WhiteBalanceTemperature": 250,
        "WhiteBalanceTint": 1,
        "ColorBalanceRed": 2,
    },
    "documentary": {
        "Exposure": 0.1,
        "Contrast": 6,
        "Saturation": 4,
        "Clarity": 6,
        "Highlights": -6,
        "Shadows": 6,
        "ToneCurve": "Film Standard",
    },
    "vivid": {
        "Contrast": 4,
        "Saturation": 6,
        "Clarity": 5,
    },
    "rich reds": {
        "Saturation": 2,
        "ColorBalanceRed": 6,
    },
    "natural skin": {
        "Highlights": -2,
        "WhiteBalanceTint": 1,
        "ColorBalanceRed": 2,
    },
    "crisp detail": {
        "Clarity": 8,
        "Contrast": 2,
    },
    "warm earth tones": {
        "WhiteBalanceTemperature": 220,
        "ColorBalanceRed": 2,
        "ColorBalanceGreen": 1,
    },
    "travel photography": {
        "Exposure": 0.05,
        "Contrast": 2,
        "Saturation": 2,
    },
}


def expand_style_references(prompt: str, intents: list[str] | None = None) -> PromptExpansion:
    normalized = prompt.lower()
    additions: list[str] = []
    added_intents: list[str] = []

    for alias, descriptors in _STYLE_REFERENCE_ALIASES.items():
        if alias not in normalized:
            continue
        additions.extend(descriptors)
        for descriptor in descriptors:
            for key, mapped in _TRAIT_INTENTS.items():
                if key in descriptor.lower():
                    for intent in mapped:
                        if intent not in added_intents:
                            added_intents.append(intent)

    if not additions:
        return PromptExpansion(expanded_prompt=prompt)

    existing_intents = {intent.lower() for intent in (intents or [])}
    deduped_additions = []
    for item in additions:
        if item.lower() not in normalized:
            deduped_additions.append(item)

    if not deduped_additions:
        return PromptExpansion(expanded_prompt=prompt, added_intents=tuple(added_intents))

    expanded_prompt = f"{prompt}. Creative direction: {', '.join(deduped_additions)}."
    deduped_intents = tuple(
        intent for intent in added_intents if intent.lower() not in existing_intents
    )
    return PromptExpansion(expanded_prompt=expanded_prompt, added_intents=deduped_intents)


def apply_creative_direction(
    keys: dict[str, str | int | float],
    prompt: str,
) -> dict[str, str | int | float]:
    updated = dict(keys)
    normalized = prompt.lower()

    for trait, adjustments in _TRAIT_ADJUSTMENTS.items():
        if trait not in normalized:
            continue
        for key, delta_or_value in adjustments.items():
            current = updated.get(key)
            if isinstance(delta_or_value, str):
                updated[key] = delta_or_value
                continue
            if isinstance(current, (int, float)):
                updated[key] = _clamp_key(key, float(current) + float(delta_or_value))
            else:
                updated[key] = _clamp_key(key, float(delta_or_value))

    return updated


def _clamp_key(key: str, value: float) -> int | float:
    if key == "Exposure":
        return round(max(-4.0, min(4.0, value)), 2)
    if key in {"Contrast", "Saturation", "Clarity", "Highlights", "Shadows"}:
        return int(round(max(-100.0, min(100.0, value))))
    if key == "WhiteBalanceTemperature":
        return int(round(max(2000.0, min(12000.0, value))))
    if key in {"WhiteBalanceTint", "ColorBalanceRed", "ColorBalanceGreen", "ColorBalanceBlue"}:
        return int(round(max(-50.0, min(50.0, value))))
    return round(value, 2)
