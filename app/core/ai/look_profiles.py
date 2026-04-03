from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PromptExpansion:
    expanded_prompt: str
    added_intents: tuple[str, ...] = ()


Intensity = str


@dataclass(frozen=True)
class VariantProfile:
    name: str
    triggers: tuple[str, ...]
    intents: tuple[str, ...]
    adjustments: dict[str, str | int | float]


@dataclass(frozen=True)
class MainProfile:
    name: str
    triggers: tuple[str, ...]
    intents: tuple[str, ...]
    adjustments: dict[str, str | int | float]
    variants: tuple[VariantProfile, VariantProfile, VariantProfile]


def _variant(
    name: str,
    triggers: tuple[str, ...],
    intents: tuple[str, ...],
    adjustments: dict[str, str | int | float],
) -> VariantProfile:
    return VariantProfile(name=name, triggers=triggers, intents=intents, adjustments=adjustments)


_MAIN_PROFILES: tuple[MainProfile, ...] = (
    MainProfile(
        name="cinematic_portrait",
        triggers=("cinematic portrait", "cinematic", "hero portrait"),
        intents=("cinematic", "portrait"),
        adjustments={
            "Contrast": 8,
            "Clarity": 5,
            "Highlights": -8,
            "Shadows": 10,
            "ToneCurve": "Film Standard",
        },
        variants=(
            _variant(
                "cool_teal",
                ("teal shadows", "cool cinematic", "teal"),
                ("cool",),
                {"ColorBalanceBlue": 6, "WhiteBalanceTemperature": -250, "Saturation": -1},
            ),
            _variant(
                "warm_skin",
                ("warm skin", "golden skin", "warm portrait"),
                ("warm",),
                {"WhiteBalanceTemperature": 280, "ColorBalanceRed": 3, "WhiteBalanceTint": 1},
            ),
            _variant(
                "soft_rolloff",
                ("soft rolloff", "soft highlight", "gentle highlight"),
                ("soft",),
                {"Highlights": -6, "Contrast": -2, "Clarity": -1},
            ),
        ),
    ),
    MainProfile(
        name="gothic_fantasy",
        triggers=("gothic", "dark fantasy", "macabre", "burtonesque"),
        intents=("gothic", "cinematic", "stylized"),
        adjustments={
            "Exposure": -0.3,
            "Contrast": 12,
            "Saturation": -5,
            "Clarity": 4,
            "Highlights": -12,
            "Shadows": 6,
            "ColorBalanceGreen": 4,
            "ColorBalanceBlue": 5,
            "ToneCurve": "Film Extra Shadow",
        },
        variants=(
            _variant(
                "porcelain_skin",
                ("pale skin", "porcelain skin", "ghostly skin"),
                ("portrait",),
                {"Highlights": -4, "Saturation": -2, "WhiteBalanceTint": 2},
            ),
            _variant(
                "twisted_whimsy",
                ("whimsical", "storybook", "twisted whimsy"),
                ("stylized",),
                {"Shadows": 5, "WhiteBalanceTint": 3, "ColorBalanceGreen": 2},
            ),
            _variant(
                "moonlit_blue",
                ("moonlit", "cold moonlight", "blue moon"),
                ("cool",),
                {"WhiteBalanceTemperature": -350, "ColorBalanceBlue": 4, "Exposure": -0.15},
            ),
        ),
    ),
    MainProfile(
        name="vivid_documentary",
        triggers=("documentary", "photojournal", "travel portrait", "editorial documentary"),
        intents=("documentary", "portrait", "vivid"),
        adjustments={
            "Exposure": 0.15,
            "Contrast": 8,
            "Saturation": 8,
            "Clarity": 10,
            "Highlights": -8,
            "Shadows": 8,
            "ColorBalanceRed": 4,
            "ToneCurve": "Film Standard",
        },
        variants=(
            _variant(
                "rich_reds",
                ("rich reds", "vibrant reds", "red fabric"),
                ("vivid",),
                {"Saturation": 3, "ColorBalanceRed": 6},
            ),
            _variant(
                "warm_earth",
                ("warm earth", "earth tones", "dusty warm"),
                ("warm",),
                {"WhiteBalanceTemperature": 250, "ColorBalanceRed": 2, "ColorBalanceGreen": 1},
            ),
            _variant(
                "natural_skin",
                ("natural skin", "honest skin", "true skin"),
                ("portrait",),
                {"Highlights": -3, "WhiteBalanceTint": 1, "Contrast": -1},
            ),
        ),
    ),
    MainProfile(
        name="editorial_fashion",
        triggers=("editorial", "fashion", "magazine", "runway"),
        intents=("editorial", "fashion"),
        adjustments={
            "Exposure": 0.1,
            "Contrast": 9,
            "Saturation": 2,
            "Clarity": 7,
            "Highlights": -10,
            "Shadows": 6,
            "ToneCurve": "Film Standard",
        },
        variants=(
            _variant(
                "polished_skin",
                ("polished skin", "beauty skin", "clean skin"),
                ("portrait",),
                {"Highlights": -3, "Clarity": -1, "WhiteBalanceTint": 1},
            ),
            _variant(
                "studio_clean",
                ("studio", "clean backdrop", "commercial clean"),
                ("commercial",),
                {"Exposure": 0.2, "Contrast": 2, "Saturation": -1},
            ),
            _variant(
                "high_gloss",
                ("high gloss", "luxury gloss", "glossy"),
                ("luxury",),
                {"Clarity": 3, "Highlights": -2, "ColorBalanceBlue": 1},
            ),
        ),
    ),
    MainProfile(
        name="moody_monochrome",
        triggers=("monochrome", "black and white", "bw", "grayscale"),
        intents=("monochrome", "moody"),
        adjustments={
            "Contrast": 14,
            "Saturation": -20,
            "Clarity": 8,
            "Highlights": -10,
            "Shadows": 8,
            "ToneCurve": "Film Extra Shadow",
        },
        variants=(
            _variant(
                "matte_fade",
                ("matte", "fade", "lifted blacks"),
                ("matte",),
                {"Contrast": -3, "Shadows": 4},
            ),
            _variant(
                "silver_print",
                ("silver", "print", "darkroom"),
                ("fine-art",),
                {"Clarity": 2, "Highlights": -3},
            ),
            _variant(
                "hard_light",
                ("hard light", "noir", "hard shadow"),
                ("noir",),
                {"Contrast": 6, "Highlights": -4, "Shadows": -2},
            ),
        ),
    ),
    MainProfile(
        name="golden_hour",
        triggers=("golden hour", "sunset glow", "late afternoon"),
        intents=("warm", "portrait"),
        adjustments={
            "Exposure": 0.2,
            "Contrast": 4,
            "Saturation": 5,
            "Highlights": -6,
            "Shadows": 8,
            "WhiteBalanceTemperature": 350,
            "ColorBalanceRed": 3,
        },
        variants=(
            _variant(
                "peach_glow",
                ("peach", "peach glow"),
                ("warm",),
                {"ColorBalanceRed": 3, "WhiteBalanceTint": 2},
            ),
            _variant(
                "amber_haze",
                ("amber", "amber haze"),
                ("warm",),
                {"WhiteBalanceTemperature": 250, "Highlights": -2},
            ),
            _variant(
                "sunlit_skin",
                ("sunlit skin", "luminous skin"),
                ("portrait",),
                {"Highlights": -2, "WhiteBalanceTint": 1},
            ),
        ),
    ),
    MainProfile(
        name="night_neon",
        triggers=("night neon", "neon", "tokyo night", "city lights"),
        intents=("night", "cinematic"),
        adjustments={
            "Exposure": -0.25,
            "Contrast": 10,
            "Saturation": 5,
            "Clarity": 7,
            "Highlights": -12,
            "Shadows": 6,
            "ColorBalanceBlue": 4,
        },
        variants=(
            _variant(
                "magenta_signage",
                ("magenta", "pink neon", "fuchsia"),
                ("stylized",),
                {"WhiteBalanceTint": 4, "ColorBalanceRed": 3, "ColorBalanceBlue": 2},
            ),
            _variant(
                "cyan_glow",
                ("cyan", "teal neon", "electric blue"),
                ("cool",),
                {"ColorBalanceBlue": 5, "WhiteBalanceTemperature": -250},
            ),
            _variant(
                "wet_streets",
                ("wet streets", "rainy street", "reflections"),
                ("moody",),
                {"Highlights": -4, "Clarity": 2, "Shadows": 2},
            ),
        ),
    ),
    MainProfile(
        name="vintage_film",
        triggers=("vintage film", "retro film", "old film", "analogue"),
        intents=("film", "vintage"),
        adjustments={
            "Contrast": 3,
            "Saturation": -2,
            "Clarity": -1,
            "Highlights": -5,
            "Shadows": 6,
            "ToneCurve": "Film Standard",
        },
        variants=(
            _variant(
                "faded_print",
                ("faded", "washed print", "faded print"),
                ("matte",),
                {"Contrast": -3, "Saturation": -2},
            ),
            _variant(
                "warm_grain",
                ("warm grain", "dusty warm"),
                ("warm",),
                {"WhiteBalanceTemperature": 220, "ColorBalanceRed": 2},
            ),
            _variant(
                "cool_archive",
                ("archive", "cool archive"),
                ("cool",),
                {"WhiteBalanceTemperature": -180, "ColorBalanceBlue": 2},
            ),
        ),
    ),
    MainProfile(
        name="pastel_airy",
        triggers=("airy", "pastel", "soft pastel", "bright airy"),
        intents=("airy", "soft"),
        adjustments={
            "Exposure": 0.35,
            "Contrast": -2,
            "Saturation": -1,
            "Clarity": -3,
            "Highlights": -4,
            "Shadows": 10,
        },
        variants=(
            _variant(
                "rose_tint",
                ("rose", "pink tint", "blush"),
                ("soft",),
                {"WhiteBalanceTint": 3, "ColorBalanceRed": 2},
            ),
            _variant(
                "blue_milk",
                ("powder blue", "blue milk", "cool pastel"),
                ("cool",),
                {"ColorBalanceBlue": 3, "WhiteBalanceTemperature": -150},
            ),
            _variant(
                "cream_highlights",
                ("cream", "creamy", "creamy highlights"),
                ("warm",),
                {"Highlights": -2, "WhiteBalanceTemperature": 160},
            ),
        ),
    ),
    MainProfile(
        name="travel_earth",
        triggers=("travel", "earthy travel", "dusty road", "expedition"),
        intents=("travel", "warm"),
        adjustments={
            "Exposure": 0.05,
            "Contrast": 5,
            "Saturation": 4,
            "Clarity": 6,
            "Highlights": -6,
            "Shadows": 8,
            "WhiteBalanceTemperature": 180,
            "ColorBalanceRed": 2,
            "ColorBalanceGreen": 1,
        },
        variants=(
            _variant(
                "dusty_sand",
                ("dusty", "sand", "desert"),
                ("warm",),
                {"WhiteBalanceTemperature": 220, "Saturation": -1},
            ),
            _variant(
                "market_colors",
                ("market", "bazaar", "spice colors"),
                ("vivid",),
                {"Saturation": 3, "ColorBalanceRed": 2},
            ),
            _variant(
                "sun_baked",
                ("sun baked", "harsh sun"),
                ("travel",),
                {"Highlights": -4, "Contrast": 2},
            ),
        ),
    ),
    MainProfile(
        name="dramatic_landscape",
        triggers=("dramatic landscape", "epic landscape", "mountain drama"),
        intents=("landscape", "dramatic"),
        adjustments={
            "Exposure": -0.1,
            "Contrast": 12,
            "Saturation": 3,
            "Clarity": 12,
            "Highlights": -14,
            "Shadows": 6,
        },
        variants=(
            _variant(
                "stormy_skies",
                ("storm", "stormy skies", "thunder"),
                ("moody",),
                {"Exposure": -0.2, "ColorBalanceBlue": 3, "Highlights": -4},
            ),
            _variant(
                "misty_depth",
                ("mist", "fog", "atmospheric"),
                ("soft",),
                {"Contrast": -2, "Shadows": 4},
            ),
            _variant(
                "craggy_detail",
                ("rock detail", "craggy", "texture"),
                ("crisp",),
                {"Clarity": 4, "Contrast": 2},
            ),
        ),
    ),
    MainProfile(
        name="clean_commercial",
        triggers=("commercial", "product clean", "clean commercial"),
        intents=("commercial", "clean"),
        adjustments={
            "Exposure": 0.15,
            "Contrast": 6,
            "Saturation": 1,
            "Clarity": 5,
            "Highlights": -4,
            "Shadows": 4,
        },
        variants=(
            _variant(
                "neutral_whites",
                ("neutral whites", "true white"),
                ("clean",),
                {"WhiteBalanceTint": -1, "WhiteBalanceTemperature": -80},
            ),
            _variant(
                "catalog_even",
                ("catalog", "ecommerce", "even light"),
                ("commercial",),
                {"Exposure": 0.1, "Contrast": -1},
            ),
            _variant(
                "premium_polish",
                ("premium polish", "premium product"),
                ("luxury",),
                {"Clarity": 2, "Highlights": -1},
            ),
        ),
    ),
    MainProfile(
        name="cozy_autumn",
        triggers=("autumn", "fall", "cozy autumn", "october"),
        intents=("autumn", "warm"),
        adjustments={
            "Exposure": 0.05,
            "Contrast": 6,
            "Saturation": 2,
            "Highlights": -8,
            "Shadows": 10,
            "WhiteBalanceTemperature": 260,
            "ColorBalanceRed": 3,
            "ColorBalanceGreen": 2,
        },
        variants=(
            _variant(
                "copper_leaves",
                ("copper", "orange leaves", "maple"),
                ("autumn",),
                {"Saturation": 2, "ColorBalanceRed": 2},
            ),
            _variant(
                "forest_moss",
                ("forest", "moss", "olive"),
                ("earthy",),
                {"ColorBalanceGreen": 3, "Saturation": -1},
            ),
            _variant(
                "candle_warmth",
                ("candle", "hearth", "fireside"),
                ("warm",),
                {"WhiteBalanceTemperature": 200, "WhiteBalanceTint": 1},
            ),
        ),
    ),
    MainProfile(
        name="crisp_winter",
        triggers=("winter", "snow", "crisp winter", "frost"),
        intents=("winter", "cool"),
        adjustments={
            "Exposure": 0.1,
            "Contrast": 8,
            "Saturation": -1,
            "Clarity": 9,
            "Highlights": -10,
            "Shadows": 6,
            "WhiteBalanceTemperature": -220,
            "ColorBalanceBlue": 3,
        },
        variants=(
            _variant(
                "snow_glow",
                ("snow glow", "bright snow"),
                ("winter",),
                {"Exposure": 0.15, "Highlights": -2},
            ),
            _variant(
                "blue_ice",
                ("ice blue", "icy", "glacier"),
                ("cool",),
                {"ColorBalanceBlue": 3, "WhiteBalanceTemperature": -180},
            ),
            _variant(
                "pine_depth",
                ("pine", "evergreen", "conifer"),
                ("earthy",),
                {"ColorBalanceGreen": 2, "Shadows": 2},
            ),
        ),
    ),
    MainProfile(
        name="analog_fade",
        triggers=("analog fade", "washed analog", "expired film"),
        intents=("film", "faded"),
        adjustments={
            "Contrast": -4,
            "Saturation": -4,
            "Clarity": -2,
            "Highlights": -3,
            "Shadows": 8,
        },
        variants=(
            _variant(
                "expired_cyan",
                ("expired", "cyan cast"),
                ("cool",),
                {"ColorBalanceBlue": 3, "WhiteBalanceTemperature": -120},
            ),
            _variant(
                "dusty_pink",
                ("dusty pink", "rose fade"),
                ("soft",),
                {"WhiteBalanceTint": 3, "ColorBalanceRed": 2},
            ),
            _variant(
                "flat_midtones",
                ("flat mids", "flat midtones"),
                ("matte",),
                {"Contrast": -2, "Shadows": 2},
            ),
        ),
    ),
    MainProfile(
        name="punchy_sports",
        triggers=("sports", "action", "stadium", "athlete"),
        intents=("sports", "punchy"),
        adjustments={
            "Exposure": 0.1,
            "Contrast": 14,
            "Saturation": 6,
            "Clarity": 12,
            "Highlights": -6,
            "Shadows": 4,
        },
        variants=(
            _variant(
                "stadium_lights",
                ("stadium lights", "floodlights"),
                ("sports",),
                {"Highlights": -3, "WhiteBalanceTemperature": -80},
            ),
            _variant(
                "team_colors",
                ("team colors", "jersey color"),
                ("vivid",),
                {"Saturation": 3, "ColorBalanceRed": 2},
            ),
            _variant(
                "speed_crisp",
                ("speed", "motion freeze", "fast action"),
                ("crisp",),
                {"Clarity": 3, "Contrast": 2},
            ),
        ),
    ),
    MainProfile(
        name="food_rich_color",
        triggers=("food", "culinary", "dish", "restaurant"),
        intents=("food", "rich"),
        adjustments={
            "Exposure": 0.1,
            "Contrast": 7,
            "Saturation": 8,
            "Clarity": 5,
            "Highlights": -6,
            "Shadows": 6,
            "WhiteBalanceTemperature": 180,
        },
        variants=(
            _variant(
                "fresh_greens",
                ("fresh greens", "herbs", "salad"),
                ("food",),
                {"ColorBalanceGreen": 3, "Saturation": 2},
            ),
            _variant(
                "warm_table",
                ("warm table", "candlelit dinner"),
                ("warm",),
                {"WhiteBalanceTemperature": 220, "ColorBalanceRed": 2},
            ),
            _variant(
                "crispy_texture",
                ("crispy", "texture", "charred"),
                ("crisp",),
                {"Clarity": 4, "Contrast": 2},
            ),
        ),
    ),
    MainProfile(
        name="bridal_luminous",
        triggers=("bridal", "wedding", "romantic portrait", "bridal portrait"),
        intents=("bridal", "portrait"),
        adjustments={
            "Exposure": 0.25,
            "Contrast": 2,
            "Saturation": 1,
            "Clarity": -1,
            "Highlights": -6,
            "Shadows": 10,
            "WhiteBalanceTint": 1,
        },
        variants=(
            _variant(
                "ivory_dress",
                ("ivory", "dress detail", "white fabric"),
                ("bridal",),
                {"Highlights": -2, "WhiteBalanceTemperature": 80},
            ),
            _variant(
                "romantic_blush",
                ("blush", "romantic", "soft rose"),
                ("soft",),
                {"WhiteBalanceTint": 2, "ColorBalanceRed": 2},
            ),
            _variant(
                "garden_light",
                ("garden", "floral", "outdoor ceremony"),
                ("warm",),
                {"WhiteBalanceTemperature": 140, "ColorBalanceGreen": 1},
            ),
        ),
    ),
    MainProfile(
        name="street_grit",
        triggers=("street", "urban grit", "gritty", "grit"),
        intents=("street", "gritty"),
        adjustments={
            "Exposure": -0.1,
            "Contrast": 12,
            "Saturation": -1,
            "Clarity": 13,
            "Highlights": -10,
            "Shadows": 4,
        },
        variants=(
            _variant(
                "concrete_cool",
                ("concrete", "steel", "urban cool"),
                ("cool",),
                {"ColorBalanceBlue": 2, "WhiteBalanceTemperature": -120},
            ),
            _variant(
                "subway_fluoro",
                ("subway", "fluorescent", "tube light"),
                ("street",),
                {"WhiteBalanceTint": -2, "ColorBalanceGreen": 2},
            ),
            _variant(
                "night_grain",
                ("night grain", "high iso"),
                ("moody",),
                {"Contrast": 2, "Shadows": 2},
            ),
        ),
    ),
    MainProfile(
        name="fine_art_matte",
        triggers=("fine art", "matte art", "gallery print"),
        intents=("fine-art", "matte"),
        adjustments={
            "Exposure": 0.05,
            "Contrast": -1,
            "Saturation": -3,
            "Clarity": -1,
            "Highlights": -5,
            "Shadows": 8,
            "ToneCurve": "Film Standard",
        },
        variants=(
            _variant(
                "soft_chalk",
                ("chalk", "powder", "soft chalk"),
                ("soft",),
                {"Clarity": -2, "Contrast": -1},
            ),
            _variant(
                "museum_neutral",
                ("neutral art", "museum"),
                ("clean",),
                {"WhiteBalanceTemperature": -80, "WhiteBalanceTint": 0},
            ),
            _variant(
                "sepia_hint",
                ("sepia", "warm paper"),
                ("warm",),
                {"WhiteBalanceTemperature": 160, "ColorBalanceRed": 2},
            ),
        ),
    ),
    MainProfile(
        name="clean_beauty",
        triggers=("beauty", "clean beauty", "cosmetic"),
        intents=("beauty", "portrait"),
        adjustments={
            "Exposure": 0.2,
            "Contrast": 3,
            "Saturation": 2,
            "Clarity": 1,
            "Highlights": -5,
            "Shadows": 8,
            "WhiteBalanceTint": 1,
        },
        variants=(
            _variant(
                "dewy_skin",
                ("dewy", "hydrated skin"),
                ("beauty",),
                {"Highlights": -2, "WhiteBalanceTemperature": 80},
            ),
            _variant(
                "clean_studio",
                ("clean studio", "beauty studio"),
                ("clean",),
                {"Exposure": 0.1, "Contrast": -1},
            ),
            _variant(
                "soft_peach",
                ("soft peach", "apricot"),
                ("warm",),
                {"ColorBalanceRed": 2, "WhiteBalanceTint": 2},
            ),
        ),
    ),
    MainProfile(
        name="minimal_scandi",
        triggers=("scandinavian", "minimal", "minimal scandi"),
        intents=("minimal", "clean"),
        adjustments={
            "Exposure": 0.2,
            "Contrast": -1,
            "Saturation": -3,
            "Clarity": 2,
            "Highlights": -4,
            "Shadows": 8,
        },
        variants=(
            _variant(
                "cool_white",
                ("cool white", "cool neutral"),
                ("cool",),
                {"WhiteBalanceTemperature": -120, "ColorBalanceBlue": 1},
            ),
            _variant(
                "oak_warmth",
                ("oak", "wood warmth", "light wood"),
                ("warm",),
                {"WhiteBalanceTemperature": 120, "ColorBalanceRed": 1},
            ),
            _variant(
                "soft_daylight",
                ("soft daylight", "window light"),
                ("soft",),
                {"Contrast": -1, "Highlights": -2},
            ),
        ),
    ),
)


