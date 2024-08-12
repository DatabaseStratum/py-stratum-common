import abc
import configparser
from typing import Dict

from pystratum_backend.ConstantWorker import ConstantWorker
from pystratum_backend.StratumIO import StratumIO

from pystratum_common.constant.ConstantClass import ConstantClass
from pystratum_common.helper.Util import Util


class CommonConstantWorker(ConstantWorker):
    """
    Abstract parent class for RDBMS specific classes for creating constants based on column widths, and auto increment
    columns and labels.
    """

    # ------------------------------------------------------------------------------------------------------------------
    def __init__(self, io: StratumIO, config: configparser.ConfigParser):
        """
        Object constructor.

        :param PyStratumIO io: The output decorator.
        """
        self._constants: Dict[str, int] = {}
        """
        All constants.
        """

        self._old_columns: Dict = {}
        """
        The previous column names, widths, and constant names (i.e. the content of self._constants_filename upon
        starting this program).
        """

        self._constants_filename: str | None = None
        """
        Filename with column names, their widths, and constant names.
        """

        self._prefix: str | None = None
        """
        The prefix used for designations a unknown constants.
        """

        self._class_name: str = ''
        """
        The name of the class that acts like a namespace for constants.
        """

        self._labels: Dict = {}
        """
        All primary key labels, their widths and constant names.
        """

        self._io: StratumIO = io
        """
        The output decorator.
        """

        self._config: configparser.ConfigParser = config
        """
        The configuration object.
        """

    # ------------------------------------------------------------------------------------------------------------------
    @abc.abstractmethod
    def _connect(self) -> None:
        """
        Connects to the database.
        """
        raise NotImplementedError()

    # ------------------------------------------------------------------------------------------------------------------
    @abc.abstractmethod
    def _disconnect(self) -> None:
        """
        Disconnects from the database.
        """
        raise NotImplementedError()

    # ------------------------------------------------------------------------------------------------------------------
    def execute(self) -> int:
        """
        Creates the constant's class.

        @rtype int:
        """
        self._read_configuration_file()

        if self._constants_filename:
            self._io.title('Constants')

            self._connect()
            self._get_old_columns()
            self._get_columns()
            self._enhance_columns()
            self._merge_columns()
            self._write_columns()
            self._get_labels()
            self._fill_constants()
            self._write_constant_class()
            self._disconnect()
            self._log_number_of_constants()

            self._io.write_line('')
        else:
            self._io.log_verbose('Constants not enabled')

        return 0

    # ------------------------------------------------------------------------------------------------------------------
    def _log_number_of_constants(self) -> None:
        """
        Logs the number of constants generated.
        """
        n_id = len(self._labels)
        n_widths = len(self._constants) - n_id

        self._io.write_line('')
        self._io.text('Number of constants based on column widths: {0}'.format(n_widths))
        self._io.text('Number of constants based on database IDs : {0}'.format(n_id))

    # ------------------------------------------------------------------------------------------------------------------
    def _read_configuration_file(self) -> None:
        """
        Reads parameters from the configuration file.
        """
        self._constants_filename = self._config.get('constants', 'columns')
        self._prefix = self._config.get('constants', 'prefix')
        self._class_name = self._config.get('constants', 'class')
        self._label_regex = self._config.get('constants', 'label_regex')

    # ------------------------------------------------------------------------------------------------------------------
    @abc.abstractmethod
    def _get_old_columns(self) -> None:
        """
        Reads from file constants_filename the previous table and column names, the width of the column,
        and the constant name (if assigned) and stores this data in old_columns.
        """
        raise NotImplementedError()

    # ------------------------------------------------------------------------------------------------------------------
    @abc.abstractmethod
    def _get_columns(self) -> None:
        """
        Retrieves metadata all columns in the MySQL schema.
        """
        raise NotImplementedError()

    # ------------------------------------------------------------------------------------------------------------------
    @abc.abstractmethod
    def _enhance_columns(self) -> None:
        """
        Enhances old_columns as follows:
        If the constant name is *, it is replaced with the column name prefixed by prefix in uppercase.
        Otherwise, the constant name is set to uppercase.
        """
        raise NotImplementedError()

    # ------------------------------------------------------------------------------------------------------------------
    @abc.abstractmethod
    def _merge_columns(self) -> None:
        """
        Preserves relevant data in old_columns into columns.
        """
        raise NotImplementedError()

    # ------------------------------------------------------------------------------------------------------------------
    @abc.abstractmethod
    def _write_columns(self) -> None:
        """
        Writes table and column names, the width of the column, and the constant name (if assigned) to
        constants_filename.
        """
        raise NotImplementedError()

    # ------------------------------------------------------------------------------------------------------------------
    @abc.abstractmethod
    def _get_labels(self) -> None:
        """
        Gets all primary key labels from the database.
        """
        raise NotImplementedError()

    # ------------------------------------------------------------------------------------------------------------------
    @abc.abstractmethod
    def _fill_constants(self) -> None:
        """
        Merges columns and labels (i.e. all known constants) into constants.
        """
        raise NotImplementedError()

    # ------------------------------------------------------------------------------------------------------------------
    def _write_constant_class(self) -> None:
        """
        Inserts new and replaces old (if any) constant declaration statements in the class that acts like a namespace
        for constants.
        """
        helper = ConstantClass(self._class_name, self._io)
        content = helper.source_with_constants(self._constants)
        Util.write_two_phases(helper.file_name(), content, self._io)

# ----------------------------------------------------------------------------------------------------------------------
