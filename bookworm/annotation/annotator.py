
from dataclasses import astuple, dataclass
from enum import IntEnum, auto

import sqlalchemy as sa

from bookworm.database.models import Book, Bookmark, Note, Quote
from bookworm.logger import logger
from bookworm.structured_text import (
    CURRENT_POSITION_MODEL_VERSION,
    LEGACY_CONTENT_HASH_VERSION,
    LEGACY_POSITION_MODEL_VERSION,
)

log = logger.getChild(__name__)
# The bakery caches query objects to avoid recompiling them into strings in every call


def _position_version_clause(model, include_unmigrated=False):
    if not include_unmigrated:
        return model.position_version == CURRENT_POSITION_MODEL_VERSION
    return sa.or_(
        model.position_version.is_(None),
        model.position_version.in_(
            (LEGACY_POSITION_MODEL_VERSION, CURRENT_POSITION_MODEL_VERSION)
        ),
    )


def _legacy_position_version_clause(model):
    return sa.or_(
        model.position_version.is_(None),
        model.position_version == LEGACY_POSITION_MODEL_VERSION,
    )


@dataclass
class AnnotationFilterCriteria:
    book_id: int = 0
    tag: str = ""
    section_title: str = ""
    content_snip: str = ""

    def any(self):
        return any(astuple(self))

    def filter_query(self, model, query):
        if not self.any():
            return query
        clauses = []
        if self.book_id is not None:
            clauses.append(model.book_id == self.book_id)
        if self.tag:
            clauses.append(model.tags.contains(self.tag))
        if self.section_title:
            clauses.append(model.section_title == self.section_title)
        if self.content_snip:
            clauses.append(model.text_column.ilike(f"%{self.content_snip}%"))
        return query.filter(sa.and_(*clauses))


class AnnotationSortCriteria(IntEnum):
    Null = auto()
    Date = auto()
    Page = auto()
    Book = auto()
    Position = auto()

    def sort_query(self, model, query, asc=True):
        if self is AnnotationSortCriteria.Null:
            return query
        sort_fn = sa.asc if asc else sa.desc
        if self is AnnotationSortCriteria.Date:
            return query.order_by(sort_fn(sa.func.coalesce(model.date_updated, model.date_created)))
        if self is AnnotationSortCriteria.Page:
            return query.order_by(sort_fn(model.page_number))
        if self is AnnotationSortCriteria.Book:
            return query.order_by(sort_fn(model.book_id))
        if self is AnnotationSortCriteria.Position:
            return query.order_by(sort_fn(model.position))


