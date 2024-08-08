import abc
import os

from pystratum_common.BuildContext import BuildContext


class Wrapper(metaclass=abc.ABCMeta):
    """
    Parent class for classes that generate Python code, i.e. wrappers, for calling a stored procedures and functions.
    """

    # ------------------------------------------------------------------------------------------------------------------
    def _build_docstring_description(self, context: BuildContext) -> None:
        """
        Builds the description part of the docstring for the wrapper method of a stored routine.

        :param context: The build context.
        """
        if context.routine['pydoc']['description']:
            context.code_store.append_line(context.routine['pydoc']['description'])

    # ------------------------------------------------------------------------------------------------------------------
    def _build_docstring_parameters(self, context: BuildContext) -> None:
        """
        Builds the parameters part of the docstring for the wrapper method of a stored routine.

        :param context: The build context.
        """
        if context.routine['pydoc']['parameters']:
            context.code_store.append_line('')

            for param in context.routine['pydoc']['parameters']:
                lines = param['description'].split(os.linesep)
                context.code_store.append_line(':param {0} {1}: {2}'.format(param['python_type'],
                                                                            param['parameter_name'],
                                                                            lines[0]))
                del lines[0]

                tmp = ':param {0} {1}:'.format(param['python_type'], param['parameter_name'])
                indent = ' ' * len(tmp)
                for line in lines:
                    context.code_store.append_line('{0} {1}'.format(indent, line))

                context.code_store.append_line('{0} {1}'.format(indent, param['data_type_descriptor']))

    # ------------------------------------------------------------------------------------------------------------------
    def _build_docstring_return_type(self, context: BuildContext) -> None:
        """
        Build the return type part of the docstring for the wrapper method of a stored routine.

        :param context: The build context.
        """
        rtype = self._return_type_hint(context)
        if rtype:
            context.code_store.append_line('')
            context.code_store.append_line(':rtype: {0}'.format(rtype))

    # ------------------------------------------------------------------------------------------------------------------
    def _build_docstring(self, context: BuildContext) -> None:
        """
        Builds the docstring for the wrapper method of the stored routine.

        :param context: The build context.
        """
        context.code_store.append_line('"""')

        self._build_docstring_description(context)
        self._build_docstring_parameters(context)
        self._build_docstring_return_type(context)

        context.code_store.append_line('"""')

    # ------------------------------------------------------------------------------------------------------------------
    @abc.abstractmethod
    def _return_type_hint(self, context: BuildContext) -> str:
        """
        Returns the return type of the wrapper method.

        :param context: The build context.
        """
        raise NotImplementedError()

    # ------------------------------------------------------------------------------------------------------------------
    @abc.abstractmethod
    def _build_result_handler(self, context: BuildContext) -> None:
        """
        Builds the code for calling the stored routine in the wrapper method.

        :param context: The build context.
        """
        raise NotImplementedError()

    # ------------------------------------------------------------------------------------------------------------------
    @staticmethod
    def _wrapper_args(context: BuildContext) -> str:
        """
        Returns code for the parameters of the wrapper method for the stored routine.

        :param context: The build context.
        """
        ret = 'self'

        for parameter_info in context.routine['pydoc']['parameters']:
            if ret:
                ret += ', '

            ret += parameter_info['parameter_name']

            if parameter_info['python_type_hint']:
                ret += ': ' + parameter_info['python_type_hint']

        return ret

    # ------------------------------------------------------------------------------------------------------------------
    def build(self, context: BuildContext) -> None:
        """
        Builds the wrapper method.

        :param context: The build context.
        """
        context.code_store.append_line()
        context.code_store.append_separator()
        context.code_store.append_line('def {0!s}({1!s}) -> {2!s}:'.format(str(context.routine['routine_name']),
                                                                           str(self._wrapper_args(context)),
                                                                           str(self._return_type_hint(context))))
        self._build_docstring(context)
        self._build_result_handler(context)
        context.code_store.decrement_indent_level()

# ----------------------------------------------------------------------------------------------------------------------
