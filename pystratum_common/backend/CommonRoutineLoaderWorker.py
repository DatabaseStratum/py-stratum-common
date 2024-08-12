import abc
import configparser
import json
import os
from typing import Any, Dict, List

from pystratum_backend.RoutineLoaderWorker import RoutineLoaderWorker
from pystratum_backend.StratumIO import StratumIO

from pystratum_common.constant.ConstantClass import ConstantClass
from pystratum_common.loader.CommonRoutineLoader import CommonRoutineLoader
from pystratum_common.loader.helper.DocBlockHelper import DocBlockHelper
from pystratum_common.loader.helper.LoaderContext import LoaderContext
from pystratum_common.loader.helper.PlaceholderHelper import PlaceholderHelper
from pystratum_common.loader.helper.StoredRoutineHelper import StoredRoutineHelper
from pystratum_common.loader.helper.TypeHintHelper import TypeHintHelper


class CommonRoutineLoaderWorker(RoutineLoaderWorker):
    """
    Class for loading stored routines into a RDBMS instance from (pseudo) SQL files.
    """

    # ------------------------------------------------------------------------------------------------------------------
    def __init__(self, io: StratumIO, config: configparser.ConfigParser):
        """
        Object constructor.

        :param io: The output decorator.
        """
        self.__error_file_names = set()
        """
        A set with source names that are not loaded into RDBMS instance.
        """

        self.__pystratum_metadata: Dict = {}
        """
        The metadata of all stored routines.
        """

        self.__pystratum_metadata_path: str | None = None
        """
        The filename of the file with the metadata of all stored routines.
        """

        self.__rdbms_metadata: Dict = {}
        """
        The metadata about all stored routines currently in the RDBMS instance.
        """

        self.__type_hints: TypeHintHelper = TypeHintHelper()
        """
        A map from type hints to their actual data types.
        """

        self.__placeholders: PlaceholderHelper = PlaceholderHelper()
        """
        A map from placeholders to their actual values.
        """

        self.__source_file_encoding: str | None = None
        """
        The character set of the source files.
        """

        self.__source_directory: str | None = None
        """
        Path where source files can be found.
        """

        self.__source_file_extension: str | None = None
        """
        The extension of the source files.
        """

        self.__source_file_names: Dict = {}
        """
        All found source files.
        """

        self.__constants_class_name: str | None = None
        """
        The name of the class that acts like a namespace for constants.
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
    def execute(self, file_names: List[str] | None = None) -> int:
        """
        Loads stored routines into the current schema.

        :param file_names: The sources that must be loaded. If empty, all sources (if required) will be loaded.
        """
        self._io.title('Loader')

        self._read_configuration_file()

        if file_names:
            self._load_list(file_names)
        else:
            self._load_all()

        if self.__error_file_names:
            self._log_overview_errors()

        self._io.write_line('')

        return 1 if self.__error_file_names else 0

    # ------------------------------------------------------------------------------------------------------------------
    @abc.abstractmethod
    def _connect(self) -> None:
        """
        Connects to the RDBMS instance.
        """
        raise NotImplementedError()

    # ------------------------------------------------------------------------------------------------------------------
    @abc.abstractmethod
    def _create_routine_loader(self, context: LoaderContext) -> CommonRoutineLoader:
        """
        Creates a Routine Loader object.

        :param context: The loader context.
        """
        raise NotImplementedError()

    # ------------------------------------------------------------------------------------------------------------------
    @abc.abstractmethod
    def _disconnect(self) -> None:
        """
        Disconnects from the RDBMS instance.
        """
        raise NotImplementedError()

    # ------------------------------------------------------------------------------------------------------------------
    @abc.abstractmethod
    def _drop_stored_routine(self, rdbms_metadata: Dict[str, Any]) -> None:
        """
        Drops a stored routine.

        :param rdbms_metadata: The metadata from the RDBMS of the stored routine to be dropped.
        """
        raise NotImplementedError()

    # ------------------------------------------------------------------------------------------------------------------
    @abc.abstractmethod
    def _fetch_rdbms_metadata(self) -> List[Dict[str, Any]]:
        """
        Retrieves metadata about all stored routines currently in the current schema of the RDBMS.
        """
        raise NotImplementedError()

    # ------------------------------------------------------------------------------------------------------------------
    @abc.abstractmethod
    def _fetch_column_types(self) -> None:
        """
        Selects schema, table, column names and the column type from the RDBMS instance and saves them as placeholders.
        """
        raise NotImplementedError()

    # ------------------------------------------------------------------------------------------------------------------
    def _drop_obsolete_routines(self) -> None:
        """
        Drops obsolete stored routines (i.e., stored routines that exit in the current schema but for
        which we don't have a source file).
        """
        for routine_name, rdbms_metadata in self.__rdbms_metadata.items():
            if routine_name not in self.__source_file_names:
                self._io.text("Dropping {0} <dbo>{1}</dbo>".format(rdbms_metadata['routine_type'].lower(),
                                                                   routine_name))
                self.__pystratum_metadata.pop('routine_name', None)
                self._drop_stored_routine(rdbms_metadata)

    # ------------------------------------------------------------------------------------------------------------------
    def _log_overview_errors(self) -> None:
        """
        Show info about sources files of stored routines that were not loaded successfully.
        """
        if self.__error_file_names:
            self._io.warning('Routines in the files below are not loaded:')
            self._io.listing(sorted(self.__error_file_names))

    # ------------------------------------------------------------------------------------------------------------------
    def _add_placeholder(self, name: str, value: str, quote: bool):
        """
        Adds a replacement to the map of replacement pairs.

        :param name: The name of the replacement pair.
        :param value: The value of the replacement pair.
        :param quote: Whether to quote the value.
        """
        key = '@' + name + '@'

        class_name = value.__class__.__name__

        if class_name in ['int', 'float']:
            self.__placeholders.add_placeholder(key, str(value))
        elif class_name in ['bool']:
            self.__placeholders.add_placeholder(key, '1' if value else '0')
        elif class_name in ['str']:
            self.__placeholders.add_placeholder(key, "'" + value + "'" if quote else value)
        else:
            self._io.log_verbose("Ignoring constant {} which is an instance of {}".format(name, class_name))

    # ------------------------------------------------------------------------------------------------------------------
    def _add_type_hint(self, hint: str, data_type: str):
        """
        Adds a type hint to the map of type hints.

        :param hint: The type hint.
        :param data_type: The actual data type.
        """
        self.__type_hints.add_type_hint(hint, data_type)

    # ------------------------------------------------------------------------------------------------------------------
    def _load_list(self, file_names: List[str] | None) -> None:
        """
        Loads all stored routines in a list into the RDBMS instance.

        :param file_names: The list of files to be loaded.
        """
        self._connect()
        self._find_source_files_from_list(file_names)
        self._fetch_column_types()
        self._fetch_constants()
        self._read_pystratum_metadata()
        self._init_rdbms_stored_routine_metadata()
        self._init_rdbms_specific()
        self._load_stored_routines()
        self._write_pystratum_metadata()
        self._disconnect()

    # ------------------------------------------------------------------------------------------------------------------
    def _load_all(self) -> None:
        """
        Loads all stored routines into the RDBMS instance.
        """
        self._connect()
        self._find_source_files()
        self._fetch_column_types()
        self._fetch_constants()
        self._read_pystratum_metadata()
        self._init_rdbms_stored_routine_metadata()
        self._init_rdbms_specific()
        self._load_stored_routines()
        self._drop_obsolete_routines()
        self._write_pystratum_metadata()
        self._disconnect()

    # ------------------------------------------------------------------------------------------------------------------
    def _read_configuration_file(self) -> None:
        """
        Reads parameters from the configuration file.
        """
        self.__source_directory = self._config.get('loader', 'source_directory')
        self.__source_file_extension = self._config.get('loader', 'extension')
        self.__source_file_encoding = self._config.get('loader', 'encoding')
        self.__pystratum_metadata_path = self._config.get('wrapper', 'metadata')
        self.__constants_class_name = self._config.get('constants', 'class', fallback=None)

    # ------------------------------------------------------------------------------------------------------------------
    def _find_source_files(self) -> None:
        """
        Searches recursively for all source files in a directory.
        """
        for dir_path, _, files in os.walk(self.__source_directory):
            for name in files:
                if name.lower().endswith(self.__source_file_extension):
                    basename = os.path.splitext(os.path.basename(name))[0]
                    relative_path = os.path.relpath(os.path.join(dir_path, name))

                    if basename in self.__source_file_names:
                        self._io.error("Files '{0}' and '{1}' have the same basename.".format(
                                self.__source_file_names[basename], relative_path))
                        self.__error_file_names.add(relative_path)
                    else:
                        self.__source_file_names[basename] = relative_path

    # ------------------------------------------------------------------------------------------------------------------
    def _read_pystratum_metadata(self) -> None:
        """
        Reads the metadata of the stored routines.
        """
        try:
            with open(self.__pystratum_metadata_path, 'r') as file:
                metadata = json.load(file)
                if metadata['pystratum_metadata_revision'] == self._pystratum_metadata_revision():
                    self.__pystratum_metadata = metadata['stored_routines']
                else:
                    self.__pystratum_metadata = {}
        except Exception:
            self.__pystratum_metadata = {}

    # ------------------------------------------------------------------------------------------------------------------
    def _load_stored_routines(self) -> None:
        """
        Loads all stored routines into the RDBMS instance.
        """
        for routine_name in sorted(self.__source_file_names):
            routine_source = StoredRoutineHelper(routine_name,
                                                 self.__source_file_names[routine_name],
                                                 self.__source_file_encoding)
            doc_block = DocBlockHelper(routine_source)
            old_rdbms_metadata = self.__rdbms_metadata.get(routine_name)
            old_pystratum_metadata = self.__pystratum_metadata.get(routine_name)
            new_pystratum_metadata = {}

            context = LoaderContext(stored_routine=routine_source,
                                    type_hints=self.__type_hints,
                                    doc_block=doc_block,
                                    placeholders=self.__placeholders,
                                    old_rdbms_metadata=old_rdbms_metadata,
                                    old_pystratum_metadata=old_pystratum_metadata,
                                    new_pystratum_metadata=new_pystratum_metadata)

            routine_loader = self._create_routine_loader(context)
            success = routine_loader.load_stored_routine(context)

            if success is False:
                self.__error_file_names.add(self.__source_file_names[routine_name])
                self.__pystratum_metadata.pop('routine_name', None)
            elif success is True:
                self.__pystratum_metadata[routine_name] = context.new_pystratum_metadata

    # ------------------------------------------------------------------------------------------------------------------
    def _write_pystratum_metadata(self) -> None:
        """
        Writes the metadata of all stored routines to the metadata file.
        """
        with open(self.__pystratum_metadata_path, 'w') as stream:
            metadata = {'pystratum_metadata_revision': self._pystratum_metadata_revision(),
                        'stored_routines':             self.__pystratum_metadata}
            json.dump(metadata, stream, indent=4, sort_keys=True)

    # ------------------------------------------------------------------------------------------------------------------
    def _find_source_files_from_list(self, file_names: List[str]) -> None:
        """
        Finds all source files that actually exist from a list of file names.

        :param file_names: The list of file names.
        """
        for file_name in file_names:
            if os.path.exists(file_name):
                routine_name = os.path.splitext(os.path.basename(file_name))[0]
                if routine_name not in self.__source_file_names:
                    self.__source_file_names[routine_name] = file_name
                else:
                    self._io.error("Files '{0}' and '{1}' have the same basename.".format(
                            self.__source_file_names[routine_name], file_name))
                    self.__error_file_names.add(file_name)
            else:
                self._io.error("File not exists: '{0}'".format(file_name))
                self.__error_file_names.add(file_name)

    # ------------------------------------------------------------------------------------------------------------------
    def _fetch_constants(self) -> None:
        """
        Gets the constants from the class that acts like a namespace for constants and adds them to the replacement
        pairs.
        """
        if self.__constants_class_name:
            helper = ConstantClass(self.__constants_class_name, self._io)
            helper.reload()
            constants = helper.constants()

            for name, value in constants.items():
                self._add_placeholder(name, value, True)

            self._io.text('Read {0} constants for substitution from <fso>{1}</fso>'.format(len(constants),
                                                                                           helper.file_name()))

    # ------------------------------------------------------------------------------------------------------------------
    def _init_rdbms_specific(self) -> None:
        """
        Executes RDBMS specific initializations.
        """
        pass

    # ------------------------------------------------------------------------------------------------------------------
    def _init_rdbms_stored_routine_metadata(self) -> None:
        """
        Loads the metadata of all stored routines currently the RDBMS instance.
        """
        rows = self._fetch_rdbms_metadata()
        for row in rows:
            self.__rdbms_metadata[row['routine_name']] = row

    # ------------------------------------------------------------------------------------------------------------------
    @staticmethod
    def _pystratum_metadata_revision() -> str:
        """
        Returns the revision of the format of the metadata of the stored routines.
        """
        return '4'

# ----------------------------------------------------------------------------------------------------------------------
