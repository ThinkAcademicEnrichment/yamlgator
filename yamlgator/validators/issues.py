from ..constants import *

class ValidationIssue(Enum):
    """Enumeration for all possible validation issues."""
    CIRCULAR_DEPENDENCY = "Circular dependency found: {path}"
    UNDEFINED_VARIABLE = "Warning: Undefined variable '{variable}' is found."
    UNUSED_VARIABLE = "Warning: Unused variable '{variable}' is defined but never used."


@dataclass
class ValidationResult:
    """Represents a single validation issue found in a tree."""
    issue_type: ValidationIssue
    message: str

    def __str__(self) -> str:
        """Returns the human-readable message for this validation issue."""
        return self.message