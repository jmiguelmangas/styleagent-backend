from pydantic import BaseModel
from pydantic import Field


class SafePolicy(BaseModel):
    remove_lens_light_falloff: bool = Field(
        default=True,
        description="Remove LensLightFallOff key from compiled output.",
    )
    remove_white_balance: bool = Field(
        default=True,
        description="Remove WhiteBalance, WhiteBalanceTemperature, and WhiteBalanceTint keys.",
    )
    remove_exposure: bool = Field(
        default=False,
        description="Remove Exposure key from compiled output.",
    )
