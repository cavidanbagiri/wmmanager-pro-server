
from pydantic_core import PydanticCustomError

def validate_unsigned(v: int) -> int:
    try:
        v = int(v)
        if v <= 0:
            raise PydanticCustomError(
                'unsigned_int',
                'Value must be a positive integer (≥1)',
                {'input_value': v}
            )
        return v
    except (TypeError, ValueError) as e:
        raise PydanticCustomError(
            'invalid_int',
            'Input must be a valid integer',
            {'error': str(e)}
        )