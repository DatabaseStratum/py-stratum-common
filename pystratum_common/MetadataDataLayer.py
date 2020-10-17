import os

from pystratum_backend.StratumStyle import StratumStyle


class MetadataDataLayer:
    """
    Data layer for retrieving metadata and loading stored routines.
    """

    # ------------------------------------------------------------------------------------------------------------------
    def __init__(self, io: StratumStyle):
        """
        Object constructor.

        :param PyStratumStyle io: The output decorator.
        """

        self._io: StratumStyle = io
        """
        The output decorator.
        """

    # ------------------------------------------------------------------------------------------------------------------
    def _log_query(self, query: str) -> None:
        """
        Logs the query on the console.

        :param str query: The query.
        """
        query = query.strip()

        if os.linesep in query:
            # Query is a multi line query
            self._io.log_very_verbose('Executing query:')
            self._io.log_very_verbose('<sql>{0}</sql>'.format(query))
        else:
            # Query is a single line query.
            self._io.log_very_verbose('Executing query: <sql>{0}</sql>'.format(query))

# ----------------------------------------------------------------------------------------------------------------------
