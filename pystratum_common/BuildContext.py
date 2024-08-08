from dataclasses import dataclass
from typing import Any, Dict

from pystratum_common.PythonCodeStore import PythonCodeStore


@dataclass
class BuildContext:
    """
    The build context for generating wrapper methods for invoking stored routines.
    """
    # ------------------------------------------------------------------------------------------------------------------
    code_store: PythonCodeStore
    """
    The Python code store for, well, storing the generated Python code.
    """

    routine: Dict[str, Any]
    """
    The metadata of the stored routine.
    """

# ----------------------------------------------------------------------------------------------------------------------
