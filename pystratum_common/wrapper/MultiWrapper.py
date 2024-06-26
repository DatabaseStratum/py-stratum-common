from abc import ABC

from pystratum_common.wrapper.Wrapper import Wrapper


class MultiWrapper(Wrapper, ABC):
    """
    Wrapper method generator for stored procedures with designation type log.
    """

    # ------------------------------------------------------------------------------------------------------------------
    def _return_type_hint(self) -> str:
        """
        Returns the return type hint of the wrapper method.
        """
        return 'List[List[Dict[str, Any]]]'

    # ------------------------------------------------------------------------------------------------------------------
    def _get_docstring_return_type(self) -> str:
        """
        Returns the return type of the wrapper methods to be used in the docstring.
        """
        return 'list[list[dict[str,*]]]'

# ----------------------------------------------------------------------------------------------------------------------