_STYLE_REFERENCE_ALIASES: dict[str, tuple[str, ...]] = {
    "tim burton": (
        "gothic fantasy",
        "cinematic portrait",
        "porcelain skin",
        "twisted whimsy",
        "moonlit blue",
    ),
    "steve mccurry": (
        "vivid documentary",
        "travel portrait",
        "rich reds",
        "warm earth",
        "natural skin",
    ),
}

_INTENSITY_LIMITS: dict[str, tuple[float, float]] = {
    "Exposure": (-1.25, 1.25),
    "Contrast": (-18.0, 24.0),
    "Saturation": (-18.0, 22.0),
    "Clarity": (-12.0, 20.0),
    "Highlights": (-35.0, 12.0),
    "Shadows": (-8.0, 24.0),
    "WhiteBalanceTemperature": (4300.0, 6800.0),
    "WhiteBalanceTint": (-10.0, 10.0),
    "ColorBalanceRed": (-10.0, 14.0),
    "ColorBalanceGreen": (-10.0, 10.0),
    "ColorBalanceBlue": (-10.0, 16.0),
}

_INTENSITY_SCALES: dict[Intensity, float] = {
    "subtle": 0.72,
    "balanced": 0.88,
    "bold": 1.0,
}


def profile_catalog() -> tuple[MainProfile, ...]:
    return _MAIN_PROFILES


