import copy
import re
from typing import Dict, List

from pystratum_common.exception.LoaderException import LoaderException
from pystratum_common.loader.helper.CommonDataTypeHelper import CommonDataTypeHelper


class TypeHintHelper:
    """
    Class for replacing type hints with their actual data types in stored routines.
    """

    # ------------------------------------------------------------------------------------------------------------------
    def __init__(self):
        """
        Object constructor.
        """
        self.__type_hints: Dict[str, str] = {}
        """
        The map from type hints to their actual data types.
        """

    # ------------------------------------------------------------------------------------------------------------------
    def add_type_hint(self, type_hint: str, data_type: str) -> None:
        """
        Adds a type hint with its actual data type.

        :param type_hint: The type hint.
        :param data_type: The actual data type of the type hint.
        """
        self.__type_hints[type_hint] = data_type

    # ------------------------------------------------------------------------------------------------------------------
    def update_types(self, code_lines: List[str], data_type_helper: CommonDataTypeHelper) -> List[str]:
        """
        Updates types in the source of the stored routine according to the type hints.

        :param code_lines: The source of the stored routine as an array of lines.
        :param data_type_helper: The data type helper.
        """
        all_columns_types = '|'.join(data_type_helper.all_column_types())
        parts = {'whitespace': r'(?P<whitespace>\s+)',
                 'type_list':  r'(?P<datatype>(type-list)(?P<extra>.*)?)'.replace('type-list', all_columns_types),
                 'hint':       r'(?P<hint>\s+--\s+type:\s+(\w+\.)?\w+\.\w+(%max)?\s*)$'}
        pattern = ''.join(parts.values())

        code_lines = copy.copy(code_lines)
        for index, line in enumerate(code_lines):
            if re.search(parts['hint'], line):
                matches = re.search(pattern, line, re.IGNORECASE)
                if not matches:
                    raise LoaderException(f'Found a type hint at line {index + 1}, but unable to find data type.')

                hint = re.sub(r'\s+--\s+type:\s+', '', matches['hint'], re.IGNORECASE)
                if hint not in self.__type_hints:
                    raise LoaderException(f"Unknown type hint '{hint}' found at line {index + 1}.")

                other = re.search(r'(?P<extra1> not\s+null)?\s*(?P<extra2> default.+)?\s*(?P<extra3>[;,]\s*)?$',
                                  matches['datatype'],
                                  re.IGNORECASE)
                if other:
                    extra1 = other.group('extra1') or ''
                    extra2 = other.group('extra2') or ''
                    extra3 = other.group('extra3') or ''
                else:
                    extra1 = ''
                    extra2 = ''
                    extra3 = ''

                actual_type = self.__type_hints[hint]
                new_line = '{}{}{}{}{}{}{}'.format(line[0:-len(matches[0])],
                                                   matches['whitespace'],
                                                   actual_type,  # <== the real replacement
                                                   extra1,
                                                   extra2,
                                                   extra3,
                                                   matches['hint'])

                if line.replace(' ', '') != new_line.replace(' ', ''):
                    code_lines[index] = new_line

        return code_lines

    # ------------------------------------------------------------------------------------------------------------------
    def align_type_hints(self, code_lines: List[str]) -> List[str]:
        """
        Aligns the type hints in the source of the stored routine.

        :param code_lines: The source of the stored routine as an array of lines.
        """
        blocks = []
        start = None
        length = 0
        for index, line in enumerate(code_lines):
            match = re.search(r'--\s+type:\s+.*$', line)
            if match:
                if start is None:
                    start = index
                length = max(length, len(line) - len(match.group(0)) + 2)
            else:
                if start is not None:
                    blocks.append({'first': start, 'last': index, 'length': length})
                    start = None
                    length = 0

        for block in blocks:
            for index in range(block['first'], block['last']):
                matches = re.search(r'\s+type:\s+.*$', code_lines[index])
                left_part = code_lines[index][0:-len(matches.group(0))].rstrip()
                left_part = left_part + ' ' * (block['length'] - len(left_part) + 1)
                code_lines[index] = left_part + matches.group(0).lstrip()

        return code_lines

    # ------------------------------------------------------------------------------------------------------------------
    def extract_type_hints(self, path: str, code: str) -> Dict[str, str]:
        """
        Returns the type hints in the source of a stored routine.

        :param path: The path to the source of the stored routine.
        :param code: The source of the stored routine.
        """
        type_hints = {}

        for match in re.finditer(r'(\s+--\s+type:\s+(?P<type_hint>(\w+\.)?\w+\.\w+(%max)?))', code):
            type_hint = match.group('type_hint')
            if type_hint not in self.__type_hints:
                raise LoaderException("Unknown type hint '{0}' in file {1}".format(type_hint, path))
            type_hints[type_hint] = self.__type_hints[type_hint]

        return type_hints

    # ------------------------------------------------------------------------------------------------------------------
    def compare_type_hints(self, type_hints: Dict[str, str]) -> bool:
        """
        Returns whether a set of type hints equals with the current type hints and actual data types.

        :param type_hints: The set of type hints.
        """
        for type_hint, data_type in type_hints.items():
            if type_hint not in self.__type_hints or data_type != self.__type_hints[type_hint]:
                return False

        return True

# ----------------------------------------------------------------------------------------------------------------------
