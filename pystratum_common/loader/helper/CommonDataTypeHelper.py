import abc
from typing import Any, Dict, List


class CommonDataTypeHelper(metaclass=abc.ABCMeta):
    """
    Utility class for deriving information based on a DBMS native data type.
    """

    # ------------------------------------------------------------------------------------------------------------------
    @abc.abstractmethod
    def all_column_types(self) -> List[str]:
        """
        Returns all column types supported by the RDBMS.
        """
        raise NotImplementedError()

    # ------------------------------------------------------------------------------------------------------------------
    @abc.abstractmethod
    def column_type_to_python_type(self, data_type_info: Dict[str, Any]) -> str:
        """
        Returns the corresponding Python data type of DBMS native data type.

        :param dict data_type_info: The DBMS native data type metadata.
        """
        raise NotImplementedError()

# ----------------------------------------------------------------------------------------------------------------------
