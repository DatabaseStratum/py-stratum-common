from abc import ABC

from pystratum_common.wrapper.Wrapper import Wrapper


class NoneWrapper(Wrapper, ABC):
    """
    Wrapper method generator for stored procedures without any result set.
    """

    # ------------------------------------------------------------------------------------------------------------------
    def _return_type_hint(self) -> str:
        """
        Returns the return type hint of the wrapper method.
        """
        return 'int'

    # ------------------------------------------------------------------------------------------------------------------
    def _get_docstring_return_type(self) -> str:
        """
        Returns the return type of the wrapper methods to be used in the docstring.
        """
        return 'int'

# ----------------------------------------------------------------------------------------------------------------------