def expand_style_references(prompt: str, intents: list[str] | None = None) -> PromptExpansion:
    normalized = prompt.lower()
    additions: list[str] = []
    added_intents: list[str] = []

    for alias, descriptors in _STYLE_REFERENCE_ALIASES.items():
        if alias not in normalized:
            continue
        additions.extend(descriptors)

    if not additions:
        return PromptExpansion(expanded_prompt=prompt)

    existing_intents = {intent.lower() for intent in (intents or [])}
    for descriptor in additions:
        for profile in _matched_profiles(descriptor):
            for intent in _profile_intents(profile):
                if intent.lower() not in existing_intents and intent not in added_intents:
                    added_intents.append(intent)

    deduped_additions = [item for item in additions if item.lower() not in normalized]
    if not deduped_additions:
        return PromptExpansion(expanded_prompt=prompt, added_intents=tuple(added_intents))

    expanded_prompt = f"{prompt}. Creative direction: {', '.join(deduped_additions)}."
    return PromptExpansion(expanded_prompt=expanded_prompt, added_intents=tuple(added_intents))


def apply_creative_direction(
    keys: dict[str, str | int | float],
    prompt: str,
    constraints: dict | None = None,
) -> dict[str, str | int | float]:
    updated = dict(keys)
    normalized = prompt.lower()

    matched_profiles = _matched_profiles(normalized)
    for profile in matched_profiles:
        for key, delta_or_value in _profile_adjustments(profile).items():
            current = updated.get(key)
            if isinstance(delta_or_value, str):
                updated[key] = delta_or_value
                continue
            numeric_value = float(delta_or_value)
            if isinstance(current, (int, float)):
                numeric_value += float(current)
            updated[key] = _clamp_key(key, numeric_value)

    intensity = infer_intensity(prompt, constraints)
    return _normalize_intensity(updated, matched_profiles, intensity)


