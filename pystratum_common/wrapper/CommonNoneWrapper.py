from abc import ABC

from pystratum_common.wrapper.CommonWrapper import CommonWrapper
from pystratum_common.wrapper.helper.WrapperContext import WrapperContext


class CommonNoneWrapper(CommonWrapper, ABC):
    """
    Wrapper method generator for stored procedures without any result set.
    """

    # ------------------------------------------------------------------------------------------------------------------
    def _return_type_hint(self, context: WrapperContext) -> str:
        """
        Returns the return type of the wrapper method.

        :param context: The wrapper context.
        """
        return 'int'

# ----------------------------------------------------------------------------------------------------------------------
