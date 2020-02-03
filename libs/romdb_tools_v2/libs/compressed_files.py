import datetime
import re

import cons
import hash
import shell


# Classes
#=======================================================================================================================
class _CompressedFile:
    def __init__(self):
        self.u_crc32 = u''
        self.u_name = u''
        self.i_real_size = 0
        self.i_comp_size = 0
        self.o_date = None

    def __str__(self):
        return unicode(self).encode('utf8')

    def __unicode__(self):
        u_output = u'<_CompressedFile>\n'
        u_output += u'  .u_name:      %s\n' % self.u_name
        u_output += u'  .u_crc32:     %s\n' % self.u_crc32
        u_output += u'  .i_comp_size: %i\n' % self.i_comp_size
        u_output += u'  .i_real_size: %i\n' % self.i_real_size
        return u_output

    def __nonzero__(self):
        """
        Method to generate the True/False check over the class instances.
        :return: True/False
        """
        b_value = False

        lx_values = (self.u_crc32, self.u_name, self.i_real_size, self.i_comp_size, self.o_date)

        for x_value in lx_values:
            if x_value:
                b_value = True
                break

        return b_value


class _RomSet:
    def __init__(self):
        self.lo_romfiles = []
        self.u_platform = None

    def __str__(self):
        return unicode(self).encode('utf8')

    def __unicode__(self):
        u_out = u'<_RomSet>\n'
        u_out += u'  .u_platform:  %s\n' % self.u_platform
        u_out += u'  .u_ccrc32:    %s\n' % self.u_ccrc32
        u_out += u'  .u_dcrc32:    %s\n' % self.u_dcrc32
        u_out += u'  .lo_romfiles: (%i)\n' % len(self.lo_romfiles)

        for o_romfile in self.lo_romfiles:
            u_out += u'                %s %i %s\n' % (o_romfile.u_crc32, o_romfile.i_size, o_romfile.u_file)

        return u_out

    def add_rom(self, po_rom):
        """
        Method to add a new romfile
        :param po_rom:
        :return: Nothing
        """

        self.lo_romfiles.append(po_rom)

    def _get_size(self):
        i_size = 0
        for o_romfile in self.lo_romfiles:
            i_size += o_romfile.i_size

        return i_size

    def _get_ccrc32(self):
        return self._get_crc32(pb_clean=True)

    def _get_dcrc32(self):
        return self._get_crc32(pb_clean=False)

    def _get_crc32(self, pb_clean=True):
        i_crc32 = 0
        for o_romfile in self.lo_romfiles:
            if pb_clean and (o_romfile.u_ext not in cons.tu_IGNORE_EXTENSIONS):
                i_crc32 += o_romfile.i_crc32
            elif not pb_clean:
                i_crc32 += o_romfile.i_crc32

        return hash.unicode_crc32(i_crc32)

    u_ccrc32 = property(fget=_get_ccrc32, fset=None)
    u_dcrc32 = property(fget=_get_dcrc32, fset=None)


class _Rom(object):
    def __init__(self):
        self.u_file = u''
        self.i_crc32 = 0
        self.i_size = 0

    def __str__(self):
        return unicode(self).encode('utf8')

    def __unicode__(self):
        u_out = u'<_Rom>\n'
        u_out += u'  .u_file:  %s\n' % self.u_file
        u_out += u'  .u_name:  %s\n' % self.u_name
        u_out += u'  .u_ext:   %s\n' % self.u_ext
        u_out += u'  .i_size:  %i\n' % self.i_size
        u_out += u'  .i_crc32: %s\n' % self.i_crc32
        u_out += u'  .u_crc32: %s\n' % self.u_crc32
        return u_out

    def _get_crc32(self):
        return hash.unicode_crc32(self.i_crc32)

    def _get_name(self):
        return self.u_file.rpartition(u'.')[0]

    def _get_ext(self):
        return self.u_file.rpartition(u'.')[2]

    u_crc32 = property(fget=_get_crc32, fset=None)
    u_name = property(fget=_get_name, fset=None)
    u_ext = property(fget=_get_ext, fset=None)


# 7z Functions
#=======================================================================================================================
def scan_7z_file(pu_file):
    """
    Function that build the ROMset found in the 7z file

    :param pu_file:
    :return:
    """

    # Obtaining ROMset data from content of 7z file
    #----------------------------------------------
    # Since 7z support is quite limited from python (so the required code would be big and messy), I simply parse the
    # output data from the 7z command line tool.
    lo_7z_files = _parse_7z_cli_output(pu_file)

    o_romset = _RomSet()
    for o_file in lo_7z_files:
        o_rom = _Rom()
        o_rom.u_file = o_file.u_name
        o_rom.i_crc32 = int(o_file.u_crc32, 16)
        o_rom.i_size = o_file.i_real_size

        o_romset.add_rom(o_rom)

    return o_romset


