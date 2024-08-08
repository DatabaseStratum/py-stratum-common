import os

from pystratum_backend.StratumIO import StratumIO


class CommonMetadataDataLayer:
    """
    Data layer for retrieving metadata and loading stored routines.
    """

    # ------------------------------------------------------------------------------------------------------------------
    def __init__(self, io: StratumIO):
        """
        Object constructor.

        :param io: The output decorator.
        """

        self._io: StratumIO = io
        """
        The output decorator.
        """

    # ------------------------------------------------------------------------------------------------------------------
    def _log_query(self, query: str) -> None:
        """
        Logs the query on the console.

        :param query: The query.
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
