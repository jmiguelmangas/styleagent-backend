from app.core.captureone.costyle_parser import Entry
from app.core.models import SafePolicy

_WHITE_BALANCE_KEYS = {
    "WhiteBalance",
    "WhiteBalanceTemperature",
    "WhiteBalanceTint",
}


def apply_safe_policy(entries: list[Entry], policy: SafePolicy | None = None) -> list[Entry]:
    """Return a filtered entry list according to safe-policy rules."""
    effective_policy = policy or SafePolicy()

    blocked_keys: set[str] = set()
    if effective_policy.remove_lens_light_falloff:
        blocked_keys.add("LensLightFallOff")
    if effective_policy.remove_white_balance:
        blocked_keys.update(_WHITE_BALANCE_KEYS)
    if effective_policy.remove_exposure:
        blocked_keys.add("Exposure")

    return [entry for entry in entries if entry.key not in blocked_keys]
