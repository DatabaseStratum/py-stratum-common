import importlib
import inspect
import os
import re
from typing import Any, Dict, List

from pystratum_backend.StratumIO import StratumIO


class ConstantClass:
    """
    Helper class for loading and modifying the class that acts like a namespace for constants.
    """

    # ------------------------------------------------------------------------------------------------------------------
    def __init__(self, class_name: str, io: StratumIO):
        """
        Object constructor.

        :param class_name: The name of class that acts like a namespace for constants.
        :param io: The output decorator.
        """
        self.__class_name: str = class_name
        """
        The name of class that acts like a namespace for constants.
        """

        self.__module = None
        """
        The module of which the class that acts like a namespace for constants belongs.

        :type: module
        """

        self.__annotation: str = '# PyStratum'
        """
        The comment after which the auto generated constants must be inserted.
        """

        self._io: StratumIO = io
        """
        The output decorator.
        """

        self.__load()

    # ------------------------------------------------------------------------------------------------------------------
    def __load(self) -> None:
        """
        Loads dynamically the class that acts like a namespace for constants.
        """
        parts = self.__class_name.split('.')
        module_name = ".".join(parts[:-1])
        module = __import__(module_name)
        modules = []
        for comp in parts[1:]:
            module = getattr(module, comp)
            modules.append(module)

        self.__module = modules[-2]

    # ------------------------------------------------------------------------------------------------------------------
    def file_name(self) -> str:
        """
        Returns the filename of the module with the class that acts like a namespace for constants.
        """
        path = os.path.realpath(inspect.getfile(self.__module))
        cwd = os.path.realpath(os.getcwd())
        common = os.path.commonprefix([path, cwd])
        if common == cwd:
            return os.path.relpath(path, cwd)

        return path

    # ------------------------------------------------------------------------------------------------------------------
    def source(self) -> str:
        """
        Returns the source of the module with the class that acts like a namespace for constants.
        """
        return inspect.getsource(self.__module)

    # ------------------------------------------------------------------------------------------------------------------
    def reload(self) -> None:
        """
        Reloads the module with the class that acts like a namespace for constants.
        """
        importlib.reload(self.__module)

    # ------------------------------------------------------------------------------------------------------------------
    def constants(self) -> Dict[str, Any]:
        """
        Gets the constants from the class that acts like a namespace for constants.
        """
        ret = {}

        name = self.__class_name.split('.')[-1]
        constant_class = getattr(self.__module, name)
        for name, value in constant_class.__dict__.items():
            if re.match(r'^[A-Z][A-Z0-9_]*$', name):
                ret[name] = value

        return ret

    # ------------------------------------------------------------------------------------------------------------------
    def __extract_info(self, lines: List[str]) -> Dict[str, int | str]:
        """
        Extracts the following info from the source of the module with the class that acts like a namespace for
        constants:
        * Start line with constants
        * Last line with constants
        * Indent for constants

        :param lines: The source of the module with the class that acts like a namespace for constants.
        """
        ret = {'start_line': 0,
               'last_line':  0,
               'indent':     ''}

        mode = 1
        count = 0
        for line in lines:
            if mode == 1:
                if line.strip() == self.__annotation:
                    ret['start_line'] = count + 1
                    ret['last_line'] = count + 1
                    parts = re.match(r'^(\s+)', line)
                    ret['indent'] = parts.group(1)
                    mode = 2

            elif mode == 2:
                if line.strip() == '' or line.strip()[0:1] == '#':
                    mode = 3
                else:
                    ret['last_line'] = count + 1

            else:
                break

            count += 1

        if mode != 3:
            raise RuntimeError("Unable to find '{}' in file {}".format(self.__annotation, self.source()))

        return ret

    # ------------------------------------------------------------------------------------------------------------------
    def source_with_constants(self, constants: Dict[str, int]) -> str:
        """
        Returns the source of the module with the class that acts like a namespace for constants with new constants.

        :param constants: The new constants.
        """
        old_lines = self.source().split("\n")
        info = self.__extract_info(old_lines)

        new_lines = old_lines[0:info['start_line']]

        for constant, value in sorted(constants.items()):
            new_lines.append("{0}{1} = {2}".format(info['indent'], str(constant), str(value)))

        new_lines.extend(old_lines[info['last_line']:])

        return "\n".join(new_lines)

# ----------------------------------------------------------------------------------------------------------------------