def infer_intensity(prompt: str, constraints: dict | None = None) -> Intensity:
    if isinstance(constraints, dict):
        raw = constraints.get("intensity")
        if isinstance(raw, str):
            normalized = raw.strip().lower()
            if normalized in _INTENSITY_SCALES:
                return normalized

    normalized_prompt = prompt.lower()
    subtle_markers = (
        "subtle",
        "gentle",
        "light touch",
        "restrained",
        "natural",
        "softly",
    )
    bold_markers = (
        "bold",
        "strong",
        "dramatic",
        "pushed",
        "intense",
        "stylized",
    )

    if any(marker in normalized_prompt for marker in subtle_markers):
        return "subtle"
    if any(marker in normalized_prompt for marker in bold_markers):
        return "bold"
    return "balanced"


def _matched_profiles(prompt: str) -> list[MainProfile | VariantProfile]:
    normalized = prompt.lower()
    matches: list[MainProfile | VariantProfile] = []

    for profile in _MAIN_PROFILES:
        if any(trigger in normalized for trigger in profile.triggers):
            matches.append(profile)
        for variant in profile.variants:
            if any(trigger in normalized for trigger in variant.triggers):
                matches.append(variant)

    return matches


def _profile_intents(profile: MainProfile | VariantProfile) -> tuple[str, ...]:
    return profile.intents


def _profile_adjustments(profile: MainProfile | VariantProfile) -> dict[str, str | int | float]:
    return profile.adjustments


def _normalize_intensity(
    keys: dict[str, str | int | float],
    matched_profiles: list[MainProfile | VariantProfile],
    intensity: Intensity,
) -> dict[str, str | int | float]:
    if not matched_profiles:
        return keys

    normalized = dict(keys)
    profile_count = len(matched_profiles)

    if profile_count <= 2:
        profile_scale = 1.0
    elif profile_count == 3:
        profile_scale = 0.92
    elif profile_count == 4:
        profile_scale = 0.84
    else:
        profile_scale = 0.76

    intensity_scale = _INTENSITY_SCALES.get(intensity, _INTENSITY_SCALES["balanced"])
    scale = profile_scale * intensity_scale

    for key, limits in _INTENSITY_LIMITS.items():
        current = normalized.get(key)
        if not isinstance(current, (int, float)):
            continue
        scaled = float(current) * scale
        bounded = max(limits[0], min(limits[1], scaled))
        normalized[key] = _clamp_key(key, bounded)

    return normalized


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
