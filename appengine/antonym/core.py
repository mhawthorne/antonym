class AppException(Exception): pass


class IllegalArgumentException(AppException): pass


class IllegalStateException(AppException): pass


class DataException(AppException): pass


class MissingDataException(DataException): pass


class DuplicateDataException(DataException): pass


class NotFoundException(DataException): pass