def _parse_7z_cli_output(pu_file):
    """
    Function to parse the information output of 7z about the contents of a compressed file.
    :param pu_file:
    :return:
    """

    # The current support for 7z files in python is very limited at the moment, so I get the content
    # of the file by using the command line tool for 7z and then I pare its output.
    u_cmd = u'7z l -slt "%s"' % pu_file
    o_cmd = shell.Command(u_cmd)
    o_cmd.execute()

    # Files data will come after a line with "----------" and there is an empty line between the information of two
    # files
    u_elements_data = o_cmd.u_stdout.partition(u'----------')[2]

    lu_elements_data = u_elements_data.split(u'\n\n')

    lo_files = []
    for u_elem_data in lu_elements_data:
        o_file = _parse_7z_cli_file_chunk(u_elem_data)
        if o_file:
            lo_files.append(o_file)

    return lo_files


def _parse_7z_cli_file_chunk(pu_chunk):
    """
    Function to parse the chunk of text of 7z about a particular file.

    Example chunk:

        Path = MediEvil (Spain) (Track 2).bin
        Size = 32989152
        Packed Size = 4724
        Modified = 2015-05-26 14:39:08
        Attributes = ....A
        CRC = B97FFD28
        Encrypted = -
        Method = LZMA:25
        Block = 0

    :param pu_chunk:
    :return:
    """

    lu_lines = pu_chunk.splitlines()

    o_file = _CompressedFile()

    for u_line in lu_lines:
        if u_line.startswith(u'Path ='):
            o_file.u_name = u_line.partition(u'=')[2].strip()

        elif u_line.startswith(u'Size ='):
            o_file.i_real_size = int(u_line.partition(u'=')[2])
        elif u_line.startswith(u'Packed Size ='):
            # Apparently, using maximum compression, 7z doesn't inform you abut the uncompressed size of the file.
            try:
                o_file.i_comp_size = int(u_line.partition(u'=')[2])
            except ValueError:
                o_file.i_comp_size = 0

        elif u_line.startswith(u'CRC ='):
            o_file.u_crc32 = u_line.partition(u'=')[2].strip().lower()

    return o_file


# zip Functions
#=======================================================================================================================
def scan_zip_file(pu_file):
    lo_zip_files = _parse_zip_cli_output(pu_file)

    o_romset = _RomSet()
    for o_file in lo_zip_files:
        o_rom = _Rom()
        o_rom.u_file = o_file.u_name
        o_rom.i_crc32 = int(o_file.u_crc32, 16)
        o_rom.i_size = o_file.i_real_size

        o_romset.add_rom(o_rom)

    return o_romset


def _parse_zip_cli_output(pu_file):
    u_cmd = u'unzip -v "%s"' % pu_file
    o_cmd = shell.Command(u_cmd)
    o_cmd.execute()

    # Command output is something like
    #
    #   Archive:  snt_Actraiser (Japan).zip
    #   TORRENTZIPPED-48567FAD
    #    Length   Method    Size  Cmpr    Date    Time   CRC-32   Name
    #   --------  ------  ------- ---- ---------- ----- --------  ----
    #    1048576  Defl:X   677852  35% 1996-12-24 23:32 bee9b30c  Actraiser (Japan).sfc
    #   --------          -------  ---                            -------
    #    1048576           677852  35%                            1 file

    lu_lines = o_cmd.u_stdout.splitlines()[4:-2]

    lo_files = []
    for u_line in lu_lines:
        o_compressed_file = _parse_zip_cli_line(u_line)
        if o_compressed_file is not None:
            lo_files.append(o_compressed_file)

    return lo_files


def _parse_zip_cli_line(pu_line):

    # For each word we also get the real position inside the original string (we will se later why)
    ltu_pos_word = []
    for o_match in re.finditer(r'\S+', pu_line):
        i_pos, u_word = o_match.start(), o_match.group()
        ltu_pos_word.append((i_pos, u_word))

    o_file = _CompressedFile()
    o_file.i_real_size = int(ltu_pos_word[0][1])
    o_file.i_comp_size = int(ltu_pos_word[2][1])
    o_file.o_date = datetime.datetime.strptime(u'%s %s' % (ltu_pos_word[4][1], ltu_pos_word[5][1]), u'%Y-%m-%d %H:%M')
    o_file.u_crc32 = ltu_pos_word[6][1]

    # Because file names can contain more than one space, we need to do a manual cut of the name
    o_file.u_name = pu_line[ltu_pos_word[7][0]:]

    # Directory names finish with a slash.
    if o_file.u_name.endswith(u'/'):
        o_file = None

    return o_file
