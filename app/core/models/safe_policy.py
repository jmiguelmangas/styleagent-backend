from pydantic import BaseModel


class SafePolicy(BaseModel):
    remove_lens_light_falloff: bool = True
    remove_white_balance: bool = True
    remove_exposure: bool = False