class Annotator:
    """Controller for annotations."""

    model = None
    """The model to act upon."""

    def __init__(self, reader):
        self.reader = reader
        self.session = self.model.session()

    @property
    def current_book(self):
        if not self.reader.ready:
            return None
        return self.reader.get_or_create_current_book_record()

    @property
    def current_query(self):
        return self.session.query(self.model).filter_by(
            book_id=self.current_book.id,
            position_version=CURRENT_POSITION_MODEL_VERSION,
        )

    @classmethod
    def get_books_for_model(cls, include_unmigrated=False):
        return (
            Book.query.filter(
                Book.id.in_(
                    sa.select([cls.model.book_id]).where(
                        _position_version_clause(cls.model, include_unmigrated)
                    )
                )
            )
            .order_by(Book.title.asc())
            .all()
        )

    def get_sections(self):
        return (
            self.current_query.with_entities(self.model.section_title)
            .distinct()
            .order_by(self.model.page_number)
            .all()
        )

    @classmethod
    def get_all(
        cls,
        filter_criteria=None,
        sort_criteria=AnnotationSortCriteria.Date,
        asc=False,
        include_unmigrated=False,
    ):
        model = cls.model
        query = model.query.filter(_position_version_clause(model, include_unmigrated))
        if filter_criteria is not None:
            query = filter_criteria.filter_query(model, query)
        return sort_criteria.sort_query(model, query, asc=asc).all()

    def _get_legacy_book_ids(self):
        document = self.reader.document
        if document is None:
            return []
        records = (
            Book.query.filter(Book.content_hash.is_not(None))
            .filter(
                sa.or_(
                    Book.content_hash_version.is_(None),
                    Book.content_hash_version == LEGACY_CONTENT_HASH_VERSION,
                )
            )
            .all()
        )
        records = [
            record for record in records if record.uri.format == document.uri.format
        ]
        if not records:
            return []
        legacy_content_hash = document.get_legacy_content_hash()
        if legacy_content_hash is None:
            return []
        return [
            record.id
            for record in records
            if record.content_hash == legacy_content_hash
        ]

    def _management_query(self):
        current_book_id = self.current_book.id
        legacy_book_ids = [
            book_id for book_id in self._get_legacy_book_ids() if book_id != current_book_id
        ]
        query = self.session.query(self.model)
        current_book_clause = sa.and_(
            self.model.book_id == current_book_id,
            _position_version_clause(self.model, include_unmigrated=True),
        )
        if not legacy_book_ids:
            return query.filter(current_book_clause)
        return query.filter(
            sa.or_(
                current_book_clause,
                sa.and_(
                    self.model.book_id.in_(legacy_book_ids),
                    _legacy_position_version_clause(self.model),
                ),
            )
        )

    def get_for_book(
        self,
        filter_criteria=None,
        sort_criteria=AnnotationSortCriteria.Page,
        asc=True,
        include_unmigrated=False,
    ):
        filter_criteria = filter_criteria or AnnotationFilterCriteria()
        query = self._management_query() if include_unmigrated else self.current_query
        query = filter_criteria.filter_query(self.model, query)
        return sort_criteria.sort_query(self.model, query, asc=asc).all()

    def get_for_page(self, page_number=None, asc=False):
        return self.current_query.filter_by(
            page_number=page_number or self.reader.current_page,
        )

    def get_for_section(self, section_ident=None, asc=False):
        section_ident = section_ident or self.reader.active_section.unique_identifier
        return self.current_query.filter_by(section_identifier=section_ident)

    def get(self, item_id):
        return self.session.get(self.model, item_id)

    @staticmethod
    def needs_relocation(item):
        return item.position_version in (None, LEGACY_POSITION_MODEL_VERSION)

    def relocate(self, item_id):
        item = self.get(item_id)
        if item is None or not self.needs_relocation(item):
            raise ValueError(_("Only annotations marked for repositioning can be relocated."))
        current_book = self.current_book
        if item.book_id not in {current_book.id, *self._get_legacy_book_ids()}:
            raise ValueError(_("The annotation does not belong to the current document."))

        insertion_point = self.reader.view.get_insertion_point()
        selection = self.reader.view.get_selection_range()
        has_selection = selection.start != selection.stop
        if self.model is Quote and not has_selection:
            raise ValueError(_("Select text before relocating a highlight."))

        section = (
            self.reader.document.get_section_at_position(insertion_point)
            if self.reader.document.is_single_page_document()
            else self.reader.active_section
        )
        item.book_id = current_book.id
        item.page_number = self.reader.current_page
        item.section_title = section.title
        item.section_identifier = section.unique_identifier
        item.position_version = CURRENT_POSITION_MODEL_VERSION

        if self.model is Bookmark:
            item.position = self.reader.view_to_storage_position(insertion_point)
        elif has_selection:
            storage_range = self.reader.view_to_storage_range(
                selection.start, selection.stop
            )
            item.position = storage_range.start
            item.start_pos, item.end_pos = storage_range.astuple()
        else:
            item.position = self.reader.view_to_storage_position(insertion_point)
            item.start_pos = item.end_pos = None

        self.session.add(item)
        self.session.commit()
        return item

    def get_first_after(self, page_number, pos):
        model = self.model
        clauses = (
            sa.and_(
                model.page_number == page_number,
                model.position > pos,
            ),
            model.page_number > page_number,
        )
        return (
            self.current_query
            .filter(sa.or_(*clauses))
            .order_by(model.page_number.asc(), model.position.asc())
            .first()
        )

    def get_first_before(self, page_number, pos):
        model = self.model
        clauses = (
            sa.and_(
                model.page_number == page_number,
                model.position < pos,
            ),
            model.page_number < page_number,
        )
        return (
            self.current_query
            .filter(sa.or_(*clauses))
            .order_by(model.page_number.desc())
            .order_by(model.position.desc())
            .first()
        )

    def create(self, **kwargs):
        if not self.reader.document.is_single_page_document():
            section_title = self.reader.active_section.title
        else:
            section_title = self.reader.document.get_section_at_position(
                self.reader.view.get_insertion_point()
            ).title
        kwargs.update(
            {
                "book_id": self.current_book.id,
                "page_number": self.reader.current_page,
                "section_title": section_title,
                "section_identifier": self.reader.active_section.unique_identifier,
                "position_version": CURRENT_POSITION_MODEL_VERSION,
            }
        )
        annot = self.model(**kwargs)
        self.session.add(annot)
        self.session.commit()
        return annot

    def update(self, item_id, **kwargs):
        item = self.get(item_id)
        if item is None:
            raise LookupError(f"There is no record with id={item_id}.")
        for attr, value in kwargs.items():
            setattr(item, attr, value)
        if {"position", "start_pos", "end_pos"}.intersection(kwargs):
            item.position_version = CURRENT_POSITION_MODEL_VERSION
        self.session.add(item)
        self.session.commit()

    def delete(self, item_id):
        self.session.delete(self.get(item_id))
        self.session.commit()


