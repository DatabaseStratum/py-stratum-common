import os
from typing import Dict, List

from pystratum_backend.StratumIO import StratumIO

from pystratum_common.exception.LoaderException import LoaderException
from pystratum_common.helper.Util import Util


class StoredRoutineHelper:
    """
    Helper class for the source and metadata of a stored routine.
    """

    # ------------------------------------------------------------------------------------------------------------------
    def __init__(self, name: str, path: str, encoding: str):
        """
        Object constructor.

        :param name: The name of the stored routine.
        :param path: The path to the source of the stored routine.
        :param encoding: The encoding of the source of the stored routine.
        """
        self.__name: str = name
        """
        The name of the stored routine.
        """

        self.__path: str = path
        """
        The path to the source of the stored routine.
        """

        self.__encoding: str = encoding
        """
        The encoding of the source of the stored routine.
        """

        self.__code: str | None = None
        """
        The code of the stored routine.
        """

        self.__code_lines: List[str] | None = None
        """
        The code of the stored routine as an array of strings.
        """

        self.__m_time: int = 0
        """
        The last modification time of the source file.
        """

        self.__type: str | None = None
        """
        The type (procedure or function) of the stored routine.
        """

        self.__parameters: List[Dict[str, str | int | None]] | None = None
        """
        The metadata of the parameters of the stored routine.
        """

    # ------------------------------------------------------------------------------------------------------------------
    @property
    def path(self) -> str:
        """
        The path to the source of the stored routine.
        """
        return self.__path

    # ------------------------------------------------------------------------------------------------------------------
    @property
    def encoding(self) -> str:
        """
        The encoding of the stored routine.
        """
        return self.__encoding

    # ------------------------------------------------------------------------------------------------------------------
    @property
    def code(self) -> str:
        """
        The code of the stored routine.
        """
        if self.__code is None:
            self.__read_source_file()

        return self.__code

    # ------------------------------------------------------------------------------------------------------------------
    @property
    def code_lines(self) -> List[str]:
        """
        The code of the stored routine as an array of strings.
        """
        if self.__code_lines is None:
            self.__read_source_file()

        return self.__code_lines

    # ------------------------------------------------------------------------------------------------------------------
    @property
    def m_time(self) -> int:
        """
        The last modification time of the source file.
        """
        if self.__m_time is None:
            self.__read_source_file()

        return self.__m_time

    # ------------------------------------------------------------------------------------------------------------------
    @property
    def name(self) -> str:
        """
        Returns the name of the stored routine.
        """
        return self.__name

    # ------------------------------------------------------------------------------------------------------------------
    @property
    def parameters(self) -> List[Dict[str, str | int | None]]:
        """
        Returns the metadata of the parameters of the stored routine.
        """
        if self.__parameters is None:
            raise LoaderException("Parameters has not been set yet.")

        return self.__parameters

    # ------------------------------------------------------------------------------------------------------------------
    @parameters.setter
    def parameters(self, parameters: List[Dict[str, str | int | None]]) -> None:
        """
        Sets the metadata of the parameters of the stored routine.
        """
        if self.__parameters is not None:
            raise LoaderException("Parameters have been set already.")

        self.__parameters = parameters

    # ------------------------------------------------------------------------------------------------------------------
    @property
    def type(self) -> str:
        """
        Returns the type of the stored routine.
        """
        if self.__type is None:
            raise LoaderException("Type has not been set yet.")

        return self.__type

    # ------------------------------------------------------------------------------------------------------------------
    @type.setter
    def type(self, routine_type: str) -> None:
        """
        Sets the name of the stored routine.
        """
        if self.__type is not None:
            raise LoaderException("Type has been set already.")

        self.__type = routine_type

    # ------------------------------------------------------------------------------------------------------------------
    def update_source(self, code: str, io: StratumIO) -> None:
        """
        Updates the source of the stored routine if the new code is different from the current code.

        :param code: The new code.
        :param io: The output decorator.
        """
        if self.__code != code:
            Util.write_two_phases(self.__path, code, io)
            self.__read_source_file()

    # ------------------------------------------------------------------------------------------------------------------
    def __read_source_file(self) -> None:
        """
        Reads the file with the source of the stored routine.
        """
        try:
            with open(self.__path, 'r', encoding=self.__encoding) as file:
                self.__code = file.read()

            self.__m_time = int(os.path.getmtime(self.__path))

        except Exception as exception:
            raise LoaderException("Unable to read '{}' caused by {}.".format(self.__path, exception))

        self.__code_lines = self.__code.split('\n')

# ----------------------------------------------------------------------------------------------------------------------
