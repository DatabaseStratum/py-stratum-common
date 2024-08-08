import abc
import configparser
import json
import os
from typing import Dict

from pystratum_backend.RoutineWrapperGeneratorWorker import RoutineWrapperGeneratorWorker
from pystratum_backend.StratumIO import StratumIO

from pystratum_common.BuildContext import BuildContext
from pystratum_common.PythonCodeStore import PythonCodeStore
from pystratum_common.Util import Util


class CommonRoutineWrapperGeneratorWorker(RoutineWrapperGeneratorWorker):
    """
    Class for generating a class with wrapper methods for calling stored routines in a MySQL database.
    """

    # ------------------------------------------------------------------------------------------------------------------
    def __init__(self, io: StratumIO, config: configparser.ConfigParser):
        """
        Object constructor.

        :param io: The output decorator.
        """
        self._code_store: PythonCodeStore = PythonCodeStore()
        """
        The generated Python code buffer.
        """

        self._metadata_filename: str | None = None
        """
        The filename of the file with the metadata of all stored procedures.
        """

        self._parent_class_name: str | None = None
        """
        The class name of the parent class of the routine wrapper.
        """

        self._parent_class_namespace: str | None = None
        """
        The namespace of the parent class of the routine wrapper.
        """

        self._wrapper_class_name: str | None = None
        """
        The class name of the routine wrapper.
        """

        self._wrapper_filename: str | None = None
        """
        The filename where the generated wrapper class must be stored.
        """

        self._io: StratumIO = io
        """
        The output decorator.
        """

        self._config = config
        """
        The configuration object.
        """

    # ------------------------------------------------------------------------------------------------------------------
    def execute(self) -> int:
        """
        The "main" of the wrapper generator. Returns 0 on success, 1 if one or more errors occurred.
        """
        self._read_configuration_file()

        if self._wrapper_class_name:
            self._io.title('Wrapper')

            self.__generate_wrapper_class()

            self._io.write_line('')
        else:
            self._io.log_verbose('Wrapper not enabled')

        return 0

    # ------------------------------------------------------------------------------------------------------------------
    def __generate_wrapper_class(self) -> None:
        """
        Generates the wrapper class.
        """
        routines = self._read_routine_metadata()

        self._generate_class_header()

        if routines:
            for routine_name in sorted(routines):
                if routines[routine_name]['designation'] != 'hidden':
                    context = BuildContext(self._code_store, routines[routine_name])
                    self._build_routine_wrapper(context)
        else:
            self._io.error('No files with stored routines found')

        self._generate_class_trailer()

        Util.write_two_phases(self._wrapper_filename, self._code_store.get_code(), self._io)

    # ------------------------------------------------------------------------------------------------------------------
    def _read_configuration_file(self) -> None:
        """
        Reads parameters from the configuration file.
        """
        self._parent_class_name = self._config.get('wrapper', 'parent_class')
        self._parent_class_namespace = self._config.get('wrapper', 'parent_class_namespace')
        self._wrapper_class_name = self._config.get('wrapper', 'wrapper_class')
        self._wrapper_filename = self._config.get('wrapper', 'wrapper_file')
        self._metadata_filename = self._config.get('wrapper', 'metadata')

    # ------------------------------------------------------------------------------------------------------------------
    def _read_routine_metadata(self) -> Dict:
        """
        Returns the metadata of stored routines.
        """
        metadata = {}
        if os.path.isfile(self._metadata_filename):
            with open(self._metadata_filename, 'r') as file:
                metadata = json.load(file)

        return metadata

    # ------------------------------------------------------------------------------------------------------------------
    def _generate_class_header(self) -> None:
        """
        Generate a class header for stored routine wrapper.
        """
        self._code_store.add_import(self._parent_class_namespace, self._parent_class_name)

        self._code_store.append_line('class {0!s}({1!s}):'.format(self._wrapper_class_name, self._parent_class_name))
        self._code_store.append_line('"""')
        self._code_store.append_line('The stored routines wrappers.')
        self._code_store.append_line('"""')

    # ------------------------------------------------------------------------------------------------------------------
    def _generate_class_trailer(self) -> None:
        """
        Generate a class trailer for stored routine wrapper.
        """
        self._code_store.decrement_indent_level()
        self._code_store.append_line()
        self._code_store.append_separator()
        self._code_store.append_line()

    # ------------------------------------------------------------------------------------------------------------------
    @abc.abstractmethod
    def _build_routine_wrapper(self, context: BuildContext) -> None:
        """
        Builds a complete wrapper method for a stored routine.

        :param context: The build context.
        """
        raise NotImplementedError()

# ----------------------------------------------------------------------------------------------------------------------
