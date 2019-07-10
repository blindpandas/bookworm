from sqlalchemy import (
    Boolean,
    Column,
    Float,
    ForeignKey,
    Table,
    Text,
    Integer,
    String,
    create_engine,
)
from sqlalchemy.orm import (
    Query,
    mapper,
    class_mapper,
    reconstructor,
    relationship,
    scoped_session,
    sessionmaker,
    configure_mappers,
)
from sqlalchemy.orm.exc import UnmappedClassError
from sqlalchemy.types import DateTime
from sqlalchemy.ext.declarative import declared_attr, declarative_base
from sqlalchemy import event
import re


@event.listens_for(mapper, "mapper_configured")
def _setup_deferred_properties(mapper, class_):
    """Listen for finished mappers and apply DeferredProp
    configurations."""

    for key, value in list(class_.__dict__.items()):
        if isinstance(value, DeferredProp):
            value._config(class_, key)


class DeferredProp(object):
    """A class attribute that generates a mapped attribute 
    after mappers are configured."""

    def _setup_reverse(self, key, rel, target_cls):
        """Setup bidirectional behavior between two relationships."""

        reverse = self.kw.get("reverse")
        if reverse:
            reverse_attr = getattr(target_cls, reverse)
            if not isinstance(reverse_attr, DeferredProp):
                reverse_attr.property._add_reverse_property(key)
                rel._add_reverse_property(reverse)


class FKRelationship(DeferredProp):
    """Generates a one to many or many to one relationship."""

    def __init__(self, target, fk_col, relationship_kw=None, **kw):
        self.target = target
        self.fk_col = fk_col
        self.relationship_kw = relationship_kw or {}
        self.kw = kw

    def _config(self, cls, key):
        """Create a Column with ForeignKey as well as a relationship()."""

        target_cls = cls._decl_class_registry[self.target]

        pk_target, fk_target = self._get_pk_fk(cls, target_cls)
        pk_table = pk_target.__table__
        pk_col = list(pk_table.primary_key)[0]

        if hasattr(fk_target, self.fk_col):
            fk_col = getattr(fk_target, self.fk_col)
        else:
            fk_col = Column(self.fk_col, pk_col.type, ForeignKey(pk_col))
            setattr(fk_target, self.fk_col, fk_col)

        rel = relationship(
            target_cls,
            primaryjoin=fk_col == pk_col,
            collection_class=self.kw.pop("collection_class", list),
            **self.relationship_kw
        )
        setattr(cls, key, rel)
        self._setup_reverse(key, rel, target_cls)


class one_to_many(FKRelationship):
    """Generates a one to many relationship."""

    def _get_pk_fk(self, cls, target_cls):
        return cls, target_cls


class many_to_one(FKRelationship):
    """Generates a many to one relationship."""

    def _get_pk_fk(self, cls, target_cls):
        return target_cls, cls


class many_to_many(DeferredProp):
    """Generates a many to many relationship."""

    def __init__(self, target, tablename, local, remote, **kw):
        self.target = target
        self.tablename = tablename
        self.local = local
        self.remote = remote
        self.kw = kw

    def _config(self, cls, key):
        """Create an association table between parent/target 
        as well as a relationship()."""

        target_cls = cls._decl_class_registry[self.target]
        local_pk = list(cls.__table__.primary_key)[0]
        target_pk = list(target_cls.__table__.primary_key)[0]

        t = Table(
            self.tablename,
            cls.metadata,
            Column(self.local, ForeignKey(local_pk), primary_key=True),
            Column(self.remote, ForeignKey(target_pk), primary_key=True),
            keep_existing=True,
        )
        rel = relationship(
            target_cls,
            secondary=t,
            collection_class=self.kw.get("collection_class", set),
        )
        setattr(cls, key, rel)
        self._setup_reverse(key, rel, target_cls)


def string(size=None, **kwargs):
    """Convenience macro, return a Column with String."""
    return Column(String(size), **kwargs)


def text(**kwargs):
    """Convenience macro, return a Column with Text."""
    return Column(Text, **kwargs)


def integer(**kwargs):
    """Convenience macro, return a Column with Integer."""
    return Column(Integer, **kwargs)


def boolean(default=bool(), **kwargs):
    """Convenience macro, return a Column with Boolean."""
    return Column(Boolean, default=default, **kwargs)


def primary_key():
    return Column(Integer, primary_key=True)


def date_time(**kwargs):
    return Column(DateTime, **kwargs)


def floatingpoint():
    return Column(Float)


class _QueryProperty(object):
    """Convenience property to query a model."""

    def __get__(self, obj, type):
        try:
            mapper = class_mapper(type)
            if mapper:
                return Query(mapper, session=type.session())
        except UnmappedClassError:
            return None


class Base:
    """Base class which auto-generates tablename, surrogate 
    primary key column.
    
    Also includes a scoped session and a database generator.

    """

    @declared_attr
    def __tablename__(cls):
        """Convert CamelCase class name to underscores_between_words 
        table name."""
        name = cls.__name__
        return name[0].lower() + re.sub(
            r"([A-Z])", lambda m: "_" + m.group(0).lower(), name[1:]
        )

    id = Column(Integer, primary_key=True)
    """Surrogate 'id' primary key column."""
    query = _QueryProperty()
    """Directly query this model."""

    def __repr__(self):
        return "%s(%s)" % (
            (self.__class__.__name__),
            ", ".join(
                [
                    "%s=%r" % (key, getattr(self, key))
                    for key in sorted(self.__dict__.keys())
                    if not key.startswith("_")
                ]
            ),
        )

    @classmethod
    def get_query(cls, **kwargs):
        return cls.session().query(cls).filter_by(**kwargs)

    @classmethod
    def setup_database(
        cls,
        url,
        create=False,
        echo=False,
        autoflush=False,
        autocommit=False,
        **engine_kwargs
    ):
        """'Setup everything' method for the ultra lazy."""
        configure_mappers()
        e = create_engine(url, echo=echo, **engine_kwargs)
        if create:
            cls.metadata.create_all(e)
        cls.session = scoped_session(
            sessionmaker(e, autocommit=autocommit, autoflush=autoflush)
        )


Model = declarative_base(cls=Base)
