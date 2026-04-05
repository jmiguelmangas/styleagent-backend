from app.core.ai.look_profiles import (
    apply_creative_direction,
    build_generation_plan,
    expand_style_references,
    infer_intensity,
    infer_prompt_intensity,
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
    assert infer_prompt_intensity("Make it bold: kodak portra inspired portrait with natural skin") == "bold"
    assert infer_prompt_intensity("Make it bold: clean commercial portrait with restrained color") == "bold"
    assert infer_intensity("cinematic portrait") == "balanced"
    assert infer_intensity("cinematic portrait", {"intensity": "subtle"}) == "subtle"
    assert infer_prompt_intensity("Keep it natural: tokyo night portrait") == "subtle"


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
    assert subtle["Clarity"] <= bold["Clarity"]
    assert subtle["ColorBalanceBlue"] <= balanced["ColorBalanceBlue"] <= bold["ColorBalanceBlue"]


def test_portra_family_has_gentle_warm_film_signature() -> None:
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

    subtle = apply_creative_direction(
        base_keys,
        "kodak portra inspired portrait with soft highlights, gentle warmth and natural skin",
        {"intensity": "subtle"},
    )
    bold = apply_creative_direction(
        base_keys,
        "kodak portra inspired portrait with soft highlights, gentle warmth and natural skin",
        {"intensity": "bold"},
    )

    assert subtle["WhiteBalanceTemperature"] < bold["WhiteBalanceTemperature"]
    assert subtle["ColorBalanceRed"] <= bold["ColorBalanceRed"]
    assert subtle["Highlights"] >= bold["Highlights"]
    assert subtle["Contrast"] <= bold["Contrast"]


def test_tokyo_night_family_pushes_neon_signature_with_intensity() -> None:
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

    subtle = apply_creative_direction(
        base_keys,
        "tokyo night portrait with neon reflections, cool shadows and warm face tones",
        {"intensity": "subtle"},
    )
    bold = apply_creative_direction(
        base_keys,
        "tokyo night portrait with neon reflections, cool shadows and warm face tones",
        {"intensity": "bold"},
    )

    assert subtle["Exposure"] >= bold["Exposure"]
    assert subtle["Contrast"] <= bold["Contrast"]
    assert subtle["Clarity"] <= bold["Clarity"]
    assert subtle["ColorBalanceBlue"] <= bold["ColorBalanceBlue"]


def test_gothic_family_keeps_cold_progressive_envelope() -> None:
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
    prompt = "gothic fantasy portrait with moonlit blue, porcelain skin and twisted whimsy"

    subtle = apply_creative_direction(base_keys, prompt, {"intensity": "subtle"})
    balanced = apply_creative_direction(base_keys, prompt, {"intensity": "balanced"})
    bold = apply_creative_direction(base_keys, prompt, {"intensity": "bold"})

    assert subtle["Contrast"] <= balanced["Contrast"] <= bold["Contrast"]
    assert subtle["Clarity"] <= balanced["Clarity"] <= bold["Clarity"]
    assert subtle["WhiteBalanceTemperature"] >= balanced["WhiteBalanceTemperature"] >= bold["WhiteBalanceTemperature"]
    assert subtle["ColorBalanceBlue"] <= balanced["ColorBalanceBlue"] <= bold["ColorBalanceBlue"]
    assert subtle["Saturation"] >= balanced["Saturation"] >= bold["Saturation"]


def test_portra_family_keeps_gentle_monotonic_progression() -> None:
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
    prompt = "kodak portra inspired portrait with soft highlights, gentle warmth and natural skin"

    subtle = apply_creative_direction(base_keys, prompt, {"intensity": "subtle"})
    balanced = apply_creative_direction(base_keys, prompt, {"intensity": "balanced"})
    bold = apply_creative_direction(base_keys, prompt, {"intensity": "bold"})

    assert subtle["Contrast"] <= balanced["Contrast"] <= bold["Contrast"]
    assert subtle["Clarity"] <= balanced["Clarity"] <= bold["Clarity"]
    assert subtle["WhiteBalanceTemperature"] <= balanced["WhiteBalanceTemperature"] <= bold["WhiteBalanceTemperature"]
    assert subtle["ColorBalanceRed"] <= balanced["ColorBalanceRed"] <= bold["ColorBalanceRed"]
    assert subtle["Highlights"] >= balanced["Highlights"] >= bold["Highlights"]


def test_build_generation_plan_selects_primary_family_and_refinements() -> None:
    prompt = "cinematic portrait with cool teal shadows, warm skin and soft rolloff"
    plan = build_generation_plan(prompt, "balanced")

    assert plan.family_id == "cinematic_portrait"
    assert "cool_teal" in plan.refinement_ids
    assert "warm_skin" in plan.refinement_ids
    assert "soft_rolloff" in plan.refinement_ids
    assert plan.fallback_mode == "family_baseline"


def test_portra_trigger_does_not_false_match_portrait() -> None:
    prompt = "gothic fantasy portrait with moonlit blue, porcelain skin and twisted whimsy"

    plan = build_generation_plan(prompt, "balanced")

    assert plan.family_id == "gothic_fantasy"


def test_clean_beauty_family_stays_luminous_but_controlled() -> None:
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
    prompt = "clean beauty portrait with luminous skin, low color cast and soft tonal shaping"

    subtle = apply_creative_direction(base_keys, prompt, {"intensity": "subtle"})
    bold = apply_creative_direction(base_keys, prompt, {"intensity": "bold"})

    assert subtle["Exposure"] >= 0.15
    assert subtle["Clarity"] <= 7
    assert subtle["Contrast"] <= bold["Contrast"]
    assert subtle["ColorBalanceBlue"] <= -1


def test_minimal_scandi_family_stays_soft_and_neutral() -> None:
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
    prompt = "minimal scandinavian interior look with neutral tones and soft contrast"

    subtle = apply_creative_direction(base_keys, prompt, {"intensity": "subtle"})
    balanced = apply_creative_direction(base_keys, prompt, {"intensity": "balanced"})

    assert subtle["Saturation"] <= 4
    assert subtle["Contrast"] <= 4
    assert subtle["Clarity"] <= balanced["Clarity"]
    assert subtle["WhiteBalanceTemperature"] <= 5450


def test_build_generation_plan_filters_cross_family_refinements_when_family_selected() -> None:
    prompt = "drone aerial of a chalk coastline with deep cyan sea, midday glare and crisp edges"

    plan = build_generation_plan(prompt, "balanced")

    assert plan.family_id == "aerial_coastline"
    assert "cyan_sea" in plan.refinement_ids
    assert "midday_glare" in plan.refinement_ids


def test_moody_woodland_family_keeps_monotonic_progression() -> None:
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
    prompt = "moody woodland portrait with moonlit pines, ember warmth and shadowed trails"

    subtle = apply_creative_direction(base_keys, prompt, {"intensity": "subtle"})
    balanced = apply_creative_direction(base_keys, prompt, {"intensity": "balanced"})
    bold = apply_creative_direction(base_keys, prompt, {"intensity": "bold"})

    assert subtle["Contrast"] <= balanced["Contrast"] <= bold["Contrast"]
    assert subtle["Clarity"] <= balanced["Clarity"] <= bold["Clarity"]
    assert subtle["WhiteBalanceTemperature"] >= balanced["WhiteBalanceTemperature"] >= bold["WhiteBalanceTemperature"]
    assert subtle["ColorBalanceBlue"] <= balanced["ColorBalanceBlue"] <= bold["ColorBalanceBlue"]


def test_soft_film_matte_family_keeps_monotonic_progression() -> None:
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
    prompt = "soft film matte portrait with nostalgic color, gentle contrast and lifted shadows"

    subtle = apply_creative_direction(base_keys, prompt, {"intensity": "subtle"})
    balanced = apply_creative_direction(base_keys, prompt, {"intensity": "balanced"})
    bold = apply_creative_direction(base_keys, prompt, {"intensity": "bold"})

    assert subtle["Contrast"] <= balanced["Contrast"] <= bold["Contrast"]
    assert subtle["Clarity"] <= balanced["Clarity"] <= bold["Clarity"]
    assert subtle["Shadows"] <= balanced["Shadows"] <= bold["Shadows"]
    assert subtle["WhiteBalanceTemperature"] <= balanced["WhiteBalanceTemperature"] <= bold["WhiteBalanceTemperature"]


def test_emotive_matte_family_keeps_monotonic_progression() -> None:
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
    prompt = "emotive matte portrait with washed contrast, soft color and nostalgic softness"

    subtle = apply_creative_direction(base_keys, prompt, {"intensity": "subtle"})
    balanced = apply_creative_direction(base_keys, prompt, {"intensity": "balanced"})
    bold = apply_creative_direction(base_keys, prompt, {"intensity": "bold"})

    assert subtle["Contrast"] <= balanced["Contrast"] <= bold["Contrast"]
    assert subtle["Clarity"] <= balanced["Clarity"] <= bold["Clarity"]
    assert subtle["Shadows"] <= balanced["Shadows"] <= bold["Shadows"]
    assert subtle["WhiteBalanceTemperature"] <= balanced["WhiteBalanceTemperature"] <= bold["WhiteBalanceTemperature"]


def test_underwater_editorial_family_keeps_monotonic_progression() -> None:
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
    prompt = "underwater editorial portrait with aqua caustics, pearlescent skin and drifting fabric"

    subtle = apply_creative_direction(base_keys, prompt, {"intensity": "subtle"})
    balanced = apply_creative_direction(base_keys, prompt, {"intensity": "balanced"})
    bold = apply_creative_direction(base_keys, prompt, {"intensity": "bold"})

    assert subtle["Contrast"] <= balanced["Contrast"] <= bold["Contrast"]
    assert subtle["Clarity"] <= balanced["Clarity"] <= bold["Clarity"]
    assert subtle["Highlights"] >= balanced["Highlights"] >= bold["Highlights"]
    assert subtle["WhiteBalanceTemperature"] >= balanced["WhiteBalanceTemperature"] >= bold["WhiteBalanceTemperature"]
    assert subtle["ColorBalanceBlue"] <= balanced["ColorBalanceBlue"] <= bold["ColorBalanceBlue"]


def test_aerial_coastline_family_is_selected_and_progressive() -> None:
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
    prompt = "drone aerial of a chalk coastline with deep cyan sea, midday glare and crisp edges"

    plan = build_generation_plan(prompt, "balanced")
    assert plan.family_id == "aerial_coastline"

    subtle = apply_creative_direction(base_keys, prompt, {"intensity": "subtle"})
    balanced = apply_creative_direction(base_keys, prompt, {"intensity": "balanced"})
    bold = apply_creative_direction(base_keys, prompt, {"intensity": "bold"})

    assert "crisp_edges" in plan.refinement_ids
    assert "cyan_glow" not in plan.refinement_ids
    assert "soft_chalk" not in plan.refinement_ids
    assert subtle["Contrast"] <= balanced["Contrast"] <= bold["Contrast"]
    assert subtle["Clarity"] <= balanced["Clarity"] <= bold["Clarity"]
    assert subtle["Highlights"] >= balanced["Highlights"] >= bold["Highlights"]


def test_pastel_airy_family_stays_soft_but_progressive() -> None:
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
    prompt = "pastel maternity portrait with milky tones, luminous skin and gentle blush warmth"

    subtle = apply_creative_direction(base_keys, prompt, {"intensity": "subtle"})
    balanced = apply_creative_direction(base_keys, prompt, {"intensity": "balanced"})
    bold = apply_creative_direction(base_keys, prompt, {"intensity": "bold"})

    assert subtle["Contrast"] <= balanced["Contrast"] <= bold["Contrast"]
    assert subtle["Saturation"] <= balanced["Saturation"] <= bold["Saturation"]
    assert subtle["WhiteBalanceTemperature"] <= balanced["WhiteBalanceTemperature"] <= bold["WhiteBalanceTemperature"]
    assert subtle["ColorBalanceRed"] <= balanced["ColorBalanceRed"] <= bold["ColorBalanceRed"]


def test_jazz_club_family_is_selected_and_progressive() -> None:
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
    prompt = "moody jazz club portrait with red velvet light, brass glow and smoky shadows"

    plan = build_generation_plan(prompt, "balanced")
    assert plan.family_id == "jazz_club"

    subtle = apply_creative_direction(base_keys, prompt, {"intensity": "subtle"})
    balanced = apply_creative_direction(base_keys, prompt, {"intensity": "balanced"})
    bold = apply_creative_direction(base_keys, prompt, {"intensity": "bold"})

    assert subtle["Contrast"] <= balanced["Contrast"] <= bold["Contrast"]
    assert subtle["Clarity"] <= balanced["Clarity"] <= bold["Clarity"]
    assert subtle["Highlights"] >= balanced["Highlights"] >= bold["Highlights"]