class Bookmarker(Annotator):
    """Bookmarks."""

    model = Bookmark


class TaggedAnnotator(Annotator):
    """Annotations which can be tagged."""

    @classmethod
    def get_tags(cls):
        cls.delete_orphan_tags()
        return [tag.title for tag in cls.model.Tag.query.order_by(cls.model.Tag.title).all()]

    @classmethod
    def delete_orphan_tags(cls):
        session = cls.model.session()
        orphan_tags = [tag for tag in cls.model.Tag.query if len(tag.items) == 0]
        for otag in orphan_tags:
            session.delete(otag)
        session.commit()


class PositionedAnnotator(TaggedAnnotator):
    """Annotations which are positioned on a specific text range"""

    def overlaps(
        self, start: int | None, end: int | None, page_number: int, position: int
    ) -> bool:
        """
        Determines whether an annotation overlaps with  a given position
        The criterias used to check for the position are the following:
        - If a selection is present, represented by start and end, then it is checked
        - If no selection is present the insertion point is used to determine if the annotation overlaps
        """
        model = self.model
        clauses = [
            sa.and_(
                model.start_pos.is_not(None),
                model.end_pos.is_not(None),
                model.start_pos == start,
                model.end_pos == end,
                model.page_number == page_number,
            ),
            sa.and_(model.page_number == page_number, model.position == position),
            sa.and_(
                model.start_pos.is_not(None),
                model.end_pos.is_not(None),
                model.page_number == page_number,
                sa.or_(
                    sa.and_(
                        model.start_pos == position,
                        model.end_pos == position,
                    ),
                    sa.and_(
                        model.start_pos <= position,
                        model.end_pos >= position,
                    ),
                ),
            ),
        ]
        return (
            self.current_query
            .filter(sa.or_(*clauses))
            .one_or_none()
            is not None
        )


class NoteTaker(PositionedAnnotator):
    """Comments."""

    model = Note

    def get_first_after(self, page_number, pos):
        """
        Finds the first comment that occurs after the given page and position.
        """
        model = self.model
        # Create an 'effective_pos' column that uses 'start_pos' for selection-based notes
        # and falls back to 'position' for single-point notes. This provides a single,
        # reliable value for sorting and comparison, regardless of the note type.
        effective_pos = sa.func.coalesce(model.start_pos, model.position)

        # Define the search criteria:
        # 1. Comments on the same page but after the current position.
        # 2. Any comment on subsequent pages.
        clauses = (
            sa.and_(
                model.page_number == page_number,
                effective_pos > pos,
            ),
            model.page_number > page_number,
        )

        return (
            self.current_query
            .filter(sa.or_(*clauses))
            # Sort first by page number, then by the effective position to find the correct next note.
            .order_by(model.page_number.asc(), effective_pos.asc())
            .first()
        )

    def get_first_before(self, page_number, pos):
        """
        Finds the first comment that occurs before the given page and position.
        """
        model = self.model
        # Similar to get_first_after, create a unified position for comparison.
        effective_pos = sa.func.coalesce(model.start_pos, model.position)

        # Define the search criteria:
        # 1. Comments on the same page but before the current position.
        # 2. Any comment on preceding pages.
        clauses = (
            sa.and_(
                model.page_number == page_number,
                effective_pos < pos,
            ),
            model.page_number < page_number,
        )

        return (
            self.current_query
            .filter(sa.or_(*clauses))
            # Sort in descending order to find the nearest previous note.
            .order_by(model.page_number.desc(), effective_pos.desc())
            .first()
        )


class Quoter(TaggedAnnotator):
    """Highlights."""

    model = Quote

    def get_first_after(self, page_number, pos):
        model = self.model
        clauses = (
            sa.and_(
                model.page_number == page_number,
                model.start_pos > pos,
            ),
            model.page_number > page_number,
        )
        return (
            self.current_query
            .filter(sa.or_(*clauses))
            .order_by(model.page_number.asc(), model.start_pos.asc())
            .first()
        )

    def get_first_before(self, page_number, pos):
        model = self.model
        clauses = (
            sa.and_(
                model.page_number == page_number,
                model.end_pos < pos,
            ),
            model.page_number < page_number,
        )
        return (
            self.current_query
            .filter(sa.or_(*clauses))
            .order_by(model.page_number.desc())
            .order_by(model.end_pos.desc())
            .first()
        )
