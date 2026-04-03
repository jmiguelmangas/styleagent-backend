from app.core.ai.look_profiles import (
    apply_creative_direction,
    expand_style_references,
    infer_intensity,
    profile_catalog,
)


def test_profile_catalog_contains_twenty_main_profiles_with_three_variants_each() -> None:
    catalog = profile_catalog()

    assert len(catalog) >= 20
    assert all(len(profile.variants) == 3 for profile in catalog)


def test_apply_creative_direction_mixes_main_profile_and_variant_adjustments() -> None:
    base_keys = {
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

    mixed = apply_creative_direction(
        base_keys,
        "gothic cinematic portrait with moonlit blue and porcelain skin",
    )

    assert mixed["Contrast"] > base_keys["Contrast"]
    assert mixed["WhiteBalanceTemperature"] < base_keys["WhiteBalanceTemperature"]
    assert mixed["ColorBalanceBlue"] > base_keys["ColorBalanceBlue"]
    assert mixed["ToneCurve"] == "Film Extra Shadow"


def test_expand_style_references_maps_named_reference_to_multiple_profiles() -> None:
    expansion = expand_style_references("portrait preset in the style of Steve McCurry", ["portrait"])

    assert "vivid documentary" in expansion.expanded_prompt.lower()
    assert "rich reds" in expansion.expanded_prompt.lower()
    assert "travel" in expansion.added_intents


def test_apply_creative_direction_normalizes_high_intensity_mixes() -> None:
    base_keys = {
        "Exposure": 0.2,
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

    mixed = apply_creative_direction(
        base_keys,
        "cinematic portrait with cool teal shadows, warm skin, soft rolloff and wet streets neon mood",
    )

    assert mixed["Contrast"] <= 24
    assert mixed["Clarity"] <= 20
    assert mixed["Highlights"] >= -35
    assert mixed["ColorBalanceBlue"] <= 16


def test_infer_intensity_supports_prompt_markers_and_constraints() -> None:
    assert infer_intensity("make it subtle and natural") == "subtle"
    assert infer_intensity("make it bold and dramatic") == "bold"
    assert infer_intensity("cinematic portrait") == "balanced"
    assert infer_intensity("cinematic portrait", {"intensity": "subtle"}) == "subtle"


def test_apply_creative_direction_supports_subtle_and_bold_modes() -> None:
    base_keys = {
        "Exposure": 0.2,
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
    prompt = "cinematic portrait with cool teal shadows, warm skin, soft rolloff and wet streets neon mood"

    subtle = apply_creative_direction(base_keys, prompt, {"intensity": "subtle"})
    balanced = apply_creative_direction(base_keys, prompt, {"intensity": "balanced"})
    bold = apply_creative_direction(base_keys, prompt, {"intensity": "bold"})

    assert subtle["Contrast"] <= balanced["Contrast"] <= bold["Contrast"]
    assert subtle["Clarity"] <= balanced["Clarity"] <= bold["Clarity"]
    assert subtle["ColorBalanceBlue"] <= balanced["ColorBalanceBlue"] <= bold["ColorBalanceBlue"]
