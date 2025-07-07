"""
Flask extensions initialization.
"""
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    """Base class for all database models."""
    pass

# Initialize extensions
db = SQLAlchemy(model_class=Base)