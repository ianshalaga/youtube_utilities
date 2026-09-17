'''
Convención de Naming ORM

- Las clases ORM representan una entidad individual → singular
- Las tablas representan colecciones → plural
- Los nombres de relaciones siguen el plural cuando corresponda
'''

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
