import abc
import os
from abc import ABC

from pystratum_common.wrapper.helper.WrapperContext import WrapperContext


class CommonWrapper(ABC):
    """
    Parent class for classes that generate Python code, i.e. wrappers, for invoking stored routines.
    """

    # ------------------------------------------------------------------------------------------------------------------
    @staticmethod
    def _build_docstring_description(context: WrapperContext) -> None:
        """
        Builds the description part of the docstring for the wrapper method of a stored routine.

        :param context: The wrapper context.
        """
        if context.pystratum_metadata['pydoc']['description']:
            context.code_store.append_line(context.pystratum_metadata['pydoc']['description'])

    # ------------------------------------------------------------------------------------------------------------------
    def _build_docstring_parameters(self, context: WrapperContext) -> None:
        """
        Builds the parameter's part of the docstring for the wrapper method of a stored routine.

        :param context: The wrapper context.
        """
        if context.pystratum_metadata['pydoc']['parameters']:
            context.code_store.append_line('')

            for param in context.pystratum_metadata['pydoc']['parameters']:
                lines = param['description'].split(os.linesep)
                context.code_store.append_line(
                        ':param {0}: {1}'.format(param['name'], lines[0]))
                del lines[0]

                tmp = ':param {0}:'.format(param['name'])
                indent = ' ' * len(tmp)
                for line in lines:
                    context.code_store.append_line('{0} {1}'.format(indent, line))

                if param['data_type_descriptor']:
                    context.code_store.append_line(
                        '{0} RDBMS data type: {1}'.format(indent, param['data_type_descriptor']))

    # ------------------------------------------------------------------------------------------------------------------
    def _build_docstring(self, context: WrapperContext) -> None:
        """
        Builds the docstring for the wrapper method of the stored routine.

        :param context: The wrapper context.
        """
        context.code_store.append_line('"""')

        self._build_docstring_description(context)
        self._build_docstring_parameters(context)

        context.code_store.append_line('"""')

    # ------------------------------------------------------------------------------------------------------------------
    @abc.abstractmethod
    def _return_type_hint(self, context: WrapperContext) -> str:
        """
        Returns the return type of the wrapper method.

        :param context: The wrapper context.
        """
        raise NotImplementedError()

    # ------------------------------------------------------------------------------------------------------------------
    @abc.abstractmethod
    def _build_result_handler(self, context: WrapperContext) -> None:
        """
        Builds the code for calling the stored routine in the wrapper method.

        :param context: The wrapper context.
        """
        raise NotImplementedError()

    # ------------------------------------------------------------------------------------------------------------------
    @staticmethod
    def _wrapper_args(context: WrapperContext) -> str:
        """
        Returns code for the parameters of the wrapper method for the stored routine.

        :param context: The wrapper context.
        """
        ret = 'self'

        for parameter_info in context.pystratum_metadata['pydoc']['parameters']:
            if ret:
                ret += ', '

            ret += parameter_info['name']

            if parameter_info['python_type']:
                ret += ': ' + parameter_info['python_type'] + ' | None'

        return ret

    # ------------------------------------------------------------------------------------------------------------------
    def build(self, context: WrapperContext) -> None:
        """
        Builds the wrapper method.

        :param context: The wrapper context.
        """
        context.code_store.append_line()
        context.code_store.append_separator()
        context.code_store.append_line(
                'def {0!s}({1!s}) -> {2!s}:'.format(str(context.pystratum_metadata['routine_name']),
                                                    str(self._wrapper_args(context)),
                                                    str(self._return_type_hint(context))))
        self._build_docstring(context)
        self._build_result_handler(context)
        context.code_store.decrement_indent_level()

# ----------------------------------------------------------------------------------------------------------------------
