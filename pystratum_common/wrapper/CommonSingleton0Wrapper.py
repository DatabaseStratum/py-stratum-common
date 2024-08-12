from abc import ABC

from pystratum_common.wrapper.CommonWrapper import CommonWrapper
from pystratum_common.wrapper.helper.WrapperContext import WrapperContext


class CommonSingleton0Wrapper(CommonWrapper, ABC):
    """
    Wrapper method generator for stored procedures that are selecting 0 or 1 row with one column only.
    """

    # ------------------------------------------------------------------------------------------------------------------
    def _return_type_hint(self, context: WrapperContext) -> str:
        """
        Returns the return type of the wrapper method.

        :param context: The wrapper context.
        """
        return_types = context.pystratum_metadata['pydoc']['return']
        if 'Any' in return_types:
            context.code_store.add_import('typing', 'Any')

        if 'None' not in return_types:
            return_types.append('None')

        return ' | '.join(return_types)

# ----------------------------------------------------------------------------------------------------------------------
