from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class BaseORMModel(DeclarativeBase):
    __enabled__ = True
