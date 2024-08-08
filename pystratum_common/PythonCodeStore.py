from typing import List, Set


class PythonCodeStore:
    """
    Class for automatically generating Python code with proper indentation.
    """

    # ------------------------------------------------------------------------------------------------------------------
    def __init__(self):
        """
        Object constructor.
        """
        self.__page_width: int = 120
        """
        The maximum number of columns in the source code.
        """

        self.__lines: List[str] = []
        """
        The lines of Python code.
        """

        self.__imports: Set[str] = set()
        """
        The list of imports.
        """

        self.__indent_level: int = 0
        """
        The current level of indentation in the generated code.
        """

    # ------------------------------------------------------------------------------------------------------------------
    def get_code(self) -> str:
        """
        Returns the generated code.
        """
        code = ''

        if self.__imports:
            code = '\n'.join(sorted(self.__imports))
            code += '\n\n\n'

        code += '\n'.join(self.__lines)

        return code

    # ------------------------------------------------------------------------------------------------------------------
    def append_line(self, line: str = '') -> None:
        """
        Appends a line to the code.

        :param line: The line of code.
        """
        if line:
            line = (' ' * 4 * self.__indent_level) + str(line)
        else:
            line = ''

        self.__lines.append(str(line))

        if line[-1:] == ':':
            self.__indent_level += 1

    # ------------------------------------------------------------------------------------------------------------------
    def append_separator(self) -> None:
        """
        Inserts a horizontal (commented) line tot the generated code.
        """
        tmp = self.__page_width - ((4 * self.__indent_level) + 2)
        self.__lines.append((' ' * 4 * self.__indent_level) + '# ' + ('-' * tmp))

    # ------------------------------------------------------------------------------------------------------------------
    def add_import(self, package_name: str, module_name: str) -> None:
        """
        Adds an import of a module of a package.

        :param module_name: The name of the package.
        :param package_name: The name of the module.
        """
        self.__imports.add(f'from {package_name} import {module_name}')

    # ------------------------------------------------------------------------------------------------------------------
    def decrement_indent_level(self, levels: int = 1) -> None:
        """
        Decrements the indent level of the generated code.

        :param levels: The number of levels indent level of the generated code must be decremented.
        """
        self.__indent_level -= int(levels)

# ----------------------------------------------------------------------------------------------------------------------
