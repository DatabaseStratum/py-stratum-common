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
    def add_type_hint(self, hint: str, data_type: str) -> None:
        """
        Adds a type hint with its actual data type.

        :param hint: The name of the placeholder.
        :param data_type: The actual value of the placeholder.
        """
        self.__type_hints[hint] = data_type

    # ------------------------------------------------------------------------------------------------------------------
    def update_types(self, code_lines: List[str], data_type_helper: CommonDataTypeHelper) -> List[str]:
        """
        Updates types in the source of the stored routine according to the type hints.

        :param code_lines: The source of the stored routine as an array of lines.
        :param data_type_helper: The data type helper.
        """
        new_code_lines = []

        all_columns_types = '|'.join(data_type_helper.all_column_types())
        parts = {'whitespace': r'(?P<whitespace>\s+)',
                 'type_list':  r'(?P<datatype>(type-list).*)'.replace('type-list', all_columns_types),
                 'nullable':   r'(?P<nullable>not\s+null)?',
                 'hint':       r'(?P<hint>\s+--\s+type:\s+.*)$'}
        pattern = ''.join(parts.values())

        for index, line in enumerate(code_lines):
            if re.search(parts['hint'], line):
                matches = re.search(pattern, line)
                if not matches:
                    raise LoaderException(f'Found a type hint at line {index + 1}, but unable to find data type.')

                hint = re.sub(r'\s+--\s+type:\s+', '', matches['hint'])
                if hint not in self.__type_hints:
                    raise LoaderException(f"Unknown type hint '{hint}' found at line {index + 1}.")

                other = re.search(r'(?P<punctuation>\s*[;,]\s*)$', matches['datatype'])
                if other:
                    punctuation = other['punctuation']
                else:
                    punctuation = ''

                actual_type = self.__type_hints[hint]
                new_line = '{}{}{}{}{}{}'.format(line[0:-len(matches[0])],
                                                 matches['whitespace'],
                                                 actual_type,  # <== the real update
                                                 matches['nullable'] if matches['nullable'] else '',
                                                 punctuation,
                                                 matches['hint'])

                if line.replace(' ', '') != new_line.replace(' ', ''):
                    new_code_lines.append(new_line)
                else:
                    new_code_lines.append(line)
            else:
                new_code_lines.append(line)

        return new_code_lines

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
    def get_type_hints(self, path: str, code: str) -> Dict[str, str]:
        """
        Returns the type hints found in the source of the stored routine.

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
        for hint, data_type in type_hints.items():
            if hint not in self.__type_hints or data_type != self.__type_hints[hint]:
                return False

        return True

# ----------------------------------------------------------------------------------------------------------------------
