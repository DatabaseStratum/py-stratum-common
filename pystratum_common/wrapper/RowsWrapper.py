from abc import ABC

from pystratum_common.wrapper.Wrapper import Wrapper


class RowsWrapper(Wrapper, ABC):
    """
    Wrapper method generator for stored procedures that are selecting 0, 1, or more rows.
    """

    # ------------------------------------------------------------------------------------------------------------------
    def _return_type_hint(self) -> str:
        """
        Returns the return type hint of the wrapper method.
        """
        return 'List[Dict[str, Any]]'

    # ------------------------------------------------------------------------------------------------------------------
    def _get_docstring_return_type(self) -> str:
        """
        Returns the return type of the wrapper methods to be used in the docstring.
        """
        return 'list[dict[str,*]]'

# ----------------------------------------------------------------------------------------------------------------------
