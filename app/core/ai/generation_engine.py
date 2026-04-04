from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


Intensity = str
CaptureOneValue = str | int | float


@dataclass(frozen=True)
class FamilyBaseline:
    family_id: str
    intents: tuple[str, ...]
    base_adjustments: dict[str, CaptureOneValue]
    intensity_multipliers: dict[Intensity, float]
    family_signatures: dict[Intensity, dict[str, CaptureOneValue]]
    family_envelopes: dict[Intensity, dict[str, tuple[float, float]]]


@dataclass(frozen=True)
class RefinementLayer:
    layer_id: str
    family_id: str | None
    intents: tuple[str, ...]
    adjustments: dict[str, CaptureOneValue]
    intensity_multipliers: dict[Intensity, float]


@dataclass(frozen=True)
class GenerationPlan:
    prompt: str
    intensity: Intensity
    family_id: str | None
    fallback_mode: str
    refinement_ids: tuple[str, ...]
    matched_profile_names: tuple[str, ...]


@dataclass(frozen=True)
class GenerationEngineConfig:
    global_intensity_scales: dict[Intensity, float]
    key_limits: dict[str, tuple[float, float]]


def compose_generation_plan(
    *,
    prompt: str,
    intensity: Intensity,
    matched_profile_names: list[str],
    matched_family_ids: list[str],
    matched_refinement_ids: list[str],
) -> GenerationPlan:
    family_id = matched_family_ids[0] if matched_family_ids else None
    fallback_mode = "family_baseline" if family_id else "generic"
    refinement_ids: list[str] = []

    for candidate in matched_family_ids[1:]:
        refinement_ids.append(f"family::{candidate}")
    refinement_ids.extend(matched_refinement_ids)

    deduped_refinements: list[str] = []
    for refinement_id in refinement_ids:
        if refinement_id not in deduped_refinements:
            deduped_refinements.append(refinement_id)

    return GenerationPlan(
        prompt=prompt,
        intensity=intensity,
        family_id=family_id,
        fallback_mode=fallback_mode,
        refinement_ids=tuple(deduped_refinements),
        matched_profile_names=tuple(matched_profile_names),
    )


def execute_generation_plan(
    *,
    base_keys: dict[str, CaptureOneValue],
    plan: GenerationPlan,
    baselines: dict[str, FamilyBaseline],
    refinements: dict[str, RefinementLayer],
    config: GenerationEngineConfig,
    clamp_key: Callable[[str, float], int | float],
) -> dict[str, CaptureOneValue]:
    original = dict(base_keys)
    updated = dict(base_keys)

    baseline = baselines.get(plan.family_id) if plan.family_id else None
    if baseline:
        _apply_adjustments(
            updated,
            baseline.base_adjustments,
            baseline.intensity_multipliers.get(plan.intensity, 1.0),
            clamp_key,
        )

    for refinement_id in plan.refinement_ids:
        if refinement_id.startswith("family::"):
            family_refinement = baselines.get(refinement_id.split("::", 1)[1])
            if family_refinement:
                _apply_adjustments(
                    updated,
                    family_refinement.base_adjustments,
                    family_refinement.intensity_multipliers.get(plan.intensity, 1.0),
                    clamp_key,
                )
            continue

        refinement = refinements.get(refinement_id)
        if refinement:
            _apply_adjustments(
                updated,
                refinement.adjustments,
                refinement.intensity_multipliers.get(plan.intensity, 1.0),
                clamp_key,
            )

    if baseline:
        signature = baseline.family_signatures.get(plan.intensity)
        if signature:
            _apply_adjustments(updated, signature, 1.0, clamp_key)

    normalized = _normalize_deltas(
        original_keys=original,
        updated_keys=updated,
        key_limits=config.key_limits,
        global_scale=config.global_intensity_scales.get(plan.intensity, 1.0),
        profile_count=max(1, len(plan.matched_profile_names)),
        clamp_key=clamp_key,
    )
    if baseline:
        normalized = _apply_family_envelope(
            normalized,
            envelope=baseline.family_envelopes.get(plan.intensity, {}),
            clamp_key=clamp_key,
        )
    return normalized


def _apply_adjustments(
    target: dict[str, CaptureOneValue],
    adjustments: dict[str, CaptureOneValue],
    scale: float,
    clamp_key: Callable[[str, float], int | float],
) -> None:
    for key, delta_or_value in adjustments.items():
        current = target.get(key)
        if isinstance(delta_or_value, str):
            target[key] = delta_or_value
            continue
        numeric_value = float(delta_or_value) * scale
        if isinstance(current, (int, float)):
            numeric_value += float(current)
        target[key] = clamp_key(key, numeric_value)


def _normalize_deltas(
    *,
    original_keys: dict[str, CaptureOneValue],
    updated_keys: dict[str, CaptureOneValue],
    key_limits: dict[str, tuple[float, float]],
    global_scale: float,
    profile_count: int,
    clamp_key: Callable[[str, float], int | float],
) -> dict[str, CaptureOneValue]:
    normalized = dict(updated_keys)
    if profile_count <= 2:
        profile_scale = 1.0
    elif profile_count == 3:
        profile_scale = 0.92
    elif profile_count == 4:
        profile_scale = 0.84
    else:
        profile_scale = 0.76

    scale = profile_scale * global_scale
    for key, limits in key_limits.items():
        current = normalized.get(key)
        if not isinstance(current, (int, float)):
            continue
        baseline = original_keys.get(key)
        if isinstance(baseline, (int, float)):
            scaled = float(baseline) + (float(current) - float(baseline)) * scale
        else:
            scaled = float(current) * scale
        bounded = max(limits[0], min(limits[1], scaled))
        normalized[key] = clamp_key(key, bounded)
    return normalized


def _apply_family_envelope(
    keys: dict[str, CaptureOneValue],
    *,
    envelope: dict[str, tuple[float, float]],
    clamp_key: Callable[[str, float], int | float],
) -> dict[str, CaptureOneValue]:
    if not envelope:
        return keys

    constrained = dict(keys)
    for key, (min_value, max_value) in envelope.items():
        current = constrained.get(key)
        if not isinstance(current, (int, float)):
            continue
        bounded = max(min_value, min(max_value, float(current)))
        constrained[key] = clamp_key(key, bounded)
    return constrained
