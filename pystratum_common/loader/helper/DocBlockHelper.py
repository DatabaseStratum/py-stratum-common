import re
from typing import Any, Dict, List, Tuple

from pystratum_common.exception.LoaderException import LoaderException
from pystratum_common.loader.helper.DocBlockReflection import DocBlockReflection
from pystratum_common.loader.helper.StoredRoutineHelper import StoredRoutineHelper


class DocBlockHelper:
    """
    Helper class for extracting information for the Docblock of a stored routine.
    """

    # ------------------------------------------------------------------------------------------------------------------
    def __init__(self, routine_source: StoredRoutineHelper):
        """
        Object constructor.

        :param routine_source: The routine source helper.
        """
        self.__doc_block_reflection = DocBlockHelper.__create_doc_block_reflection(routine_source)

        self.__param_tags_have_types: bool = False
        """
        Whether @param tags have types. 
        """

        self.__designation: Dict[str, Any] | None = None
        """
        The designation of the stored routine.
        """

    # ------------------------------------------------------------------------------------------------------------------
    @property
    def param_tags_have_types(self):
        """
        Whether @param tags have types.
        """
        return self.__param_tags_have_types

    # ------------------------------------------------------------------------------------------------------------------
    @param_tags_have_types.setter
    def param_tags_have_types(self, param_tags_have_types: bool) -> None:
        """
        Set whether @param tags have types.

        :param param_tags_have_types: Whether @param tags have types.
        """
        self.__param_tags_have_types = param_tags_have_types

    # ------------------------------------------------------------------------------------------------------------------
    @property
    def designation(self) -> Dict[str, str]:
        """
        Returns the designation of the stored routine.
        """
        if self.__designation is None:
            tags = self.__doc_block_reflection.get_tags('type')
            if len(tags) == 0:
                raise LoaderException('Tag @type not found.')
            if len(tags) > 1:
                raise LoaderException('Found multiple @type tags.')

            tag = tags[0]
            parts1 = re.match(r'^(@type)\s+(?P<type>\w+)\s*(?P<extra>.*)', tag, re.DOTALL)
            if not parts1:
                raise LoaderException(f'Found @type tag without designation type. Found: {tag}')

            self.__designation = {'type': parts1.group('type')}

            if self.__designation['type'] in ['rows_with_key', 'rows_with_index']:
                if parts1.group('extra').strip() != '':
                    self.__designation['columns'] = re.split('[,\t\n ]+', parts1.group('extra'))
                else:
                    raise LoaderException(f'Designation type {self.__designation['type']} requires a list of columns. '
                                          f'Found: {tag}')

            elif self.__designation['type'] == 'insert_many':
                parts2 = re.match(r'^(?P<table_name>\w+)\s*(?P<keys>.+)', parts1.group('extra'), re.DOTALL)
                if not parts2:
                    raise LoaderException(f'Designation type insert_many requires a table name and a list of keys. '
                                          f'Found: {tag}')
                self.__designation['table_name'] = parts2.group('table_name')
                self.__designation['keys'] = re.split('[,\t\n ]+', parts2.group('keys'))

            elif self.__designation['type'] in ['singleton0', 'singleton1', 'function']:
                if parts1.group('extra').strip() != '':
                    self.__designation['return'] = re.split('[,|\t\n ]+', parts1.group('extra'))
                else:
                    raise LoaderException(f'Designation type {self.__designation['type']} requires a list of return ',
                                          f'types. Found: {tag}')

            elif parts1.group('extra').strip() != '':
                raise LoaderException(f'Superfluous data found after designation type {self.__designation['type']}. '
                                      f'Found: {tag}')

        return self.__designation

    # ------------------------------------------------------------------------------------------------------------------
    def description(self) -> str:
        """
        Returns the description of the stored routine.
        """
        return self.__doc_block_reflection.get_description()

    # ------------------------------------------------------------------------------------------------------------------
    def parameters(self) -> List[Dict[str, str]]:
        """
        Returns the parameters as found in the DocBlock of the stored routine.
        """
        parameters = []
        for tag in self.__doc_block_reflection.get_tags('param'):
            if self.__param_tags_have_types:
                parts = re.match(r'^(@param)\s+(?P<type>\w+)\s+:?(?P<name>\w+)\s*(?P<description>.+)?', tag, re.DOTALL)
                if parts:
                    parameters.append({'name':        parts.group('name'),
                                       'type':        parts.group('type'),
                                       'description': parts.group('description')})
            else:
                parts = re.match(r'^(@param)\s+(?P<name>\w+)\s*(?P<description>.+)?', tag, re.DOTALL)
                if parts:
                    parameters.append({'name':        parts.group('name'),
                                       'description': parts.group('description')})

        return parameters

    # ------------------------------------------------------------------------------------------------------------------
    def parameter_description(self, name: str) -> str:
        """
        Returns the description of a parameter as found in the DocBlock of the stored routine.

        :param name: The name of the parameter.
        """
        for parameter in self.parameters():
            if parameter['name'] == name:
                return parameter['description']

        return ''

    # ------------------------------------------------------------------------------------------------------------------
    @staticmethod
    def __create_doc_block_reflection(routine_source: StoredRoutineHelper) -> DocBlockReflection:
        """
        Creates the DocBlock reflection object.

        :param routine_source: The routine source helper.
        """
        line1, line2 = DocBlockHelper.__get_doc_block_lines(routine_source)
        doc_block = routine_source.code_lines[line1:line2 - line1 + 1]

        return DocBlockReflection(doc_block)

    # ------------------------------------------------------------------------------------------------------------------
    @staticmethod
    def __get_doc_block_lines(routine_source: StoredRoutineHelper) -> Tuple[int, int]:
        """
        Returns the start and end line of the DocBlock of the stored routine code.

        :param routine_source: The routine source helper.
        """
        line1 = None
        line2 = None

        i = 0
        for line in routine_source.code_lines:
            if re.match(r'\s*/\*\*', line):
                line1 = i

            if re.match(r'\s*\*/', line):
                line2 = i
                break

            i += 1

        if line1 is None or line2 is None:
            raise LoaderException("No DocBlock found in {}.".format(routine_source.path))

        return line1, line2

# ----------------------------------------------------------------------------------------------------------------------
