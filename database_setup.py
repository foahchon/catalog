from sqlalchemy import Column, ForeignKey, Integer, String, func, DateTime, Binary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
    """Class for storing user information.

    Attributes:
        id: Unique user key.
        google_id: Google ID of user.
        name: User's username on Google profile.
        email: User's e-mail address on Google profile.
        picture: URL of user's picture on Google profile.
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    google_id = Column(String(80), nullable=False)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))


class CatalogItem(Base):
    """Class for storing catalog items.

    Attributes:
        id: Unique item key.
        category_id: ID of category item belongs to.
        name: Name of item.
        description: (Ideally) brief description of item.
        user: User who created item.
        user_id: ID of user who created item.
        created_at: Time at which item was inserted into the database.
        image_blob: Blob containing image of item
                    submitted with item's name and description.
    """

    __tablename__ = "items"

    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey('categories.id'))

    name = Column(String(80), nullable=False)
    description = Column(String(500), nullable=False)

    user = relationship("User")
    user_id = Column(Integer, ForeignKey('users.id'))

    created_at = Column(DateTime, default=func.now())

    image_blob = Column(Binary, nullable=True)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description
        }


class Category(Base):
    """Class for storing item categories.

    Attributes:
        id: Unique category key.
        name: Name of category.
        items: Items belonging to category.

    """
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)

    items = relationship("CatalogItem", backref="category")

    @property
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'items': [item.serialize for item in self.items]
        }

engine = create_engine('sqlite:///catalog.db')

Base.metadata.create_all(engine)
