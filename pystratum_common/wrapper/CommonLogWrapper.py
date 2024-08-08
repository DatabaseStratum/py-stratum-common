from abc import ABC

from pystratum_common.wrapper.CommonWrapper import CommonWrapper
from pystratum_common.wrapper.helper.WrapperContext import BuildContext


class CommonLogWrapper(CommonWrapper, ABC):
    """
    Wrapper method generator for stored procedures with designation type log.
    """

    # ------------------------------------------------------------------------------------------------------------------
    def _return_type_hint(self, context: BuildContext) -> str:
        """
        Returns the return type of the wrapper method.

        :param context: The build context.
        """
        return 'int'

# ----------------------------------------------------------------------------------------------------------------------
