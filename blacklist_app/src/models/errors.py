class BadRequestError(Exception):
    """
    Exception raised when request validation fails.
    """
    def __init__(self, message="Bad request", errors=None):
        self.message = message
        self.errors = errors
        super().__init__(self.message)


class NotFoundError(Exception):
    """
    Exception raised when a resource is not found.
    """
    def __init__(self, message="Resource not found"):
        self.message = message
        super().__init__(self.message)


class UnauthorizedError(Exception):
    """
    Exception raised when authentication fails.
    """
    def __init__(self, message="Unauthorized"):
        self.message = message
        super().__init__(self.message)


class ConflictError(Exception):
    """
    Exception raised when there's a conflict (e.g., duplicate entry).
    """
    def __init__(self, message="Resource already exists"):
        self.message = message
        super().__init__(self.message)

