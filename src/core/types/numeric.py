from typing import Annotated

from pydantic import BeforeValidator

from src.core.validators.numeric import validate_unsigned

UnsignedInt = Annotated[int, BeforeValidator(validate_unsigned)]