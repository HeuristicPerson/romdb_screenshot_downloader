"""
Library to read and write csv files.

Log:
    28-05-2017 - Updated Col Process method to work fine when no data is present.

"""

import codecs


# Classes
#=======================================================================================================================
class ParsedCsv:
    def __init__(self):
        self.lu_comments = []  # Comment rows. They are written at the beginning of the output file with comment char.
        self.lu_headings = []  # Headings row. It goes after the comments and it doesn't include comment char.
        self.llu_rows = []     # Actual data rows.

    def __str__(self):
        return unicode(self).encode('utf8')

    def __unicode__(self):
        u_output = u''
        u_output += u'<ParsedCsv>\n'
        u_spc = u'  '

        li_longest_elements = []

        for i_column in range(0, self.num_columns()):
            i_longest_element = 0
            lu_elements = self.get_column(i_column)

            # 1st, we check the longest element in the data
            for u_element in lu_elements:
                i_longest_element = max(i_longest_element, len(u_element))

            # 2nd, we check the longest element in the heading
            try:
                i_longest_element = max(i_longest_element, len(self.lu_headings[i_column]))
            except IndexError:
                pass

            li_longest_elements.append(i_longest_element)

        # Total row width calculation
        i_total_width = sum(li_longest_elements) + len(u_spc) * (len(li_longest_elements) - 1)

        # Generating the comments
        if self.lu_comments:
            u_output += u'  #%s\n' % (u'=' * (i_total_width - 1))
            for u_comment_row in self.lu_comments:
                u_output += u'  # %s\n' % u_comment_row
            u_output += u'  #%s\n' % (u'=' * (i_total_width - 1))

        # Generating the output for each row
        if self.lu_headings:
            u_row_output = u''
            i_column = 0

            for u_element in self.lu_headings:
                u_row_output += u'%s  ' % u_element.ljust(li_longest_elements[i_column])
                i_column += 1

            u_row_output = u_row_output[:-2]
            u_output += u'  %s\n' % u_row_output
            u_output += u'  %s\n' % (u'-' * len(u_row_output))

        for lu_row in self.llu_rows:
            u_row_output = u''
            i_column = 0

            for u_element in lu_row:
                u_row_output += u'%s  ' % u_element.ljust(li_longest_elements[i_column])
                i_column += 1

            u_row_output = u_row_output[:-2]
            u_output += u'  %s\n' % u_row_output

        return u_output

    def append_row(self, lu_row):
        """
        Method to append a new row at the end of the array.

        :param lu_row: Row to append. i.e. ['foo', 'bar', 23]

        :return: Nothing
        """
        lu_clean_row = []

        for u_element in lu_row:
            lu_clean_row.append(unicode(u_element).strip())

        self.llu_rows.append(lu_clean_row)

    def get_column(self, pi_column):
        """
        Method to obtain the data of one column as a list.

        :param pi_column: Number of the column. i.e. 3 (The first column is number 0)

        :return: A list of unicode elements. '' if the cell is empty.
        """

        lu_values = []

        for lu_row in self.llu_rows:
            try:
                lu_values.append(lu_row[pi_column])
            except IndexError:
                lu_values.append(u'')

        return lu_values

    def get_row(self, pi_row):
        """
        Method to obtain the data of one row as a list.
        :param pi_row:
        :return: A list of unicode elements. '' if the cell is empty
        """

        try:
            lu_output = self.llu_rows[pi_row]
        except IndexError:
            lu_output = []

        return lu_output

    def from_plain_unicode(self, pu_data, pu_sep=u',', pu_com=u'#', pb_headings=False):
        """
        Method to populate the object from an unicode string.
        :param pu_data:
        :param pu_sep:
        :param pu_com:
        :param pb_headings:
        :return:
        """

        # TODO: Clear the object content before importing new one... or add another parameter to append/rewrite.

        i_data_line = 0

        for u_line in pu_data.splitlines():
            # Getting comments
            # -----------------
            # This method of reading comments anywhere in the file and adding them to a comments section has a big
            # caveat: If you read a csv file and then you save it to disk again, all the comments are going to be moved
            # to the heading of the file. So, if the comments' position is relevant, reading and saving files can be a
            # big issue. It's not at all for the purpose of HQ Tools.
            if u_line[0] == pu_com:
                u_line = u_line.lstrip(u'%s ' % pu_com)
                u_line = u_line.rstrip(u'\n')
                self.lu_comments.append(u_line)

            # Getting data
            # -------------
            else:
                i_data_line += 1
                u_clean_line = _line_clean(u_line)
                lu_line_fields = u_clean_line.split(pu_sep)

                if pb_headings and i_data_line == 1:
                    self.lu_headings = lu_line_fields
                else:
                    self.append_row(lu_line_fields)

    def load_from_disk(self, pu_file=u'', pu_sep=u',', pu_com=u'#', pb_headings=False):
        """
        Method to populate the object with data from a csv file.

        :param pu_file: Path of the file. i.e. '/home/john/my_file.csv'

        :param pu_sep: Separator for fields. i.e. ';'

        :param pu_com: Comment indicator (lines starting with this character will be ignored). i.e. '#'

        :param pb_headings: True => 1st row of data will be considered headings
                            False =>

        :return: Nothing
        """
        # TODO: give the option to append or to rewrite.

        o_file = codecs.open(pu_file.encode('utf8'), 'r', 'utf8')
        u_data = o_file.read()
        o_file.close()

        self.from_plain_unicode(u_data, pu_sep=pu_sep, pu_com=pu_com, pb_headings=pb_headings)

    def num_columns(self):
        """
        Method to obtain the number of columns stored.
        :return: an integer. i.e. 24
        """
        i_columns = 0

        # 1st, check the number of columns in the data
        for lu_row in self.llu_rows:
            i_columns = max(i_columns, len(lu_row))

        # 2nd, check the number of columns in the headings
        i_columns = max(i_columns, len(self.lu_headings))

        return i_columns

    def to_plain_unicode(self, pu_sep=u',', pu_com=u'#', pb_just_data=False):
        """
        Function to convert the Csv object to a plain unicode string without any fanciness.
        :param pu_sep: Separation character.
        :param pu_com: Comment character.
        :type pb_just_data: Boolean To print just data lines without comments or headings.
        :return: An unicode string.
        """
        u_output = u''

        # Comments
        #---------
        if not pb_just_data:
            for u_comment in self.lu_comments:
                u_output += u'%s %s\n' % (pu_com, u_comment)

        # Headings and data
        #------------------
        if pb_just_data:
            llu_data = self.llu_rows
        else:
            llu_data = [self.lu_headings] + self.llu_rows

        for lu_data_row in llu_data:
            u_output += u'%s\n' % pu_sep.join(lu_data_row)

        return u_output

    def save_to_disk(self, pu_file=u'', pu_sep=u',', pu_com=u'#'):
        """
        Function to save a ParsedCsvFile from disk.
        :param pu_file:
        :param pu_sep:
        :param pu_com:
        :return:
        """
        u_data = self.to_plain_unicode(pu_sep, pu_com)
        o_file = codecs.open(pu_file, 'w', 'utf8')
        o_file.write(u_data)
        o_file.close()

    def process_column(self, pi_column, pu_method):
        """
        Method to process a column of the csv and return the resulting value.
        :param pi_column: Number of the column. The first column is 0.
        :param pu_method: Process method. Valid methods are:
                            - min: minimum value in the column
                            - max: maximum value in the column
                            - avg: average value of the column
                            - std: standard deviation of the column
                            - sum: sum of the whole column
        :return: integer when possible, but float in general.
        """
        # First we get all the values in the column.
        lf_values = []
        for lu_row in self.llu_rows:
            try:
                f_new_value = float(lu_row[pi_column])
                lf_values.append(f_new_value)
            except ValueError:
                pass

        f_result = None
        # Everything stored in a csv is text, so we have to convert it to a float beforehand
        if lf_values:
            if pu_method == u'max':
                f_result = max(lf_values)
            elif pu_method == u'min':
                f_result = min(lf_values)
            elif pu_method == u'avg':
                f_result = float(sum(lf_values)) / len(lf_values)
            elif pu_method == u'sum':
                f_result = sum(lf_values)
            # TODO: Finish this method

        return f_result


