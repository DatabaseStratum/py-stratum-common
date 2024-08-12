import abc
import math
import os
from typing import Any, Dict

from pystratum_backend.StratumIO import StratumIO

from pystratum_common.loader.helper.CommonDataTypeHelper import CommonDataTypeHelper
from pystratum_common.loader.helper.LoaderContext import LoaderContext


class CommonRoutineLoader(metaclass=abc.ABCMeta):
    """
    Class for loading a single stored routine into a RDBMS instance from a SQL file.
    """

    # ------------------------------------------------------------------------------------------------------------------
    def __init__(self, io: StratumIO, ):
        """
        Object constructor.

        :param io: The output decorator.
        """

        self._io: StratumIO = io
        """
        The output decorator.
        """

    # ------------------------------------------------------------------------------------------------------------------
    def load_stored_routine(self, context: LoaderContext) -> bool | None:
        """
        Loads the stored routine into the RDBMS instance.

        Returns whether the stored routine is successfully loaded.

        :param context: The loader context.
        """
        try:
            if self._must_reload(context):
                self._update_source_type_hints(context, self._io)
                self._extract_name(context)
                self._substitute_placeholders(context)
                self._load_routine_file(context)
                self._extract_insert_many_table_columns(context)
                self._extract_stored_routine_parameters(context)
                self._validate_parameter_lists(context)
                self._update_metadata(context)

                return True

            return None

        except Exception as exception:
            self._log_exception(exception)
            if self._io.is_verbose():
                raise exception
            return False

    # ------------------------------------------------------------------------------------------------------------------
    def _must_reload(self, context: LoaderContext) -> bool:
        """
        Returns whether the source file must be loaded or reloaded.

        :param context: The loader context.
        """
        if not context.old_pystratum_metadata:
            return True

        if context.old_pystratum_metadata['timestamp'] != context.stored_routine.m_time:
            return True

        if context.old_pystratum_metadata['type_hints']:
            if not context.type_hints.compare_type_hints(context.old_pystratum_metadata['type_hints']):
                return True

        if context.old_pystratum_metadata['placeholders']:
            if not context.placeholders.compare_placeholders(context.old_pystratum_metadata['placeholders']):
                return True

        if not context.old_rdbms_metadata:
            return True

    # ------------------------------------------------------------------------------------------------------------------
    @abc.abstractmethod
    def _get_data_type_helper(self) -> CommonDataTypeHelper:
        """
        Returns a data type helper object appropriate for the RDBMS.
        """
        raise NotImplementedError()

    # ------------------------------------------------------------------------------------------------------------------
    @abc.abstractmethod
    def _extract_name(self, context: LoaderContext) -> None:
        """
        Extracts the name of the stored routine and the stored routine type (i.e. procedure or function) source.

        :param context: The loader context.
        """
        raise NotImplementedError()

    # ------------------------------------------------------------------------------------------------------------------
    @abc.abstractmethod
    def _load_routine_file(self, context: LoaderContext) -> None:
        """
        Loads the stored routine into the RDBMS instance.

        :param context: The loader context.
        """
        raise NotImplementedError()

    # ------------------------------------------------------------------------------------------------------------------
    @abc.abstractmethod
    def _extract_insert_many_table_columns(self, context: LoaderContext) -> None:
        """
        Gets the column names and column types of the current table for insert many.

        :param context: The loader context.
        """
        raise NotImplementedError()

    # ------------------------------------------------------------------------------------------------------------------
    @abc.abstractmethod
    def _extract_stored_routine_parameters(self, context: LoaderContext) -> None:
        """
        Extracts the metadata of the stored routine parameters from the RDBMS.

        :param context: The loader context.
        """
        raise NotImplementedError()

    # ------------------------------------------------------------------------------------------------------------------
    @abc.abstractmethod
    def _drop_stored_routine(self, context: LoaderContext) -> None:
        """
        Drops the stored routine if it exists.

        :param context: The loader context.
        """
        raise NotImplementedError()

    # ------------------------------------------------------------------------------------------------------------------
    def _update_source_type_hints(self, context: LoaderContext, io: StratumIO) -> None:
        """
        Updates the source of the stored routine based on the values of type hints.

        :param context: The loader context.
        :param io: The output decorator.
        """
        lines = context.type_hints.update_types(context.stored_routine.code_lines, self._get_data_type_helper())
        lines = context.type_hints.align_type_hints(lines)
        context.stored_routine.update_source('\n'.join(lines), io)

    # ------------------------------------------------------------------------------------------------------------------
    def _validate_parameter_lists(self, context: LoaderContext) -> None:
        """
        Validates the parameters found the DocBlock in the source of the stored routine against the parameters from the
        metadata of MySQL and reports missing and unknown parameters names.

        :param context: The loader context.
        """
        # Make a list with names of parameters used in the database.
        database_parameters_names = []
        for parameter in context.stored_routine.parameters:
            database_parameters_names.append(parameter['name'])

        # Make a list with names of parameters used in dock block of routine.
        doc_block_parameters_names = []
        for parameter in context.doc_block.parameters():
            doc_block_parameters_names.append(parameter['name'])

        # Check and show warning if any parameter is missing in doc block.
        for parameter in database_parameters_names:
            if parameter not in doc_block_parameters_names:
                self._io.warning('Parameter {} is missing in doc block'.format(parameter))

        # Check and show warning if found unknown parameters in doc block.
        for parameter in doc_block_parameters_names:
            if parameter not in database_parameters_names:
                self._io.warning('Unknown parameter {} found in doc block'.format(parameter))

    # ------------------------------------------------------------------------------------------------------------------
    def _substitute_placeholders(self, context: LoaderContext) -> None:
        """
        Substitutes all placeholders with their actual values in the source of the routine.
        """
        self._set_magic_constants(context)
        self._routine_source_code = context.placeholders.substitute_placeholders(context.stored_routine.code_lines)

    # ------------------------------------------------------------------------------------------------------------------
    def _log_exception(self, exception: Exception) -> None:
        """
        Logs an exception.

        :param exception: The exception.
        """
        self._io.error(str(exception).strip().split(os.linesep))

    # ------------------------------------------------------------------------------------------------------------------
    def _get_pydoc(self, context: LoaderContext) -> Dict[str, Any]:
        """
        Returns the DocBlock parts to be used by the wrapper generator.

        :param context: The loader context.
        """
        helper = self._get_data_type_helper()

        pydoc = {'description': context.doc_block.description()}

        parameters = []
        for parameter_info in context.stored_routine.parameters:
            parameters.append(
                    {'name':                 parameter_info['name'],
                     'python_type':          helper.column_type_to_python_type(parameter_info),
                     'data_type_descriptor': parameter_info['data_type_descriptor'],
                     'description':          context.doc_block.parameter_description(parameter_info['name'])})

        pydoc['parameters'] = parameters

        if 'return' in context.doc_block.designation:
            return_types = context.doc_block.designation['return']
            if '*' in return_types:
                pydoc['return'] = ['Any']
            elif len(return_types) == 1 and return_types[0] == 'bool':
                pydoc['return'] = ['bool']
            else:
                pydoc['return'] = []
                nullable = False
                for return_type in return_types:
                    if return_type == 'null':
                        nullable = True
                    else:
                        pydoc['return'].append(helper.column_type_to_python_type({'data_type': return_type}))
                sorted(set(pydoc['return']))
                if nullable:
                    pydoc['return'].append('None')

        return pydoc

    # ------------------------------------------------------------------------------------------------------------------
    def _update_metadata(self, context: LoaderContext) -> None:
        """
        Updates the metadata of the stored routine.

        :param context: The loader context.
        """
        placeholders = context.placeholders.get_placeholders(context.stored_routine.path, context.stored_routine.code)
        type_hints = context.type_hints.get_type_hints(context.stored_routine.path, context.stored_routine.code)

        context.new_pystratum_metadata['routine_name'] = context.stored_routine.name
        context.new_pystratum_metadata['designation'] = context.doc_block.designation
        context.new_pystratum_metadata['parameters'] = context.stored_routine.parameters
        context.new_pystratum_metadata['timestamp'] = context.stored_routine.m_time
        context.new_pystratum_metadata['type_hints'] = type_hints
        context.new_pystratum_metadata['placeholders'] = placeholders
        context.new_pystratum_metadata['pydoc'] = self._get_pydoc(context)

    # ------------------------------------------------------------------------------------------------------------------
    def _set_magic_constants(self, context: LoaderContext) -> None:
        """
        Adds magic constants to placeholders.

        :param context: The loader context.
        """
        real_path = os.path.realpath(context.stored_routine.path)
        routine_name = os.path.splitext(os.path.basename(context.stored_routine.path))[0]

        context.placeholders.add_placeholder('__FILE__', f"'{real_path}'")
        context.placeholders.add_placeholder('__ROUTINE__', f"'{routine_name}'")
        context.placeholders.add_placeholder('__DIR__', f"'{os.path.dirname(real_path)}'")

    # ------------------------------------------------------------------------------------------------------------------
    def _print_sql_with_error(self, sql: str, error_line: int) -> None:
        """
        Writes a SQL statement with a syntax error to the output. The line where the error occurs is highlighted.

        :param sql: The SQL statement.
        :param error_line: The line where the error occurs.
        """
        if os.linesep in sql:
            lines = sql.split(os.linesep)
            digits = math.ceil(math.log(len(lines) + 1, 10))
            i = 1
            for line in lines:
                if i == error_line:
                    self._io.text('<error>{0:{width}} {1}</error>'.format(i, line, width=digits, ))
                else:
                    self._io.text('{0:{width}} {1}'.format(i, line, width=digits, ))
                i += 1
        else:
            self._io.text(sql)

# ----------------------------------------------------------------------------------------------------------------------
