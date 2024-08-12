import re
from abc import ABC

from pystratum_common.wrapper.CommonWrapper import CommonWrapper
from pystratum_common.wrapper.helper.WrapperContext import WrapperContext


class CommonInsertManyWrapper(CommonWrapper, ABC):
    """
    Wrapper method generator for stored procedures with designation type insert_many.
    """

    # ------------------------------------------------------------------------------------------------------------------
    def _return_type_hint(self, context: WrapperContext) -> str:
        """
        Returns the return type hint of the wrapper method.

        :param context: The wrapper context.
        """
        return 'int'

    # ------------------------------------------------------------------------------------------------------------------
    @staticmethod
    def _wrapper_args(context: WrapperContext) -> str:
        """
        Returns code for the parameters of the wrapper method for the stored routine.

        :param context: The wrapper context.
        """
        context.code_store.add_import('typing', 'Any')
        context.code_store.add_import('typing', 'Dict')
        context.code_store.add_import('typing', 'List')
        parameters = CommonWrapper._wrapper_args(context)

        return re.sub(r'^self', 'self, rows: List[Dict[str, Any]]', parameters)

    # ------------------------------------------------------------------------------------------------------------------
    def _build_docstring_parameters(self, context: WrapperContext) -> None:
        """
        Builds the parameter's part of the docstring for the wrapper method of a stored routine.

        :param context: The wrapper context.
        """
        parameter = {'name':                 'rows',
                     'python_type':          'List[Dict[str, Any]]',
                     'description':          'The rows that must be inserted.',
                     'data_type_descriptor': None}
        context.pystratum_metadata['pydoc']['parameters'].insert(0, parameter)

        CommonWrapper._build_docstring_parameters(self, context)

# ----------------------------------------------------------------------------------------------------------------------
