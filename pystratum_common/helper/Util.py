import os

from pystratum_backend.StratumIO import StratumIO


class Util:
    """
    A utility class with miscellaneous functions that don't belong somewhere else.
    """

    # ------------------------------------------------------------------------------------------------------------------
    @staticmethod
    def write_two_phases(filename: str, data: str, io: StratumIO) -> None:
        """
        Writes a file in two phase to the filesystem.

        First write the data to a temporary file (in the same directory) and then renames the temporary file. If the
        file already exists and its content is equal to the data that must be written no action is taken. This has the
        following advantages:
        *   In case of some write error (e.g. disk full) the original file is kept intact and no file with partially
            data is written.
        *   Renaming a file is atomic. So, running processes will never read a partially written data.

        :param filename: The name of the file were the data must be stored.
        :param data: The data that must be written.
        :param io: The output decorator.
        """
        write_flag = True
        if os.path.exists(filename):
            with open(filename, 'r') as file:
                old_data = file.read()
                if data == old_data:
                    write_flag = False

        if write_flag:
            tmp_filename = filename + '.tmp'
            with open(tmp_filename, 'w+') as file:
                file.write(data)
            os.replace(tmp_filename, filename)
            io.text('Wrote: <fso>{0}</fso>'.format(filename))
        else:
            io.text('File <fso>{0}</fso> is up to date'.format(filename))

# ----------------------------------------------------------------------------------------------------------------------
