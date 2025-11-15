from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, ForeignKey

Base = declarative_base()

class Board(Base):
    __tablename__ = "boards"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)

class KanbanColumn(Base):
    __tablename__ = "columns"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    board_id = Column(Integer, ForeignKey("boards.id"), nullable=False)

class Card(Base):
    __tablename__ = "cards"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    column_id = Column(Integer, ForeignKey("columns.id"), nullable=False)
