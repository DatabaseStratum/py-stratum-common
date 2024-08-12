from abc import ABC

from pystratum_common.wrapper.CommonWrapper import CommonWrapper
from pystratum_common.wrapper.helper.WrapperContext import WrapperContext


class CommonRowsWrapper(CommonWrapper, ABC):
    """
    Wrapper method generator for stored procedures that are selecting 0, 1, or more rows.
    """

    # ------------------------------------------------------------------------------------------------------------------
    def _return_type_hint(self, context: WrapperContext) -> str:
        """
        Returns the return type of the wrapper method.

        :param context: The wrapper context.
        """
        context.code_store.add_import('typing', 'Any')
        context.code_store.add_import('typing', 'Dict')
        context.code_store.add_import('typing', 'List')

        return 'List[Dict[str, Any]]'

# ----------------------------------------------------------------------------------------------------------------------
