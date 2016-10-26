class DataStoreError(Exception):
    """
    Base exception class for this module
    """


class NotFoundError(DataStoreError):
    """
    Raised when the entry was not found
    """


class UnexpectedResultError(DataStoreError):
    """
    Raised when  the result set returned from the database is not the expected
    value. Examples include receiving more than one result when only one is
    expected.
    """


class MissingKeyError(DataStoreError):
    """
    Raised when a new item is missing a unique name
    """


class AlreadyExistsError(DataStoreError):
    """
    Raised when trying to add an entry that already exists
    """


class CorruptAttributeError(DataStoreError):
    """
    Raised when the specified checksum of an attribute does not actually match
    the generated checksum.
    """


class XmlError(DataStoreError):
    """
    Raised when there is an error generating or parsing an XML file.
    """


class NonExistentUserError(DataStoreError):
    """
    Raised when flushing data with an non-existent user.
    """


class InvalidEntitySchemaError(DataStoreError):
    """
    Raised when an entity is being added for an invalid schema.
    (e.g. unpublished)
    """


class ConstraintError(DataStoreError):
    """
    Raised when an invalid value is set to an entity
    """
