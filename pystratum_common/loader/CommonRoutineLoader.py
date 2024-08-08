import abc
import math
import os
import re
from typing import Dict, List, Tuple

from pystratum_backend.StratumIO import StratumIO

from pystratum_common.exception.LoaderException import LoaderException
from pystratum_common.loader.helper.DataTypeHelper import DataTypeHelper
from pystratum_common.loader.helper.DocBlockReflection import DocBlockReflection


class CommonRoutineLoader(metaclass=abc.ABCMeta):
    """
    Class for loading a single stored routine into a RDBMS instance from a SQL file.
    """

    # ------------------------------------------------------------------------------------------------------------------
    def __init__(self,
                 io: StratumIO,
                 routine_filename: str,
                 routine_file_encoding: str,
                 pystratum_old_metadata: Dict,
                 replace_pairs: Dict[str, str],
                 rdbms_old_metadata: Dict):
        """
        Object constructor.

        :param io: The output decorator.
        :param routine_filename: The filename of the source of the stored routine.
        :param routine_file_encoding: The encoding of the source file.
        :param pystratum_old_metadata: The metadata of the stored routine from PyStratum.
        :param replace_pairs: A map from placeholders to their actual values.
        :param rdbms_old_metadata: The old metadata of the stored routine from the RDBMS instance.
        """
        self._source_filename: str = routine_filename
        """
        The source filename holding the stored routine.
        """

        self._routine_file_encoding: str = routine_file_encoding
        """
        The encoding of the routine file.
        """

        self._pystratum_old_metadata: Dict = pystratum_old_metadata
        """
        The old metadata of the stored routine.  Note: this data comes from the metadata file.
        """

        self._pystratum_metadata: Dict = {}
        """
        The metadata of the stored routine. Note: this data is stored in the metadata file and is generated by
        pyStratum.
        """

        self._replace_pairs: Dict[str, str] = replace_pairs
        """
        A map from placeholders to their actual values.
        """

        self._rdbms_old_metadata: Dict = rdbms_old_metadata
        """
        The old information about the stored routine. Note: this data comes from the metadata of the RDBMS instance.
        """

        self._m_time: int = 0
        """
        The last modification time of the source file.
        """

        self._routine_name: str | None = None
        """
        The name of the stored routine.
        """

        self._routine_source_code: str | None = None
        """
        The source code as a single string of the stored routine.
        """

        self._routine_source_code_lines: List[str] = []
        """
        The source code as an array of lines string of the stored routine.
        """

        self._replace: Dict = {}
        """
        The replace pairs (i.e. placeholders and their actual values).
        """

        self._routine_type: str | None = None
        """
        The stored routine type (i.e. procedure or function) of the stored routine.
        """

        self._designation_type: str | None = None
        """
        The designation type of the stored routine.
        """

        self._doc_block_parts_source: Dict = dict()
        """
        All DocBlock parts as found in the source of the stored routine.
        """

        self._doc_block_parts_wrapper: Dict = dict()
        """
        The DocBlock parts to be used by the wrapper generator.
        """

        self._columns_types: List | None = None
        """
        The column types of columns of the table for bulk insert of the stored routine.
        """

        self._fields: List | None = None
        """
        The keys in the dictionary for bulk insert.
        """

        self._parameters: List[Dict] = []
        """
        The information about the parameters of the stored routine.
        """

        self._table_name: str | None = None
        """
        If designation type is bulk_insert the table name for bulk insert.
        """

        self._columns: List | None = None
        """
        The key or index columns (depending on the designation type) of the stored routine.
        """

        self._io: StratumIO = io
        """
        The output decorator.
        """

    # ------------------------------------------------------------------------------------------------------------------
    def load_stored_routine(self) -> Dict[str, str] | False:
        """
        Loads the stored routine into the instance of MySQL.

        Returns the metadata of the stored routine if the stored routine is loaded successfully. Otherwise, returns
        False.
        """
        try:
            self._routine_name = os.path.splitext(os.path.basename(self._source_filename))[0]

            if os.path.exists(self._source_filename):
                if os.path.isfile(self._source_filename):
                    self._m_time = int(os.path.getmtime(self._source_filename))
                else:
                    raise LoaderException("Unable to get mtime of file '{}'".format(self._source_filename))
            else:
                raise LoaderException("Source file '{}' does not exist".format(self._source_filename))

            if self._pystratum_old_metadata:
                self._pystratum_metadata = self._pystratum_old_metadata

            load = self._must_reload()
            if load:
                self.__read_source_file()
                self.__get_placeholders()
                self._get_designation_type()
                self._get_name()
                self.__substitute_replace_pairs()
                self._load_routine_file()
                if self._designation_type == 'bulk_insert':
                    self._get_bulk_insert_table_columns_info()
                self._get_routine_parameters_info()
                self.__get_doc_block_parts_wrapper()
                self.__validate_parameter_lists()
                self._update_metadata()

            return self._pystratum_metadata

        except Exception as exception:
            self._log_exception(exception)
            return False

    # ------------------------------------------------------------------------------------------------------------------
    def __validate_parameter_lists(self) -> None:
        """
        Validates the parameters found the DocBlock in the source of the stored routine against the parameters from the
        metadata of MySQL and reports missing and unknown parameters names.
        """
        # Make list with names of parameters used in database.
        database_parameters_names = []
        for parameter in self._parameters:
            database_parameters_names.append(parameter['name'])

        # Make list with names of parameters used in dock block of routine.
        doc_block_parameters_names = []
        if 'parameters' in self._doc_block_parts_source:
            for parameter in self._doc_block_parts_source['parameters']:
                doc_block_parameters_names.append(parameter['name'])

        # Check and show warning if any parameters is missing in doc block.
        for parameter in database_parameters_names:
            if parameter not in doc_block_parameters_names:
                self._io.warning('Parameter {} is missing in doc block'.format(parameter))

        # Check and show warning if found unknown parameters in doc block.
        for parameter in doc_block_parameters_names:
            if parameter not in database_parameters_names:
                self._io.warning('Unknown parameter {} found in doc block'.format(parameter))

    # ------------------------------------------------------------------------------------------------------------------
    def __read_source_file(self) -> None:
        """
        Reads the file with the source of the stored routine.
        """
        with open(self._source_filename, 'r', encoding=self._routine_file_encoding) as file:
            self._routine_source_code = file.read()

        self._routine_source_code_lines = self._routine_source_code.split("\n")

    # ------------------------------------------------------------------------------------------------------------------
    def __substitute_replace_pairs(self) -> None:
        """
        Substitutes all replace pairs in the source of the stored routine.
        """
        self._set_magic_constants()

        routine_source = []
        i = 0
        for line in self._routine_source_code_lines:
            self._replace['__LINE__'] = "'%d'" % (i + 1)
            for search, replace in self._replace.items():
                tmp = re.findall(search, line, re.IGNORECASE)
                if tmp:
                    line = line.replace(tmp[0], replace)
            routine_source.append(line)
            i += 1

        self._routine_source_code = "\n".join(routine_source)

    # ------------------------------------------------------------------------------------------------------------------
    def _log_exception(self, exception: Exception) -> None:
        """
        Logs an exception.

        :param exception: The exception.
        """
        self._io.error(str(exception).strip().split(os.linesep))

    # ------------------------------------------------------------------------------------------------------------------
    @abc.abstractmethod
    def _must_reload(self) -> bool:
        """
        Returns whether the source file must be load or reloaded.
        """
        raise NotImplementedError()

    # ------------------------------------------------------------------------------------------------------------------
    def __get_placeholders(self) -> None:
        """
        Extracts the placeholders from the stored routine source.
        """
        pattern = re.compile('(@[A-Za-z0-9_.]+(%(max-)?type)?@)')
        matches = pattern.findall(self._routine_source_code)

        placeholders = []

        if len(matches) != 0:
            for tmp in matches:
                placeholder = tmp[0]
                if placeholder.lower() not in self._replace_pairs:
                    raise LoaderException("Unknown placeholder '{0}' in file {1}".
                                          format(placeholder, self._source_filename))
                if placeholder not in placeholders:
                    placeholders.append(placeholder)

        for placeholder in placeholders:
            if placeholder not in self._replace:
                self._replace[placeholder] = self._replace_pairs[placeholder.lower()]

    # ------------------------------------------------------------------------------------------------------------------
    def _get_designation_type(self) -> None:
        """
        Extracts the designation type of the stored routine.
        """
        self._get_designation_type_old()
        if not self._designation_type:
            self._get_designation_type_new()

    # ------------------------------------------------------------------------------------------------------------------
    def _get_designation_type_new(self) -> None:
        """
        Extracts the designation type of the stored routine.
        """
        line1, line2 = self.__get_doc_block_lines()

        if line1 is not None and line2 is not None and line1 <= line2:
            doc_block = self._routine_source_code_lines[line1:line2 - line1 + 1]
        else:
            doc_block = list()

        reflection = DocBlockReflection(doc_block)

        designation_type = list()
        for tag in reflection.get_tags('type'):
            designation_type.append(tag)

        if len(designation_type) == 1:
            pattern = re.compile(r'^@type\s*(\w+)\s*(.+)?\s*', re.IGNORECASE)
            matches = pattern.findall(designation_type[0])
            if matches:
                self._designation_type = matches[0][0].lower()
                tmp = str(matches[0][1])
                if self._designation_type == 'bulk_insert':
                    n = re.compile(r'([a-zA-Z0-9_]+)\s+([a-zA-Z0-9_,]+)', re.IGNORECASE)
                    info = n.findall(tmp)
                    if not info:
                        raise LoaderException('Expected: -- type: bulk_insert <table_name> <columns> in file {0}'.
                                              format(self._source_filename))
                    self._table_name = info[0][0]
                    self._columns = str(info[0][1]).split(',')

                elif self._designation_type == 'rows_with_key' or self._designation_type == 'rows_with_index':
                    self._columns = str(matches[0][1]).split(',')
                else:
                    if matches[0][1]:
                        raise LoaderException('Expected: @type {}'.format(self._designation_type))

        if not self._designation_type:
            raise LoaderException("Unable to find the designation type of the stored routine in file {0}".
                                  format(self._source_filename))

    # ------------------------------------------------------------------------------------------------------------------
    def _get_designation_type_old(self) -> None:
        """
        Extracts the designation type of the stored routine.
        """
        positions = self._get_specification_positions()
        if positions[0] != -1 and positions[1] != -1:
            pattern = re.compile(r'^\s*--\s+type\s*:\s*(\w+)\s*(.+)?\s*', re.IGNORECASE)
            for line_number in range(positions[0], positions[1] + 1):
                matches = pattern.findall(self._routine_source_code_lines[line_number])
                if matches:
                    self._designation_type = matches[0][0].lower()
                    tmp = str(matches[0][1])
                    if self._designation_type == 'bulk_insert':
                        n = re.compile(r'([a-zA-Z0-9_]+)\s+([a-zA-Z0-9_,]+)', re.IGNORECASE)
                        info = n.findall(tmp)
                        if not info:
                            raise LoaderException('Expected: -- type: bulk_insert <table_name> <columns> in file {0}'.
                                                  format(self._source_filename))
                        self._table_name = info[0][0]
                        self._columns = str(info[0][1]).split(',')

                    elif self._designation_type == 'rows_with_key' or self._designation_type == 'rows_with_index':
                        self._columns = str(matches[0][1]).split(',')
                    else:
                        if matches[0][1]:
                            raise LoaderException('Expected: -- type: {}'.format(self._designation_type))

    # ------------------------------------------------------------------------------------------------------------------
    def _get_specification_positions(self) -> Tuple[int, int]:
        """
        Returns a tuple with the start and end line numbers of the stored routine specification.
        """
        start = -1
        for (i, line) in enumerate(self._routine_source_code_lines):
            if self._is_start_of_stored_routine(line):
                start = i

        end = -1
        for (i, line) in enumerate(self._routine_source_code_lines):
            if self._is_start_of_stored_routine_body(line):
                end = i - 1

        return start, end

    # ------------------------------------------------------------------------------------------------------------------
    @abc.abstractmethod
    def _is_start_of_stored_routine(self, line: str) -> bool:
        """
        Returns whether a line is the start of the code of the stored routine.

        :param line: The line with source code of the stored routine.
        """
        raise NotImplementedError()

    # ------------------------------------------------------------------------------------------------------------------
    def _is_start_of_stored_routine_body(self, line: str) -> bool:
        """
        Returns whether a line is the start of the body of the stored routine.

        :param line: The line with source code of the stored routine.
        """
        raise NotImplementedError()

    # ------------------------------------------------------------------------------------------------------------------
    def __get_doc_block_lines(self) -> Tuple[int, int]:
        """
        Returns the start and end line of the DocBlock of the stored routine code.
        """
        line1 = None
        line2 = None

        i = 0
        for line in self._routine_source_code_lines:
            if re.match(r'\s*/\*\*', line):
                line1 = i

            if re.match(r'\s*\*/', line):
                line2 = i

            if self._is_start_of_stored_routine(line):
                break

            i += 1

        return line1, line2

    # ------------------------------------------------------------------------------------------------------------------
    def __get_doc_block_parts_source(self) -> None:
        """
        Extracts the DocBlock (in parts) from the source of the stored routine source.
        """
        line1, line2 = self.__get_doc_block_lines()

        if line1 is not None and line2 is not None and line1 <= line2:
            doc_block = self._routine_source_code_lines[line1:line2 - line1 + 1]
        else:
            doc_block = list()

        reflection = DocBlockReflection(doc_block)

        self._doc_block_parts_source['description'] = reflection.get_description()

        self._doc_block_parts_source['parameters'] = list()
        for tag in reflection.get_tags('param'):
            parts = re.match(r'^(@param)\s+(\w+)\s*(.+)?', tag, re.DOTALL)
            if parts:
                self._doc_block_parts_source['parameters'].append({'name':        parts.group(2),
                                                                   'description': parts.group(3)})

    # ------------------------------------------------------------------------------------------------------------------
    def __get_parameter_doc_description(self, name: str) -> str:
        """
        Returns the description by name of the parameter as found in the DocBlock of the stored routine.

        :param name: The name of the parameter.
        """
        for param in self._doc_block_parts_source['parameters']:
            if param['name'] == name:
                return param['description']

        return ''

    # ------------------------------------------------------------------------------------------------------------------
    @abc.abstractmethod
    def _get_data_type_helper(self) -> DataTypeHelper:
        """
        Returns a data type helper object appropriate for the RDBMS.
        """
        raise NotImplementedError()

    # ------------------------------------------------------------------------------------------------------------------
    def __get_doc_block_parts_wrapper(self) -> None:
        """
        Generates the DocBlock parts to be used by the wrapper generator.
        """
        self.__get_doc_block_parts_source()

        helper = self._get_data_type_helper()

        parameters = list()
        for parameter_info in self._parameters:
            parameters.append(
                    {'parameter_name':       parameter_info['name'],
                     'python_type':          helper.column_type_to_python_type(parameter_info),
                     'python_type_hint':     helper.column_type_to_python_type_hint(parameter_info),
                     'data_type_descriptor': parameter_info['data_type_descriptor'],
                     'description':          self.__get_parameter_doc_description(parameter_info['name'])})

        self._doc_block_parts_wrapper['description'] = self._doc_block_parts_source['description']
        self._doc_block_parts_wrapper['parameters'] = parameters

    # ------------------------------------------------------------------------------------------------------------------
    @abc.abstractmethod
    def _get_name(self) -> None:
        """
        Extracts the name of the stored routine and the stored routine type (i.e. procedure or function) source.
        """
        raise NotImplementedError()

    # ------------------------------------------------------------------------------------------------------------------
    @abc.abstractmethod
    def _load_routine_file(self) -> None:
        """
        Loads the stored routine into the RDBMS instance.
        """
        raise NotImplementedError()

    # ------------------------------------------------------------------------------------------------------------------
    @abc.abstractmethod
    def _get_bulk_insert_table_columns_info(self) -> None:
        """
        Gets the column names and column types of the current table for bulk insert.
        """
        raise NotImplementedError()

    # ------------------------------------------------------------------------------------------------------------------
    @abc.abstractmethod
    def _get_routine_parameters_info(self) -> None:
        """
        Retrieves information about the stored routine parameters from the metadata of the RDBMS.
        """
        raise NotImplementedError()

    # ------------------------------------------------------------------------------------------------------------------
    def _update_metadata(self) -> None:
        """
        Updates the metadata of the stored routine.
        """
        self._pystratum_metadata['routine_name'] = self._routine_name
        self._pystratum_metadata['designation'] = self._designation_type
        self._pystratum_metadata['table_name'] = self._table_name
        self._pystratum_metadata['parameters'] = self._parameters
        self._pystratum_metadata['columns'] = self._columns
        self._pystratum_metadata['fields'] = self._fields
        self._pystratum_metadata['column_types'] = self._columns_types
        self._pystratum_metadata['timestamp'] = self._m_time
        self._pystratum_metadata['replace'] = self._replace
        self._pystratum_metadata['pydoc'] = self._doc_block_parts_wrapper

    # ------------------------------------------------------------------------------------------------------------------
    @abc.abstractmethod
    def _drop_routine(self) -> None:
        """
        Drops the stored routine if it exists.
        """
        raise NotImplementedError()

    # ------------------------------------------------------------------------------------------------------------------
    def _set_magic_constants(self) -> None:
        """
        Adds magic constants to replace list.
        """
        real_path = os.path.realpath(self._source_filename)

        self._replace['__FILE__'] = "'%s'" % real_path
        self._replace['__ROUTINE__'] = "'%s'" % self._routine_name
        self._replace['__DIR__'] = "'%s'" % os.path.dirname(real_path)

    # ------------------------------------------------------------------------------------------------------------------
    def _unset_magic_constants(self) -> None:
        """
        Removes magic constants from current replace list.
        """
        if '__FILE__' in self._replace:
            del self._replace['__FILE__']

        if '__ROUTINE__' in self._replace:
            del self._replace['__ROUTINE__']

        if '__DIR__' in self._replace:
            del self._replace['__DIR__']

        if '__LINE__' in self._replace:
            del self._replace['__LINE__']

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
