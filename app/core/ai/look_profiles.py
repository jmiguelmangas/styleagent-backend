from __future__ import annotations

from dataclasses import dataclass
import re

from app.core.ai.generation_engine import (
    FamilyBaseline,
    GenerationEngineConfig,
    GenerationPlan,
    RefinementLayer,
    compose_generation_plan,
    execute_generation_plan,
)

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
        name="portra_film",
        triggers=("portra", "kodak portra", "portra inspired"),
        intents=("film", "portrait", "natural"),
        adjustments={
            "Exposure": 0.08,
            "Contrast": 1,
            "Saturation": 3,
            "Clarity": -1,
            "Highlights": -9,
            "Shadows": 6,
            "WhiteBalanceTemperature": 260,
            "WhiteBalanceTint": 1,
            "ColorBalanceRed": 3,
            "ColorBalanceBlue": -1,
            "ToneCurve": "Film Standard",
        },
        variants=(
            _variant(
                "soft_highlights",
                ("soft highlights", "soft highlight", "gentle highlight"),
                ("soft",),
                {"Highlights": -4, "Contrast": -1},
            ),
            _variant(
                "gentle_warmth",
                ("gentle warmth", "warmth", "warm portrait"),
                ("warm",),
                {"WhiteBalanceTemperature": 180, "ColorBalanceRed": 2, "WhiteBalanceTint": 1},
            ),
            _variant(
                "natural_skin_film",
                ("natural skin", "natural skin tones", "honest skin"),
                ("natural",),
                {"Saturation": -1, "Clarity": -1, "Highlights": -2},
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
        name="underwater_editorial",
        triggers=("underwater editorial", "aqua caustics", "pearlescent skin", "drifting fabric", "underwater portrait"),
        intents=("editorial", "cool", "stylized"),
        adjustments={
            "Exposure": 0.08,
            "Contrast": 4,
            "Saturation": 1,
            "Clarity": 3,
            "Highlights": -6,
            "Shadows": 4,
            "WhiteBalanceTemperature": -220,
            "ColorBalanceBlue": 3,
            "ToneCurve": "Film Standard",
        },
        variants=(
            _variant(
                "aqua_caustics",
                ("aqua caustics", "caustics", "aqua light"),
                ("cool",),
                {"ColorBalanceBlue": 4, "Highlights": -2, "WhiteBalanceTemperature": -180},
            ),
            _variant(
                "pearlescent_skin",
                ("pearlescent skin", "pearlescent", "iridescent skin"),
                ("portrait",),
                {"Highlights": -2, "WhiteBalanceTint": 1, "Saturation": -1},
            ),
            _variant(
                "drifting_fabric",
                ("drifting fabric", "floating fabric", "flowing fabric"),
                ("stylized",),
                {"Shadows": 2, "Clarity": 1, "Contrast": 1},
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
        name="jazz_club",
        triggers=("jazz club", "smoky shadows", "brass glow", "red velvet light"),
        intents=("moody", "portrait", "warm"),
        adjustments={
            "Exposure": -0.12,
            "Contrast": 7,
            "Saturation": 1,
            "Clarity": 4,
            "Highlights": -8,
            "Shadows": 6,
            "WhiteBalanceTemperature": -180,
            "ColorBalanceRed": 2,
            "ToneCurve": "Film Extra Shadow",
        },
        variants=(
            _variant(
                "velvet_red",
                ("red velvet", "velvet light", "deep crimson"),
                ("warm",),
                {"ColorBalanceRed": 4, "WhiteBalanceTint": 1, "Saturation": 1},
            ),
            _variant(
                "brass_glow",
                ("brass glow", "amber brass", "gold horn"),
                ("warm",),
                {"WhiteBalanceTemperature": 140, "Highlights": -2, "ColorBalanceRed": 1},
            ),
            _variant(
                "smoky_room",
                ("smoky", "smoky shadows", "club smoke"),
                ("moody",),
                {"Contrast": 2, "Shadows": 3, "Clarity": 1},
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
        name="aerial_coastline",
        triggers=("drone aerial", "aerial coastline", "coastline", "cyan sea"),
        intents=("landscape", "aerial", "coastal"),
        adjustments={
            "Exposure": 0.12,
            "Contrast": 3,
            "Saturation": 1,
            "Clarity": 2,
            "Highlights": -2,
            "Shadows": -1,
            "ColorBalanceBlue": 1,
        },
        variants=(
            _variant(
                "cyan_sea",
                ("deep cyan sea", "cyan sea", "coastal cyan"),
                ("cool",),
                {"ColorBalanceBlue": 3, "Saturation": 1, "WhiteBalanceTemperature": -120},
            ),
            _variant(
                "midday_glare",
                ("midday glare", "sun glare", "hard midday light"),
                ("clean",),
                {"Highlights": -3, "Contrast": 1, "Exposure": 0.05},
            ),
            _variant(
                "crisp_edges",
                ("crisp edges", "chalk", "cliff edge"),
                ("crisp",),
                {"Clarity": 2, "Contrast": 1},
            ),
        ),
    ),
    MainProfile(
        name="moody_woodland",
        triggers=("moody woodland", "woodland portrait", "moonlit pines", "shadowed trails", "ember warmth"),
        intents=("moody", "portrait", "woodland"),
        adjustments={
            "Exposure": -0.08,
            "Contrast": 5,
            "Saturation": -1,
            "Clarity": 4,
            "Highlights": -8,
            "Shadows": 6,
            "WhiteBalanceTemperature": -120,
            "ColorBalanceGreen": 2,
            "ToneCurve": "Film Extra Shadow",
        },
        variants=(
            _variant(
                "pine_depth",
                ("moonlit pines", "pines", "deep forest"),
                ("woodland",),
                {"ColorBalanceGreen": 2, "ColorBalanceBlue": 2, "Shadows": 2},
            ),
            _variant(
                "ember_warmth",
                ("ember warmth", "ember", "embers"),
                ("warm",),
                {"WhiteBalanceTemperature": 140, "ColorBalanceRed": 2, "Highlights": -2},
            ),
            _variant(
                "shadowed_trails",
                ("shadowed trails", "trails", "forest shadows"),
                ("moody",),
                {"Contrast": 2, "Clarity": 2, "Highlights": -3},
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
        name="soft_film_matte",
        triggers=("soft film matte", "nostalgic color", "lifted shadows", "gentle contrast"),
        intents=("film", "matte", "soft"),
        adjustments={
            "Exposure": 0.05,
            "Contrast": -1,
            "Saturation": -1,
            "Clarity": -1,
            "Highlights": -5,
            "Shadows": 8,
            "WhiteBalanceTemperature": 140,
            "ColorBalanceRed": 1,
            "ToneCurve": "Film Standard",
        },
        variants=(
            _variant(
                "nostalgic_color",
                ("nostalgic color", "nostalgic colour", "nostalgic tones"),
                ("film",),
                {"Saturation": -1, "ColorBalanceRed": 1, "WhiteBalanceTemperature": 80},
            ),
            _variant(
                "gentle_contrast",
                ("gentle contrast", "soft contrast", "low contrast"),
                ("soft",),
                {"Contrast": -1, "Clarity": -1, "Highlights": -2},
            ),
            _variant(
                "lifted_shadows",
                ("lifted shadows", "matte shadows", "lifted blacks"),
                ("matte",),
                {"Shadows": 3, "Contrast": -1, "Clarity": -1},
            ),
        ),
    ),
    MainProfile(
        name="emotive_matte",
        triggers=("emotive matte", "washed contrast", "nostalgic softness", "soft color"),
        intents=("soft", "matte", "emotive"),
        adjustments={
            "Exposure": 0.04,
            "Contrast": -2,
            "Saturation": -1,
            "Clarity": -2,
            "Highlights": -6,
            "Shadows": 8,
            "WhiteBalanceTemperature": 80,
            "ColorBalanceRed": 1,
            "ToneCurve": "Film Standard",
        },
        variants=(
            _variant(
                "washed_contrast",
                ("washed contrast", "washed", "soft fade"),
                ("matte",),
                {"Contrast": -2, "Shadows": 2},
            ),
            _variant(
                "soft_color",
                ("soft color", "soft colour", "muted color"),
                ("soft",),
                {"Saturation": -1, "WhiteBalanceTemperature": 60, "ColorBalanceRed": 1},
            ),
            _variant(
                "nostalgic_softness",
                ("nostalgic softness", "nostalgic", "memory-like"),
                ("emotive",),
                {"Clarity": -1, "Highlights": -2, "Shadows": 2},
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

_NEUTRAL_BASE_KEYS: dict[str, int | float | str] = {
    "Exposure": 0.1,
    "Contrast": 8,
    "Saturation": 6,
    "Clarity": 8,
    "Highlights": -8,
    "Shadows": 10,
    "WhiteBalanceTemperature": 5600,
    "WhiteBalanceTint": 2,
    "ColorBalanceRed": 3,
    "ColorBalanceGreen": 0,
    "ColorBalanceBlue": -2,
    "ToneCurve": "Film Standard",
}

_ANCHORED_FAMILIES: set[str] = {
    "aerial_coastline",
    "cinematic_portrait",
    "gothic_fantasy",
    "jazz_club",
    "moody_woodland",
    "pastel_airy",
    "portra_film",
    "soft_film_matte",
    "emotive_matte",
    "underwater_editorial",
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
    "subtle": 0.52,
    "balanced": 0.78,
    "bold": 1.0,
}

_MAIN_PROFILE_INTENSITY_MULTIPLIERS: dict[str, dict[Intensity, float]] = {
    "cinematic_portrait": {"subtle": 0.58, "balanced": 0.88, "bold": 1.18},
    "gothic_fantasy": {"subtle": 0.5, "balanced": 0.78, "bold": 1.02},
    "night_neon": {"subtle": 0.58, "balanced": 0.9, "bold": 1.28},
    "aerial_coastline": {"subtle": 0.48, "balanced": 0.72, "bold": 0.98},
    "jazz_club": {"subtle": 0.46, "balanced": 0.74, "bold": 1.0},
    "pastel_airy": {"subtle": 0.36, "balanced": 0.68, "bold": 0.92},
    "portra_film": {"subtle": 0.42, "balanced": 0.72, "bold": 0.98},
    "vivid_documentary": {"subtle": 0.56, "balanced": 0.82, "bold": 1.08},
    "moody_woodland": {"subtle": 0.42, "balanced": 0.72, "bold": 1.0},
    "soft_film_matte": {"subtle": 0.34, "balanced": 0.62, "bold": 0.88},
    "emotive_matte": {"subtle": 0.32, "balanced": 0.58, "bold": 0.82},
    "underwater_editorial": {"subtle": 0.42, "balanced": 0.72, "bold": 1.0},
}

_VARIANT_INTENSITY_MULTIPLIERS: dict[Intensity, float] = {
    "subtle": 0.48,
    "balanced": 0.8,
    "bold": 1.08,
}

_FAMILY_SIGNATURES: dict[str, dict[Intensity, dict[str, str | int | float]]] = {
    "cinematic_portrait": {
        "subtle": {
            "Exposure": 0.1,
            "WhiteBalanceTemperature": -120,
            "WhiteBalanceTint": 1,
            "ColorBalanceBlue": 2,
            "ColorBalanceRed": 1,
            "Highlights": -2,
            "Contrast": 1,
        },
        "balanced": {
            "Exposure": 0.15,
            "WhiteBalanceTemperature": -260,
            "WhiteBalanceTint": 2,
            "ColorBalanceBlue": 5,
            "ColorBalanceRed": 3,
            "Highlights": -5,
            "Contrast": 3,
            "Shadows": 1,
        },
        "bold": {
            "Exposure": 0.2,
            "WhiteBalanceTemperature": -420,
            "WhiteBalanceTint": 3,
            "ColorBalanceBlue": 8,
            "ColorBalanceRed": 5,
            "Highlights": -7,
            "Contrast": 5,
            "Clarity": 2,
            "Shadows": 2,
        },
    },
    "gothic_fantasy": {
        "subtle": {
            "Exposure": -0.15,
            "WhiteBalanceTemperature": -320,
            "WhiteBalanceTint": -1,
            "ColorBalanceBlue": 3,
            "ColorBalanceRed": -1,
            "Saturation": -2,
        },
        "balanced": {
            "Exposure": -0.3,
            "WhiteBalanceTemperature": -540,
            "WhiteBalanceTint": -3,
            "ColorBalanceBlue": 6,
            "ColorBalanceRed": -3,
            "Saturation": -3,
            "Highlights": -3,
        },
        "bold": {
            "Exposure": -0.45,
            "WhiteBalanceTemperature": -720,
            "WhiteBalanceTint": -5,
            "ColorBalanceBlue": 9,
            "ColorBalanceRed": -5,
            "Saturation": -4,
            "Contrast": 2,
            "Highlights": -5,
        },
    },
    "night_neon": {
        "subtle": {
            "Exposure": -0.1,
            "ColorBalanceBlue": 3,
            "WhiteBalanceTint": 1,
            "Contrast": 1,
        },
        "balanced": {
            "Exposure": -0.25,
            "ColorBalanceBlue": 6,
            "WhiteBalanceTint": -1,
            "Contrast": 4,
            "Clarity": 2,
            "Highlights": -3,
        },
        "bold": {
            "Exposure": -0.45,
            "ColorBalanceBlue": 10,
            "WhiteBalanceTint": -4,
            "Contrast": 8,
            "Clarity": 5,
            "Highlights": -6,
            "Saturation": 2,
        },
    },
    "aerial_coastline": {
        "subtle": {
            "Exposure": 0.04,
            "Contrast": -1,
            "Clarity": -1,
            "Highlights": -1,
            "ColorBalanceBlue": 1,
        },
        "balanced": {
            "Exposure": 0.08,
            "Contrast": 1,
            "Clarity": 0,
            "Highlights": -3,
            "ColorBalanceBlue": 2,
            "WhiteBalanceTemperature": -80,
        },
        "bold": {
            "Exposure": 0.12,
            "Contrast": 3,
            "Clarity": 2,
            "Highlights": -8,
            "ColorBalanceBlue": 4,
            "WhiteBalanceTemperature": -120,
            "Saturation": 1,
        },
    },
    "pastel_airy": {
        "subtle": {
            "Exposure": 0.04,
            "Contrast": -2,
            "Saturation": -1,
            "Clarity": -3,
            "WhiteBalanceTemperature": 80,
            "WhiteBalanceTint": 1,
            "ColorBalanceRed": 1,
        },
        "balanced": {
            "Exposure": 0.08,
            "Contrast": 0,
            "Clarity": -1,
            "Highlights": -2,
            "Shadows": 2,
            "WhiteBalanceTemperature": 140,
            "WhiteBalanceTint": 2,
            "ColorBalanceRed": 2,
        },
        "bold": {
            "Exposure": 0.12,
            "Contrast": 1,
            "Saturation": 1,
            "Clarity": 0,
            "Highlights": -3,
            "Shadows": 3,
            "WhiteBalanceTemperature": 220,
            "WhiteBalanceTint": 3,
            "ColorBalanceRed": 3,
        },
    },
    "jazz_club": {
        "subtle": {
            "Exposure": -0.04,
            "Contrast": 1,
            "Saturation": -1,
            "Clarity": 0,
            "Highlights": -2,
            "WhiteBalanceTemperature": -160,
            "ColorBalanceRed": 2,
        },
        "balanced": {
            "Exposure": -0.08,
            "Contrast": 3,
            "Saturation": 0,
            "Clarity": 1,
            "Highlights": -4,
            "WhiteBalanceTemperature": -260,
            "ColorBalanceRed": 3,
        },
        "bold": {
            "Exposure": -0.14,
            "Contrast": 5,
            "Saturation": 1,
            "Clarity": 2,
            "Highlights": -7,
            "WhiteBalanceTemperature": -360,
            "ColorBalanceRed": 4,
            "Shadows": 2,
        },
    },
    "portra_film": {
        "subtle": {
            "Exposure": 0.05,
            "WhiteBalanceTemperature": 120,
            "ColorBalanceRed": 1,
            "Highlights": -2,
            "Contrast": -1,
            "Clarity": -4,
        },
        "balanced": {
            "Exposure": 0.1,
            "WhiteBalanceTemperature": 240,
            "ColorBalanceRed": 2,
            "Highlights": -4,
            "Contrast": 1,
            "Saturation": 1,
            "Clarity": 0,
        },
        "bold": {
            "Exposure": 0.15,
            "WhiteBalanceTemperature": 360,
            "ColorBalanceRed": 3,
            "Highlights": -6,
            "Contrast": 2,
            "Saturation": 2,
            "Clarity": 1,
        },
    },
    "vivid_documentary": {
        "subtle": {
            "Contrast": 1,
            "Saturation": 1,
            "ColorBalanceRed": 2,
        },
        "balanced": {
            "Contrast": 3,
            "Saturation": 3,
            "ColorBalanceRed": 4,
            "Clarity": 1,
        },
        "bold": {
            "Contrast": 5,
            "Saturation": 5,
            "ColorBalanceRed": 6,
            "Clarity": 2,
            "WhiteBalanceTemperature": 180,
        },
    },
    "moody_woodland": {
        "subtle": {
            "Exposure": -0.02,
            "Contrast": 1,
            "Clarity": 0,
            "Highlights": -2,
            "WhiteBalanceTemperature": -80,
            "ColorBalanceGreen": 1,
        },
        "balanced": {
            "Exposure": -0.08,
            "Contrast": 3,
            "Clarity": 1,
            "Highlights": -5,
            "WhiteBalanceTemperature": -220,
            "ColorBalanceGreen": 2,
            "ColorBalanceRed": 1,
        },
        "bold": {
            "Exposure": -0.18,
            "Contrast": 7,
            "Clarity": 3,
            "Highlights": -9,
            "WhiteBalanceTemperature": -520,
            "ColorBalanceGreen": 3,
            "ColorBalanceBlue": 4,
            "ColorBalanceRed": 2,
            "ToneCurve": "Film Extra Shadow",
        },
    },
    "soft_film_matte": {
        "subtle": {
            "Exposure": 0.03,
            "Contrast": -1,
            "Clarity": -2,
            "Shadows": 1,
            "WhiteBalanceTemperature": 60,
        },
        "balanced": {
            "Exposure": 0.05,
            "Contrast": 0,
            "Clarity": -1,
            "Shadows": 3,
            "Highlights": -2,
            "WhiteBalanceTemperature": 120,
            "ColorBalanceRed": 1,
        },
        "bold": {
            "Exposure": 0.08,
            "Contrast": 2,
            "Clarity": 0,
            "Shadows": 5,
            "Highlights": -4,
            "WhiteBalanceTemperature": 180,
            "ColorBalanceRed": 2,
        },
    },
    "emotive_matte": {
        "subtle": {
            "Exposure": 0.03,
            "Contrast": -2,
            "Clarity": -2,
            "Shadows": 2,
            "WhiteBalanceTemperature": 40,
        },
        "balanced": {
            "Exposure": 0.05,
            "Contrast": -1,
            "Clarity": -1,
            "Shadows": 4,
            "Highlights": -2,
            "WhiteBalanceTemperature": 100,
            "ColorBalanceRed": 1,
        },
        "bold": {
            "Exposure": 0.07,
            "Contrast": 1,
            "Clarity": 0,
            "Shadows": 6,
            "Highlights": -4,
            "WhiteBalanceTemperature": 180,
            "ColorBalanceRed": 2,
        },
    },
    "underwater_editorial": {
        "subtle": {
            "Exposure": 0.03,
            "Contrast": 1,
            "Clarity": 1,
            "Highlights": -2,
            "WhiteBalanceTemperature": -140,
            "ColorBalanceBlue": 2,
        },
        "balanced": {
            "Exposure": 0.06,
            "Contrast": 3,
            "Clarity": 2,
            "Highlights": -4,
            "WhiteBalanceTemperature": -260,
            "ColorBalanceBlue": 5,
        },
        "bold": {
            "Exposure": 0.1,
            "Contrast": 6,
            "Clarity": 4,
            "Highlights": -6,
            "WhiteBalanceTemperature": -420,
            "ColorBalanceBlue": 8,
            "Shadows": 2,
        },
    },
}

_FAMILY_ENVELOPES: dict[str, dict[Intensity, dict[str, tuple[float, float]]]] = {
    "gothic_fantasy": {
        "subtle": {
            "Contrast": (4.0, 8.0),
            "Saturation": (-4.0, -1.0),
            "Clarity": (0.0, 4.0),
            "Highlights": (-22.0, -12.0),
            "WhiteBalanceTemperature": (3800.0, 4600.0),
            "ColorBalanceRed": (-4.0, 0.0),
            "ColorBalanceBlue": (8.0, 14.0),
        },
        "balanced": {
            "Contrast": (8.0, 14.0),
            "Saturation": (-6.0, -2.0),
            "Clarity": (2.0, 7.0),
            "Highlights": (-30.0, -18.0),
            "WhiteBalanceTemperature": (3500.0, 4300.0),
            "ColorBalanceRed": (-5.0, -1.0),
            "ColorBalanceBlue": (10.0, 16.0),
        },
        "bold": {
            "Contrast": (14.0, 22.0),
            "Saturation": (-7.0, -2.0),
            "Clarity": (5.0, 10.0),
            "Highlights": (-38.0, -24.0),
            "WhiteBalanceTemperature": (3200.0, 4000.0),
            "ColorBalanceRed": (-6.0, -2.0),
            "ColorBalanceBlue": (12.0, 18.0),
        },
    },
    "portra_film": {
        "subtle": {
            "Contrast": (3.0, 6.0),
            "Saturation": (5.0, 8.0),
            "Clarity": (0.0, 4.0),
            "Highlights": (-18.0, -12.0),
            "WhiteBalanceTemperature": (5900.0, 6200.0),
            "ColorBalanceRed": (4.0, 7.0),
            "ColorBalanceBlue": (-5.0, -1.0),
        },
        "balanced": {
            "Contrast": (6.0, 9.0),
            "Saturation": (7.0, 10.0),
            "Clarity": (4.0, 6.0),
            "Highlights": (-24.0, -16.0),
            "WhiteBalanceTemperature": (6100.0, 6400.0),
            "ColorBalanceRed": (6.0, 9.0),
            "ColorBalanceBlue": (-4.0, 0.0),
        },
        "bold": {
            "Contrast": (8.0, 12.0),
            "Saturation": (8.0, 12.0),
            "Clarity": (7.0, 8.0),
            "Highlights": (-32.0, -22.0),
            "WhiteBalanceTemperature": (6300.0, 6700.0),
            "ColorBalanceRed": (8.0, 12.0),
            "ColorBalanceBlue": (-4.0, 1.0),
        },
    },
    "aerial_coastline": {
        "subtle": {
            "Contrast": (6.0, 8.0),
            "Saturation": (5.0, 7.0),
            "Clarity": (6.0, 7.0),
            "Highlights": (-8.0, -6.0),
            "Shadows": (7.0, 9.0),
            "WhiteBalanceTemperature": (5450.0, 5580.0),
            "ColorBalanceBlue": (-1.0, 1.0),
        },
        "balanced": {
            "Contrast": (8.0, 10.0),
            "Saturation": (6.0, 8.0),
            "Clarity": (7.0, 8.0),
            "Highlights": (-14.0, -9.0),
            "Shadows": (9.0, 12.0),
            "WhiteBalanceTemperature": (5350.0, 5500.0),
            "ColorBalanceBlue": (0.0, 2.0),
        },
        "bold": {
            "Contrast": (11.0, 14.0),
            "Saturation": (8.0, 11.0),
            "Clarity": (8.0, 10.0),
            "Highlights": (-24.0, -16.0),
            "Shadows": (13.0, 17.0),
            "WhiteBalanceTemperature": (6100.0, 6500.0),
            "ColorBalanceBlue": (1.0, 4.0),
        },
    },
    "pastel_airy": {
        "subtle": {
            "Contrast": (4.0, 5.0),
            "Saturation": (5.0, 6.0),
            "Clarity": (4.0, 5.0),
            "Highlights": (-12.0, -8.0),
            "Shadows": (10.0, 13.0),
            "WhiteBalanceTemperature": (5640.0, 5740.0),
            "WhiteBalanceTint": (2.0, 3.0),
            "ColorBalanceRed": (4.0, 5.0),
        },
        "balanced": {
            "Contrast": (7.0, 9.0),
            "Saturation": (6.0, 7.0),
            "Clarity": (6.0, 7.0),
            "Highlights": (-12.0, -9.0),
            "Shadows": (14.0, 17.0),
            "WhiteBalanceTemperature": (5740.0, 5820.0),
            "WhiteBalanceTint": (4.0, 5.0),
            "ColorBalanceRed": (6.0, 7.0),
        },
        "bold": {
            "Contrast": (9.0, 10.0),
            "Saturation": (7.0, 9.0),
            "Clarity": (7.0, 8.0),
            "Highlights": (-16.0, -12.0),
            "Shadows": (18.0, 21.0),
            "WhiteBalanceTemperature": (5840.0, 5940.0),
            "WhiteBalanceTint": (5.0, 7.0),
            "ColorBalanceRed": (8.0, 9.0),
        },
    },
    "jazz_club": {
        "subtle": {
            "Contrast": (8.0, 11.0),
            "Saturation": (4.0, 6.0),
            "Clarity": (8.0, 10.0),
            "Highlights": (-14.0, -10.0),
            "Shadows": (12.0, 14.0),
            "WhiteBalanceTemperature": (5400.0, 5650.0),
            "ColorBalanceRed": (4.0, 6.0),
            "ColorBalanceBlue": (-1.0, 1.0),
        },
        "balanced": {
            "Contrast": (12.0, 15.0),
            "Saturation": (4.0, 7.0),
            "Clarity": (9.0, 12.0),
            "Highlights": (-20.0, -15.0),
            "Shadows": (14.0, 17.0),
            "WhiteBalanceTemperature": (4700.0, 5300.0),
            "ColorBalanceRed": (4.0, 7.0),
            "ColorBalanceBlue": (2.0, 6.0),
        },
        "bold": {
            "Contrast": (18.0, 22.0),
            "Saturation": (6.0, 9.0),
            "Clarity": (12.0, 16.0),
            "Highlights": (-28.0, -22.0),
            "Shadows": (18.0, 21.0),
            "WhiteBalanceTemperature": (3900.0, 4600.0),
            "ColorBalanceRed": (5.0, 9.0),
            "ColorBalanceBlue": (6.0, 11.0),
        },
    },
    "moody_woodland": {
        "subtle": {
            "Contrast": (7.0, 9.0),
            "Saturation": (4.0, 6.0),
            "Clarity": (6.0, 8.0),
            "Highlights": (-13.0, -10.0),
            "Shadows": (11.0, 13.0),
            "WhiteBalanceTemperature": (5600.0, 5850.0),
            "ColorBalanceRed": (3.0, 5.0),
            "ColorBalanceBlue": (-3.0, 0.0),
        },
        "balanced": {
            "Contrast": (10.0, 13.0),
            "Saturation": (4.0, 7.0),
            "Clarity": (8.0, 10.0),
            "Highlights": (-18.0, -14.0),
            "Shadows": (12.0, 15.0),
            "WhiteBalanceTemperature": (5000.0, 5600.0),
            "ColorBalanceRed": (4.0, 7.0),
            "ColorBalanceBlue": (0.0, 5.0),
        },
        "bold": {
            "Contrast": (16.0, 22.0),
            "Saturation": (-3.0, 3.0),
            "Clarity": (9.0, 12.0),
            "Highlights": (-28.0, -22.0),
            "Shadows": (14.0, 18.0),
            "WhiteBalanceTemperature": (3600.0, 4500.0),
            "ColorBalanceRed": (-2.0, 2.0),
            "ColorBalanceBlue": (12.0, 18.0),
        },
    },
    "soft_film_matte": {
        "subtle": {
            "Contrast": (4.0, 6.0),
            "Saturation": (4.0, 6.0),
            "Clarity": (4.0, 5.0),
            "Highlights": (-12.0, -9.0),
            "Shadows": (10.0, 12.0),
            "WhiteBalanceTemperature": (5640.0, 5740.0),
            "ColorBalanceRed": (3.0, 4.0),
        },
        "balanced": {
            "Contrast": (6.0, 8.0),
            "Saturation": (4.0, 6.0),
            "Clarity": (5.0, 6.0),
            "Highlights": (-14.0, -11.0),
            "Shadows": (12.0, 14.0),
            "WhiteBalanceTemperature": (5720.0, 5840.0),
            "ColorBalanceRed": (4.0, 5.0),
        },
        "bold": {
            "Contrast": (8.0, 10.0),
            "Saturation": (5.0, 7.0),
            "Clarity": (6.0, 8.0),
            "Highlights": (-18.0, -14.0),
            "Shadows": (14.0, 16.0),
            "WhiteBalanceTemperature": (5820.0, 5980.0),
            "ColorBalanceRed": (5.0, 7.0),
        },
    },
    "emotive_matte": {
        "subtle": {
            "Contrast": (4.0, 5.0),
            "Saturation": (4.0, 5.0),
            "Clarity": (4.0, 5.0),
            "Highlights": (-12.0, -9.0),
            "Shadows": (10.0, 12.0),
            "WhiteBalanceTemperature": (5620.0, 5720.0),
            "ColorBalanceRed": (3.0, 4.0),
        },
        "balanced": {
            "Contrast": (5.0, 7.0),
            "Saturation": (4.0, 5.0),
            "Clarity": (5.0, 6.0),
            "Highlights": (-16.0, -12.0),
            "Shadows": (12.0, 14.0),
            "WhiteBalanceTemperature": (5680.0, 5800.0),
            "ColorBalanceRed": (3.0, 5.0),
        },
        "bold": {
            "Contrast": (8.0, 10.0),
            "Saturation": (4.0, 5.0),
            "Clarity": (6.0, 7.0),
            "Highlights": (-20.0, -16.0),
            "Shadows": (15.0, 17.0),
            "WhiteBalanceTemperature": (5760.0, 5920.0),
            "ColorBalanceRed": (5.0, 6.0),
        },
    },
    "underwater_editorial": {
        "subtle": {
            "Contrast": (8.0, 10.0),
            "Saturation": (5.0, 6.0),
            "Clarity": (8.0, 10.0),
            "Highlights": (-12.0, -10.0),
            "Shadows": (10.0, 12.0),
            "WhiteBalanceTemperature": (5480.0, 5620.0),
            "ColorBalanceBlue": (-1.0, 2.0),
            "ColorBalanceRed": (2.0, 4.0),
        },
        "balanced": {
            "Contrast": (11.0, 13.0),
            "Saturation": (6.0, 8.0),
            "Clarity": (10.0, 12.0),
            "Highlights": (-17.0, -14.0),
            "Shadows": (13.0, 15.0),
            "WhiteBalanceTemperature": (5300.0, 5480.0),
            "ColorBalanceBlue": (1.0, 5.0),
            "ColorBalanceRed": (2.0, 4.0),
        },
        "bold": {
            "Contrast": (14.0, 17.0),
            "Saturation": (6.0, 8.0),
            "Clarity": (13.0, 15.0),
            "Highlights": (-21.0, -18.0),
            "Shadows": (15.0, 18.0),
            "WhiteBalanceTemperature": (5100.0, 5360.0),
            "ColorBalanceBlue": (4.0, 8.0),
            "ColorBalanceRed": (2.0, 4.0),
        },
    },
    "crisp_winter": {
        "subtle": {
            "Contrast": (8.0, 10.0),
            "Saturation": (4.0, 5.0),
            "Clarity": (10.0, 12.0),
            "Highlights": (-12.0, -9.0),
            "Shadows": (11.0, 13.0),
            "WhiteBalanceTemperature": (5480.0, 5560.0),
            "ColorBalanceBlue": (-1.0, 0.0),
        },
        "balanced": {
            "Contrast": (12.0, 14.0),
            "Saturation": (5.0, 6.0),
            "Clarity": (12.0, 14.0),
            "Highlights": (-16.0, -13.0),
            "Shadows": (13.0, 15.0),
            "WhiteBalanceTemperature": (5400.0, 5480.0),
            "ColorBalanceBlue": (0.0, 1.0),
        },
        "bold": {
            "Contrast": (15.0, 18.0),
            "Saturation": (5.0, 7.0),
            "Clarity": (15.0, 18.0),
            "Highlights": (-20.0, -16.0),
            "Shadows": (15.0, 18.0),
            "WhiteBalanceTemperature": (5320.0, 5420.0),
            "ColorBalanceBlue": (1.0, 3.0),
        },
    },
    "food_rich_color": {
        "subtle": {
            "Contrast": (9.0, 11.0),
            "Saturation": (6.0, 7.0),
            "Clarity": (8.0, 10.0),
            "Highlights": (-11.0, -9.0),
            "Shadows": (11.0, 13.0),
            "WhiteBalanceTemperature": (5700.0, 5850.0),
            "ColorBalanceRed": (4.0, 6.0),
        },
        "balanced": {
            "Contrast": (11.0, 13.0),
            "Saturation": (7.0, 9.0),
            "Clarity": (10.0, 12.0),
            "Highlights": (-13.0, -11.0),
            "Shadows": (13.0, 15.0),
            "WhiteBalanceTemperature": (5820.0, 5950.0),
            "ColorBalanceRed": (5.0, 8.0),
        },
        "bold": {
            "Contrast": (13.0, 16.0),
            "Saturation": (8.0, 11.0),
            "Clarity": (12.0, 15.0),
            "Highlights": (-16.0, -13.0),
            "Shadows": (15.0, 18.0),
            "WhiteBalanceTemperature": (5940.0, 6100.0),
            "ColorBalanceRed": (7.0, 10.0),
        },
    },
    "clean_commercial": {
        "subtle": {
            "Contrast": (9.0, 10.0),
            "Saturation": (6.0, 7.0),
            "Clarity": (9.0, 10.0),
            "Highlights": (-12.0, -10.0),
            "Shadows": (10.0, 12.0),
            "WhiteBalanceTemperature": (5520.0, 5600.0),
        },
        "balanced": {
            "Contrast": (11.0, 13.0),
            "Saturation": (7.0, 8.0),
            "Clarity": (11.0, 12.0),
            "Highlights": (-14.0, -12.0),
            "Shadows": (12.0, 14.0),
            "WhiteBalanceTemperature": (5560.0, 5630.0),
        },
        "bold": {
            "Contrast": (13.0, 15.0),
            "Saturation": (7.0, 9.0),
            "Clarity": (13.0, 15.0),
            "Highlights": (-18.0, -14.0),
            "Shadows": (14.0, 17.0),
            "WhiteBalanceTemperature": (5580.0, 5660.0),
        },
    },
    "travel_earth": {
        "subtle": {
            "Contrast": (9.0, 11.0),
            "Saturation": (7.0, 8.0),
            "Clarity": (9.0, 11.0),
            "Highlights": (-11.0, -9.0),
            "Shadows": (11.0, 13.0),
            "WhiteBalanceTemperature": (5680.0, 5800.0),
            "ColorBalanceRed": (5.0, 7.0),
        },
        "balanced": {
            "Contrast": (10.0, 12.0),
            "Saturation": (8.0, 9.0),
            "Clarity": (11.0, 13.0),
            "Highlights": (-14.0, -11.0),
            "Shadows": (13.0, 16.0),
            "WhiteBalanceTemperature": (5780.0, 5920.0),
            "ColorBalanceRed": (7.0, 9.0),
        },
        "bold": {
            "Contrast": (12.0, 15.0),
            "Saturation": (9.0, 12.0),
            "Clarity": (13.0, 16.0),
            "Highlights": (-18.0, -14.0),
            "Shadows": (16.0, 20.0),
            "WhiteBalanceTemperature": (5900.0, 6080.0),
            "ColorBalanceRed": (8.0, 12.0),
        },
    },
    "editorial_fashion": {
        "subtle": {
            "Contrast": (9.0, 11.0),
            "Saturation": (5.0, 6.0),
            "Clarity": (9.0, 11.0),
            "Highlights": (-13.0, -11.0),
            "Shadows": (10.0, 12.0),
            "WhiteBalanceTemperature": (5500.0, 5650.0),
        },
        "balanced": {
            "Contrast": (11.0, 13.0),
            "Saturation": (6.0, 7.0),
            "Clarity": (11.0, 13.0),
            "Highlights": (-15.0, -12.0),
            "Shadows": (12.0, 14.0),
            "WhiteBalanceTemperature": (5400.0, 5580.0),
        },
        "bold": {
            "Contrast": (13.0, 16.0),
            "Saturation": (7.0, 9.0),
            "Clarity": (13.0, 15.0),
            "Highlights": (-18.0, -14.0),
            "Shadows": (14.0, 17.0),
            "WhiteBalanceTemperature": (5300.0, 5500.0),
        },
    },
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
    intensity = infer_intensity(prompt, constraints)
    matched_profiles = _matched_profiles(prompt.lower())
    family_id = None
    if isinstance(constraints, dict):
        raw_family_id = constraints.get("family_id")
        if isinstance(raw_family_id, str) and raw_family_id.strip():
            family_id = raw_family_id.strip()

    if family_id:
        matched_refinement_ids = [profile.name for profile in matched_profiles if isinstance(profile, VariantProfile)]
        plan = build_generation_plan_from_selection(
            prompt=prompt,
            intensity=intensity,
            family_id=family_id,
            refinement_ids=matched_refinement_ids,
        )
    else:
        plan = build_generation_plan(prompt, intensity, matched_profiles)
    return apply_generation_plan(keys, plan)


def apply_generation_plan(
    keys: dict[str, str | int | float],
    plan: GenerationPlan,
) -> dict[str, str | int | float]:
    effective_base_keys = _resolve_base_keys_for_plan(keys, plan)
    return execute_generation_plan(
        base_keys=effective_base_keys,
        plan=plan,
        baselines=_baseline_registry(),
        refinements=_refinement_registry(),
        config=GenerationEngineConfig(
            global_intensity_scales=_INTENSITY_SCALES,
            key_limits=_INTENSITY_LIMITS,
        ),
        clamp_key=_clamp_key,
    )


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


def build_generation_plan_from_selection(
    prompt: str,
    intensity: Intensity,
    family_id: str | None = None,
    refinement_ids: list[str] | tuple[str, ...] | None = None,
) -> GenerationPlan:
    baselines = _baseline_registry()
    refinements = _refinement_registry()
    normalized_family_id = family_id if family_id in baselines else None

    deduped_refinements: list[str] = []
    for refinement_id in refinement_ids or ():
        if refinement_id in refinements and refinement_id not in deduped_refinements:
            deduped_refinements.append(refinement_id)

    matched_profile_names: list[str] = []
    if normalized_family_id:
        matched_profile_names.append(normalized_family_id)
    matched_profile_names.extend(deduped_refinements)

    return GenerationPlan(
        prompt=prompt,
        intensity=intensity,
        family_id=normalized_family_id,
        fallback_mode="family_baseline" if normalized_family_id else "generic",
        refinement_ids=tuple(deduped_refinements),
        matched_profile_names=tuple(matched_profile_names),
    )


def known_family_ids() -> tuple[str, ...]:
    return tuple(profile.name for profile in _MAIN_PROFILES)


def known_refinement_ids() -> tuple[str, ...]:
    return tuple(variant.name for profile in _MAIN_PROFILES for variant in profile.variants)


def build_generation_plan(
    prompt: str,
    intensity: Intensity,
    matched_profiles: list[MainProfile | VariantProfile] | None = None,
) -> GenerationPlan:
    profiles = matched_profiles if matched_profiles is not None else _matched_profiles(prompt.lower())
    matched_family_ids = [profile.name for profile in profiles if isinstance(profile, MainProfile)]
    primary_family_id = matched_family_ids[0] if matched_family_ids else None
    matched_refinement_ids = [profile.name for profile in profiles if isinstance(profile, VariantProfile)]
    if primary_family_id:
        allowed_refinement_ids = {
            variant.name for profile in _MAIN_PROFILES if profile.name == primary_family_id for variant in profile.variants
        }
        matched_refinement_ids = [refinement_id for refinement_id in matched_refinement_ids if refinement_id in allowed_refinement_ids]
        matched_profile_names = [primary_family_id, *matched_refinement_ids]
    else:
        matched_profile_names = [profile.name for profile in profiles]
    return compose_generation_plan(
        prompt=prompt,
        intensity=intensity,
        matched_profile_names=matched_profile_names,
        matched_family_ids=matched_family_ids,
        matched_refinement_ids=matched_refinement_ids,
    )


def _matched_profiles(prompt: str) -> list[MainProfile | VariantProfile]:
    normalized = prompt.lower()
    matches: list[MainProfile | VariantProfile] = []

    for profile in _MAIN_PROFILES:
        if any(_trigger_matches(normalized, trigger) for trigger in profile.triggers):
            matches.append(profile)
        for variant in profile.variants:
            if any(_trigger_matches(normalized, trigger) for trigger in variant.triggers):
                matches.append(variant)

    return matches


def _trigger_matches(prompt: str, trigger: str) -> bool:
    normalized_trigger = trigger.lower().strip()
    if not normalized_trigger:
        return False
    if " " in normalized_trigger:
        return normalized_trigger in prompt
    pattern = rf"(?<![a-z0-9]){re.escape(normalized_trigger)}(?![a-z0-9])"
    return re.search(pattern, prompt) is not None


def _profile_intents(profile: MainProfile | VariantProfile) -> tuple[str, ...]:
    return profile.intents


def _profile_adjustments(profile: MainProfile | VariantProfile) -> dict[str, str | int | float]:
    return profile.adjustments


def _baseline_registry() -> dict[str, FamilyBaseline]:
    return {
        profile.name: FamilyBaseline(
            family_id=profile.name,
            intents=profile.intents,
            base_adjustments=profile.adjustments,
            intensity_multipliers=_MAIN_PROFILE_INTENSITY_MULTIPLIERS.get(
                profile.name, {level: _INTENSITY_SCALES[level] for level in _INTENSITY_SCALES}
            ),
            family_signatures=_FAMILY_SIGNATURES.get(profile.name, {}),
            family_envelopes=_FAMILY_ENVELOPES.get(profile.name, {}),
        )
        for profile in _MAIN_PROFILES
    }


def _refinement_registry() -> dict[str, RefinementLayer]:
    layers: dict[str, RefinementLayer] = {}
    for profile in _MAIN_PROFILES:
        for variant in profile.variants:
            layers[variant.name] = RefinementLayer(
                layer_id=variant.name,
                family_id=profile.name,
                intents=variant.intents,
                adjustments=variant.adjustments,
                intensity_multipliers=_VARIANT_INTENSITY_MULTIPLIERS,
            )
    return layers


def _resolve_base_keys_for_plan(
    keys: dict[str, str | int | float],
    plan: GenerationPlan,
) -> dict[str, str | int | float]:
    if plan.family_id not in _ANCHORED_FAMILIES:
        return dict(keys)

    anchored = dict(_NEUTRAL_BASE_KEYS)
    for key, value in keys.items():
        if key not in anchored:
            anchored[key] = value
    return anchored


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