# Helper Functions
#=======================================================================================================================
def _line_clean(pu_line):
    """
    Function to remove new-line symbols from the right side of lines
    :param pu_line:
    :return:
    """

    lu_unwanted_chars = (u'\n', u'\r')

    u_clean_line = pu_line
    for u_unwanted_char in lu_unwanted_chars:
        u_clean_line = u_clean_line.rstrip(u_unwanted_char)

    return u_clean_line


def get_1st_row(pu_csv, pu_com=u'#', pu_sep=u';'):
    """
    Simple function to get the first row of data of a csv file.
    :param pu_csv:
    :param pu_com:
    :param pu_sep:
    :return:
    """
    lu_data = []
    with codecs.open(pu_csv, 'r', 'utf8') as o_file:
        for u_line in o_file:
            u_line = u_line.partition(pu_com)[0]
            u_line = u_line.strip()
            if u_line:
                lu_data = u_line.split(pu_sep)
                break

    return lu_data


def get_comments(pu_csv, pu_com=u'#'):
    """
    Function to get the comments from a csv reading just the first lines of the file.
    :param pu_csv:
    :param pu_com:
    :return:
    """
    lu_comments = []
    with codecs.open(pu_csv, mode='r', encoding='utf8') as o_file:
        for u_line in o_file:
            if u_line[0] == pu_com:
                u_raw_comment = u_line.partition(pu_com)[2]
                # When saving to file (or to text) a Csv file, a space is added between between the comment symbol
                # and the real comment, plus, a new line character is added to the end. So:
                u_clean_comment = u_raw_comment[1:].rstrip()
                lu_comments.append(u_clean_comment)
            else:
                break

    return lu_comments
