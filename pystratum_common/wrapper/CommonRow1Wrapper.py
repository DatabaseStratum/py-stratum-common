from abc import ABC

from pystratum_common.wrapper.CommonWrapper import CommonWrapper
from pystratum_common.wrapper.helper.WrapperContext import BuildContext


class CommonRow1Wrapper(CommonWrapper, ABC):
    """
    Wrapper method generator for stored procedures that are selecting 1 row.
    """

    # ------------------------------------------------------------------------------------------------------------------
    def _return_type_hint(self, context: BuildContext) -> str:
        """
        Returns the return type of the wrapper method.

        :param context: The build context.
        """
        context.code_store.add_import('typing', 'Any')
        context.code_store.add_import('typing', 'Dict')

        return 'Dict[str, Any]'

# ----------------------------------------------------------------------------------------------------------------------
