from abc import ABC

from pystratum_common.BuildContext import BuildContext
from pystratum_common.wrapper.Wrapper import Wrapper


class MultiWrapper(Wrapper, ABC):
    """
    Wrapper method generator for stored procedures with designation type log.
    """

    # ------------------------------------------------------------------------------------------------------------------
    def _return_type_hint(self, context: BuildContext) -> str:
        """
        Returns the return type of the wrapper method.

        :param context: The build context.
        """
        context.code_store.add_import('typing', 'Any')
        context.code_store.add_import('typing', 'Dict')
        context.code_store.add_import('typing', 'List')

        return 'List[List[Dict[str, Any]]]'

# ----------------------------------------------------------------------------------------------------------------------
