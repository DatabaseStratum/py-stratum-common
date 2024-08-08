import re
from abc import ABC

from pystratum_common.wrapper.CommonWrapper import CommonWrapper
from pystratum_common.wrapper.helper.WrapperContext import BuildContext


class CommonBulkWrapper(CommonWrapper, ABC):
    """
    Wrapper method generator for stored procedures with designation type bulk.
    """

    # ------------------------------------------------------------------------------------------------------------------
    def _return_type_hint(self, context: BuildContext) -> str:
        """
        Returns the return type hint of the wrapper method.

        :param context: The build context.
        """
        return 'int'

    # ------------------------------------------------------------------------------------------------------------------
    @staticmethod
    def _wrapper_args(context: BuildContext) -> str:
        """
        Returns code for the parameters of the wrapper method for the stored routine.

        :param context: The build context.
        """
        context.code_store.add_import('pystratum_middle.BulkHandler', 'BulkHandler')
        parameters = CommonWrapper._wrapper_args(context)

        return re.sub(r'^self', 'self, bulk_handler: BulkHandler', parameters)

    # ------------------------------------------------------------------------------------------------------------------
    def _build_docstring_parameters(self, context: BuildContext) -> None:
        """
        Builds the parameters part of the docstring for the wrapper method of a stored routine.

        :param context: The build context.
        """
        context.code_store.append_line('')
        context.code_store.append_line(':param BulkHandler bulk_handler: '
                                       'The bulk handler for processing the selected rows.')

        CommonWrapper._build_docstring_parameters(self, context)

# ----------------------------------------------------------------------------------------------------------------------
