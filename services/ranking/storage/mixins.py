import uuid
from sqlalchemy import Column, String


class WithCode:
    """
    Mixin para entidades con identificador público estable (UUID).
    """

    code = Column(
        String(36),
        unique=True,
        nullable=False,
        default=lambda: str(uuid.uuid4())
    )
