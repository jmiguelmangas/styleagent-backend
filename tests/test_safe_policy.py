from app.core.captureone import apply_safe_policy
from app.core.captureone.costyle_parser import Entry
from app.core.models import SafePolicy


def _entries() -> list[Entry]:
    return [
        Entry(key="Exposure", value="0.25", line_index=1),
        Entry(key="LensLightFallOff", value="12", line_index=2),
        Entry(key="WhiteBalance", value="AsShot", line_index=3),
        Entry(key="WhiteBalanceTemperature", value="5500", line_index=4),
        Entry(key="WhiteBalanceTint", value="2", line_index=5),
        Entry(key="Contrast", value="10", line_index=6),
    ]


def test_apply_safe_policy_removes_default_disallowed_keys() -> None:
    filtered = apply_safe_policy(_entries())
    filtered_keys = {entry.key for entry in filtered}

    assert "LensLightFallOff" not in filtered_keys
    assert "WhiteBalance" not in filtered_keys
    assert "WhiteBalanceTemperature" not in filtered_keys
    assert "WhiteBalanceTint" not in filtered_keys


def test_apply_safe_policy_keeps_unrelated_keys() -> None:
    filtered = apply_safe_policy(_entries())
    filtered_keys = {entry.key for entry in filtered}

    assert "Contrast" in filtered_keys
    assert "Exposure" in filtered_keys


def test_apply_safe_policy_is_idempotent() -> None:
    once = apply_safe_policy(_entries())
    twice = apply_safe_policy(once)

    assert once == twice


def test_apply_safe_policy_can_remove_exposure_when_configured() -> None:
    policy = SafePolicy(remove_exposure=True)
    filtered = apply_safe_policy(_entries(), policy=policy)

    filtered_keys = {entry.key for entry in filtered}
    assert "Exposure" not in filtered_keys
