import re
from typing import Dict, List

from pystratum_common.exception.LoaderException import LoaderException


class PlaceholderHelper:
    """
    Class for replacing placeholder with their actual values in stored routines.
    """

    # ------------------------------------------------------------------------------------------------------------------
    def __init__(self):
        """
        Object constructor.
        """
        self.__placeholders: Dict[str, str] = {}
        """
        The map from placeholders to their actual values.
        """

    # ------------------------------------------------------------------------------------------------------------------
    def add_placeholder(self, name: str, value: str) -> None:
        """
        Adds a placeholder with its actual value.

        :param name: The name of the placeholder.
        :param value: The actual value of the placeholder.
        """
        self.__placeholders[name] = value

    # ------------------------------------------------------------------------------------------------------------------
    def substitute_placeholders(self, code_lines: List[str]) -> str:
        """
        Substitutes all replace pairs in the source of the stored routine.

        :param code_lines: The source of the stored routine as an array of lines.
        """
        new_code_lines = []

        for index, line in enumerate(code_lines):
            self.__placeholders['__LINE__'] = "'%d'" % (index + 1)
            for search, replace in self.__placeholders.items():
                line = line.replace(search, replace)
            new_code_lines.append(line)

        return '\n'.join(new_code_lines)

    # ------------------------------------------------------------------------------------------------------------------
    def get_placeholders(self, path: str, code: str) -> Dict[str, str]:
        """
        Returns the placeholders found in the source of the stored routine.

        :param path: The path to the source of the stored routine.
        :param code: The source of the stored routine.
        """
        placeholders = {}
        for match in re.finditer(r'(@[A-Za-z0-9_.]+(%(max-)?type)?@)', code):
            place_holder = match[0]
            if place_holder not in self.__placeholders:
                raise LoaderException("Unknown placeholder '{0}' in file {1}".format(place_holder, path))
            placeholders[place_holder] = self.__placeholders[place_holder]

        return placeholders

    # ------------------------------------------------------------------------------------------------------------------
    def compare_placeholders(self, placeholders: Dict[str, str]) -> bool:
        """
        Returns whether a set of placeholders equals with the current placeholders and actual values.

        :param placeholders: The set of placeholders.
        """
        for key, value in placeholders.items():
            if key not in self.__placeholders or value != self.__placeholders[key]:
                return False

        return True

# ----------------------------------------------------------------------------------------------------------------------
