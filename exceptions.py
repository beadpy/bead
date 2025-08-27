"""
Custom exception classes for the Bead Framework.
"""

class BeadException(Exception):
    """Base class for all custom Bead framework exceptions."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class CompilerError(BeadException):
    """Exception raised for compilation errors in .bead files."""
    def __init__(self, message: str, file_path: str, line_no: int = None, col_offset: int = None):
        if line_no is not None and col_offset is not None:
            full_message = f"{message} in file '{file_path}' at line {line_no}, column {col_offset}."
        else:
            full_message = f"{message} in file '{file_path}'."
        super().__init__(full_message)

class RouterError(BeadException):
    """Exception raised for issues with routing."""
    pass