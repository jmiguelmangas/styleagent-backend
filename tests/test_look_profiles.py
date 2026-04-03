from app.core.ai.look_profiles import apply_creative_direction, expand_style_references, profile_catalog


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
