import abc

from pystratum_common.BuildContext import BuildContext
from pystratum_common.wrapper.Wrapper import Wrapper


class RowsWithIndexWrapper(Wrapper):
    """
    Parent class wrapper method generator for stored procedures whose result set  must be returned using tree
    structure using a combination of non-unique columns.
    """

    # ------------------------------------------------------------------------------------------------------------------
    def _return_type_hint(self, context: BuildContext) -> str:
        """
        Returns the return type of the wrapper method.

        :param context: The build context.
        """
        context.code_store.add_import('typing', 'Dict')

        return 'Dict'

    # ------------------------------------------------------------------------------------------------------------------
    @abc.abstractmethod
    def _build_execute_rows(self, context: BuildContext) -> None:
        """
        Builds the code for invoking the stored routine.

        :param context: The build context.
        """
        raise NotImplementedError()

    # ------------------------------------------------------------------------------------------------------------------
    def _build_result_handler(self, context: BuildContext) -> None:
        """
        Builds the code for calling the stored routine in the wrapper method.

        :param context: The build context.
        """
        context.code_store.append_line('ret = {}')
        self._build_execute_rows(context)
        context.code_store.append_line('for row in rows:')

        num_of_dict = len(context.routine['columns'])

        i = 0
        while i < num_of_dict:
            value = "row['{0!s}']".format(context.routine['columns'][i])

            stack = ''
            j = 0
            while j < i:
                stack += "[row['{0!s}']]".format(context.routine['columns'][j])
                j += 1
            line = 'if {0!s} in ret{1!s}:'.format(value, stack)
            context.code_store.append_line(line)
            i += 1

        line = 'ret'
        for column_name in context.routine['columns']:
            line += "[row['{0!s}']]".format(column_name)
        line += '.append(row)'
        context.code_store.append_line(line)
        context.code_store.decrement_indent_level()

        i = num_of_dict
        while i > 0:
            context.code_store.append_line('else:')

            part1 = ''
            j = 0
            while j < i - 1:
                part1 += "[row['{0!s}']]".format(context.routine['columns'][j])
                j += 1
            part1 += "[row['{0!s}']]".format(context.routine['columns'][j])

            part2 = ''
            j = i - 1
            while j < num_of_dict:
                if j + 1 != i:
                    part2 += "{{row['{0!s}']: ".format(context.routine['columns'][j])
                j += 1
            part2 += "[row]" + ('}' * (num_of_dict - i))

            line = "ret{0!s} = {1!s}".format(part1, part2)
            context.code_store.append_line(line)
            context.code_store.decrement_indent_level()
            if i > 1:
                context.code_store.decrement_indent_level()
            i -= 1

        context.code_store.append_line()
        context.code_store.decrement_indent_level()
        context.code_store.append_line('return ret')

# ----------------------------------------------------------------------------------------------------------------------
