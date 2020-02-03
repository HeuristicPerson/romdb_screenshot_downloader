# -*- coding: utf-8 -*-

"""
Library to load data from .dat files (ClrMamePro and XML format only) for ROMsets.

--- This library is part of the "hqtools" package. Never modify it outside it. ---
"""

import codecs
import xml.etree.cElementTree
import os
import re

import csv
import files


# Constants
#=======================================================================================================================
# Library version
_u_VERSION = u'2019-10-14'

# List of ROM extensions to ignore when obtaining "clean" values (size, and hashes)
_tu_IGNORE_EXTS = (u'cue',)


# Classes
#=======================================================================================================================
class Filter:
    """
    Class to store information about a filter that will be applied later to RomSetContainer.
    """

    def __init__(self, u_attribute, u_method, *x_values):
        self.u_attribute = u_attribute
        self.u_method = u_method
        self.lx_values = x_values

        for x_value in x_values:
            if not isinstance(x_value, (unicode, str, int, float)):
                raise Exception('ERROR, type "%s" is not valid value for a filter' % type(x_value))

        # TODO: Check for valid values for u_method. So far 'equals' is the only one implemented.
        # TODO: Create a check for x_values to avoid the case when you create a wrong filter with a tuple (123, 145)

    def __str__(self):
        u_output = u''
        u_output += u'[Filter]\n'
        u_output += u'u_attribute: %s\n' % self.u_attribute
        u_output += u'   u_method: %s\n' % self.u_method
        u_output += u'  lx_values: %s\n' % str(self.lx_values)

        return u_output.encode('utf8', 'strict')


class Field:
    """
    Class to store configuration data for CSV import method for RomSetContainer.
    """
    def __init__(self, pi_src_column, ps_dst_field):
        self.i_src_column = pi_src_column
        self.s_dst_field = ps_dst_field


class RomSetContainer(object):
    """
    Class to store a list of games, each game can contain different ROM files data. The information can be read/write to
    disk ROM file objects.
    """

    def __init__(self, u_file=None):

        # TODO: RomSetContainer should contain an internal registry with all the manipulations suffered by the object so
        #       when you export the file to disk you know the information is not coming directly from the RAW dat file.
        # I think that some "MODIFIED" flags would be enough like .db_flags{'added_sets': True, 'removed_sets': True...}

        # Variable definition
        self._i_position = None   # RomSet position for the iterator

        self.u_name = u''         # internal name of the dat file.
        self.u_description = u''  # description of the dat file.
        self.u_version = u''      # version of the dat file (usually a date).
        self.u_comment = u''      # extra comment for the dat file.
        self.u_type = u''         # type of DAT file the data comes from.
        self.u_author = u''       # Author of the dat.
        self.u_homepage = u''     # Homepage of the author of the DAT.

        self.lo_romsets = []      # list of game objects inside the dat file

        self._db_flags = {'from_dat': False,
                          'sets_added': False,
                          'sets_deleted': False,
                          'data_imported': False}       # Modification flags

        self._tu_valid_search_fields = ('_i_year',
                                        'u_ccrc32', 'u_dcrc32',
                                        'u_cmd5', 'u_dmd5',
                                        'u_csha1', 'u_dsha1',
                                        'u_desc', 'u_name', 'u_auth')

        if u_file:
            self.read_from_dat(u_file)

    def __str__(self):
        return str(unicode(self))

    def __unicode__(self):
        u_output = u''
        u_output += u'<RomSetContainer>\n'
        u_output += u'  ._db_flags:  %s\n' % str(self._db_flags)
        u_output += u'  .u_name:     %s\n' % self.u_name
        u_output += u'  .u_desc:     %s\n' % self.u_description
        u_output += u'  .u_version:  %s\n' % self.u_version
        u_output += u'  .u_homepage: %s\n' % self.u_homepage
        u_output += u'  .u_comment:  %s\n' % self.u_comment
        u_output += u'  .u_type:     %s\n' % self.u_type
        u_output += u'  .u_author:   %s\n' % self.u_author
        u_output += u'  .i_romsets:  %i\n' % self.i_romsets
        u_output += u'  .i_bads:     %i\n' % self.i_bads

        return u_output

    def __iter__(self):
        if self.i_romsets > 0:
            self._i_position = 0

            # If the list is not sorted, it's sorted before iterating over it.
            self._sort()

        return self

    def __len__(self):
        return self.i_romsets

    def next(self):
        """

        :type :return RomSet
        """
        if (self._i_position is not None) and (self._i_position < self.i_romsets):
            self._i_position += 1
            return self.lo_romsets[self._i_position - 1]
        else:
            raise StopIteration()

    def add_romset(self, o_romset):
        """
        Internal method to add games to the container WITHOUT any kind of duplicity or other kind of check.

        :param o_romset:
        """

        self.lo_romsets.append(o_romset)

    def del_romset(self, pu_field, px_check_value):
        """
        Method to remove a ROMset from the container. The method does not perform any kind of uniqueness check.
        :param pu_field:
        :param px_check_value:
        :return:
        """

        lo_keep_romsets = []
        for o_romset in self.lo_romsets:
            x_romset_value = getattr(o_romset, pu_field)
            if x_romset_value != px_check_value:
                lo_keep_romsets.append(o_romset)

        i_deleted = len(self.lo_romsets) - len(lo_keep_romsets)
        self.lo_romsets = lo_keep_romsets

        return i_deleted

    def get_duplicated_crc32(self):
        """
        Method to return ROMsets with duplicated CRC32
        :return: a list of ROMsets
        """

        # [1/3] We count how many times each CRC32 appears in the RomSetContainer
        #------------------------------------------------------------------------
        di_romsets = {}
        for o_romset in self:
            u_ccrc32 = o_romset.u_ccrc32
            if u_ccrc32 not in di_romsets:
                di_romsets[u_ccrc32] = 1
            else:
                di_romsets[u_ccrc32] += 1

        # [2/3] Then we keep only those that appear more than once
        #---------------------------------------------------------
        lu_repeated_ccrc32 = []
        for u_ccrc32, i_times in di_romsets.iteritems():
            if i_times > 1:
                lu_repeated_ccrc32.append(u_ccrc32)

        # [3/3] For each repeated CRC32, we get all the ROMsets with that CRC32
        #----------------------------------------------------------------------
        do_romset_collisions = {}
        for u_ccrc32 in lu_repeated_ccrc32:
            do_romset_collisions[u_ccrc32] = self.get_romsets_by_field(u'u_ccrc32', False, u_ccrc32)

        return do_romset_collisions

    def _show_duplicates(self):
        """
        Method to quick show duplicates so you can fix the problems using other tools or manually.

        WARNING! This method can be really slow.

        :return: A list of lists.
        """

        dlu_duplicated_romsets = {}

        for o_romset in self:
            if o_romset.u_dmd5 not in dlu_duplicated_romsets:
                dlu_duplicated_romsets[o_romset.u_dmd5] = []

            dlu_duplicated_romsets[o_romset.u_dmd5].append(o_romset.u_name)

        # Since for an A-B duplicate we check the duplicity two times A vs B, B vs A, the lists of duplicates are
        # doubled and have to be made unique.
        dlu_clean_duplicated_romsets = {}
        for u_key, lu_values in dlu_duplicated_romsets.iteritems():
            if len(lu_values) > 1:
                dlu_clean_duplicated_romsets[u_key] = set(lu_values)

        return dlu_clean_duplicated_romsets

    def empty(self):
        """
        Method to clean all the games of the container but keeping the meta-data.

        :return: Nothing
        """
        self.lo_romsets = []

    def copy_metadata_from(self, po_game_container):
        """
        Method to copy meta-data information (everything but the list of games itself and the number of games) from
        other RomSetContainer object.

        :param po_game_container: External RomSetContainer object.
        """

        # Modification of data
        self.u_name = po_game_container.u_name
        self.u_description = po_game_container.u_description
        self.u_version = po_game_container.u_version
        self.u_homepage = po_game_container.u_homepage
        self.u_comment = po_game_container.u_comment
        self.u_type = po_game_container.u_type
        self.u_author = po_game_container.u_author

        u_log_message = u''
        u_log_message += u'Metadata copied: '
        u_log_message += u'u_name="%s" ' % self.u_name
        u_log_message += u'u_desc="%s" ' % self.u_description
        u_log_message += u'u_version="%s" ' % self.u_version
        u_log_message += u'u_comment="%s" ' % self.u_comment
        u_log_message += u'u_type="%s" ' % self.u_type
        u_log_message += u'u_author="%s" ' % self.u_author

    def filter(self, o_filter):
        """
        Method to filter in/out games depending on a field name and allowed/disallowed values for that field.

        :param o_filter: Filter object.
        :type o_filter Filter

        :return: A list of games that match or don't match your filter criteria.
        """

        # Two RomSetContainer objects are created to store the games that matched the filter and the games that didn't
        # matched it.
        o_matched_container = RomSetContainer()
        o_matched_container.copy_metadata_from(self)
        #o_matched_container.modify_metadata(u'FILTER(', u')')
        o_unmatched_container = RomSetContainer()
        o_unmatched_container.copy_metadata_from(self)

        for o_game in self:

            # The first thing to do is (to try) to obtain o_dat_game.<u_attribute>
            try:
                x_value = getattr(o_game, o_filter.u_attribute)

            except AttributeError:
                raise Exception('ERROR: You are trying to access the unknown attribute "%s"' % o_filter.u_attribute)

            # Then we can filter. Since we are filtering already unique games present in our container, we don't need
            # to perform any uniqueness test while adding the games to the matched/unmatched containers. So, we use the
            # method add_romset which doesn't perform that test and is much faster than the equivalent one with test
            # add_romset.
            if o_filter.u_method == 'equals':
                if x_value in o_filter.lx_values:
                    o_matched_container.add_romset(o_game)

                else:
                    o_unmatched_container.add_romset(o_game)

        return o_matched_container, o_unmatched_container

    def get_romsets_by_field(self, pu_field, pb_first=False, ptx_search_values=()):
        """
        Method to get a list of MULTIPLE GAMES with certain content in a field.

        :param pu_field: Name of the field to use for the matching. i.e. '_i_year'
        :type pu_field unicode

        :param pb_first: Whether the function will just return the first result or all of them.
        :type pb_first bool

        :param px_search_values: Content of the field to search for. i.e. 1985, 1986

        :return: A list with the found romsets.
        """

        # This search function doesn't correctly if the search field is text and the ptx_search_values is incorrectly
        # given as a string. Notice below that the "search" is done with an "in". So, so AAA would match AA. For that
        # reason I check the type of the parameter.
        if not isinstance(ptx_search_values, tuple):
            raise ValueError('ERROR: ptx_search_values must be a tuple. %s given instead' % type(ptx_search_values))

        lo_romsets = []

        if pu_field not in self._tu_valid_search_fields:
            raise ValueError('Error: pu_field must be one of %s' % str(self._tu_valid_search_fields))

        else:
            for o_romset in self:
                if getattr(o_romset, pu_field) in ptx_search_values:
                    lo_romsets.append(o_romset)
                    if pb_first:
                        break

        return lo_romsets

    def read_from_dat(self, pu_file):
        """
        Method to load Dat data from a file on disk.

        :param pu_file: File containing the data. i.e. '/home/john/mame.dat'

        :return: Nothing.
        """

        # If the file is not present, we raise an error
        if not os.path.isfile(pu_file):
            raise ValueError('Can\'t find dat file "%s"' % pu_file)

        o_file = codecs.open(pu_file, u'rb', u'utf8', u'ignore')

        # We try to automatically identify it reading the beginning of the file.
        u_first_line = o_file.readline()
        o_file.close()

        # Identifying ClrMamePro mode
        if (u_first_line.find(u'clrmamepro') != -1) or (u_first_line.find(u'emulator') != -1):
            u_format = 'cmp'

        # Identifying Xml mode
        elif u_first_line.find(u'<?xml') != -1:
            u_format = 'xml'

        # Unknown format error raise
        else:
            raise IOError('Unknown DAT format')

        # Loading the file using the different readers depending on the format parameter
        if u_format == 'cmp':
            self._read_from_cmp(pu_file)
        elif u_format == 'xml':
            self._read_from_xml(pu_file)

        # After loading the games from disk, the list is sorted
        self._sort()

        # We alter the proper flag
        self._db_flags['from_dat'] = True

    def to_dict(self, ps_property):
        """
        Method to return a dictionary with all the romsets keyed by the desired property "ps_property". No checks will
        be performed so if the values of ps_property are not unique for all the RomSets, the later occurrences will
        overwrite the older ones.
        :param pu_field:
        :return:
        """
        do_output = {}
        for o_romset in self.lo_romsets:
            do_output[getattr(o_romset, ps_property)] = o_romset

        return do_output

    def _read_from_cmp(self, u_file):
        """
        Method to process ClrMamePro DATs.
        """
        self.u_type = u'ClrMamePro'

        o_file = codecs.open(u_file, 'rb', 'utf8', 'ignore')

        b_head_mode = False
        b_game_mode = False

        ls_head_strings = []    # List that will contain the multiple lines with data from the heading.
        lu_game_strings = []    # List that will contain the multiple lines with data for a game.

        for u_line in o_file:

            # Detection of the start of the heading of the file
            if (u_line.find(u'clrmamepro (') == 0) or (u_line.find('emulator (') == 0):
                b_head_mode = True
                continue

            # If we are in "head-mode" and the first character of the line is ")", it means we have reached the end of
            # the heading (so we have all its lines) and we can parse them.
            if b_head_mode and u_line.find(')') == 0:
                self.u_name = _dat_vertical_parse(ls_head_strings, 'name').decode('utf8')
                self.u_description = _dat_vertical_parse(ls_head_strings, 'description').decode('utf8')
                self.u_version = _dat_vertical_parse(ls_head_strings, 'version').decode('utf8')
                self.u_comment = _dat_vertical_parse(ls_head_strings, 'comment').decode('utf8')

                ls_head_strings = []
                b_head_mode = False
                continue

            # If we are in "head-mode", we add the found lines to a list that will be parsed later" (look the code just
            # above).
            if b_head_mode:
                ls_head_strings.append(u_line)
                continue

            # RomSet data
            if u_line.find('game (') == 0:
                b_game_mode = True
                continue

            if b_game_mode and u_line.find(')') == 0:
                u_romset_name = _dat_vertical_parse(lu_game_strings, 'name')
                u_romset_description = _dat_vertical_parse(lu_game_strings, 'description')
                u_romset_author = _dat_vertical_parse(lu_game_strings, 'manufacturer')
                u_game_year = _dat_vertical_parse(lu_game_strings, 'year')
                if u_game_year == u'':
                    u_game_year = u'0'

                lu_game_roms = _dat_vertical_parse(lu_game_strings, 'rom', 'multi')

                o_dat_romset = RomSet(u_romset_name, u_romset_description)
                o_dat_romset.u_year = u_game_year
                o_dat_romset.u_auth = u_romset_author

                for s_game_rom in lu_game_roms:
                    # sometimes name has quotes " around and sometimes not, so it's safer to use size as end.
                    u_rom_name = _dat_horizontal_parse(s_game_rom, 'name ', 'size')

                    u_rom_size = _dat_horizontal_parse(s_game_rom, 'size ', ' ')
                    u_rom_crc = _dat_horizontal_parse(s_game_rom, 'crc ', ' ')
                    u_rom_md5 = _dat_horizontal_parse(s_game_rom, 'md5 ', ' ')
                    u_rom_sha1 = _dat_horizontal_parse(s_game_rom, 'sha1 ', ' ')

                    # So far, MAME is the only dat providing flags, and it's only one.
                    u_rom_flags = _dat_horizontal_parse(s_game_rom, 'flags ', ' ')
                    b_bad = False
                    if u_rom_flags in ('baddump', 'nodump'):
                        b_bad = True

                    # create a rom object
                    o_rom = Rom()
                    o_rom.b_bad = b_bad
                    o_rom.u_name = u_rom_name
                    o_rom.i_size = int(u_rom_size)
                    o_rom.u_crc32 = u_rom_crc.lower()
                    o_rom.u_md5 = u_rom_md5.lower()
                    o_rom.u_sha1 = u_rom_sha1.lower()

                    # add the rom object to the list
                    o_dat_romset.add_rom(o_rom)

                # We add the game to the container without any kind of check, we will do it later.
                self.add_romset(o_dat_romset)

                lu_game_strings = []
                b_game_mode = False
                continue

            # RomSet mode actions
            if b_game_mode:
                lu_game_strings.append(u_line)
                pass

    def _read_from_xml(self, u_file):
        self.u_type = u'XML'

        o_xml_tree = xml.etree.cElementTree.parse(u_file)
        o_xml_root = o_xml_tree.getroot()

        # Header information
        #-------------------
        o_header = o_xml_root.find('header')
        self.u_name = o_header.find('name').text
        self.u_description = o_header.find('description').text
        self.u_version = o_header.find('version').text

        o_xelem_homepage = o_header.find('homepage')
        if o_xelem_homepage:
            self.u_homepage = o_xelem_homepage.text

        if o_header.find('author'):
            self.u_author = o_header.find('author').text
        else:
            self.u_author = u'None'

        # RomSet information
        for o_xelem_game in o_xml_root.findall('game'):
            u_game_name = o_xelem_game.attrib['name']
            u_game_description = o_xelem_game.find('description').text

            o_dat_game = RomSet(u_game_name, u_game_description)

            for o_xelem_rom in o_xelem_game.findall('rom'):
                    o_rom = Rom()
                    try:
                        o_rom.u_name = o_xelem_rom.attrib['name']
                    except KeyError:
                        pass

                    try:
                        o_rom.i_size = int(o_xelem_rom.attrib['size'])
                    except KeyError:
                        o_rom.b_bad = True

                    try:
                        o_rom.u_crc32 = o_xelem_rom.attrib['crc'].lower()
                    except KeyError:
                        o_rom.b_bad = True

                    try:
                        o_rom.u_md5 = o_xelem_rom.attrib['md5'].lower()
                    except KeyError:
                        o_rom.u_md5 = None

                    try:
                        o_rom.u_sha1 = o_xelem_rom.attrib['sha1'].lower()
                    except KeyError:
                        o_rom.u_sha1 = None

                    # MAME XML (AFAIK) includes a status field which can contain "baddump" and "nodump"
                    try:
                        u_status = o_xelem_rom.attrib['status'].lower()
                        if u_status in ('baddump', 'nodump'):
                            o_rom.b_bad = True
                    except KeyError:
                        pass

                    # Adding the rom object to the list
                    o_dat_game.lo_roms.append(o_rom)

            self.add_romset(o_dat_game)

    def _sort(self):
        # Sorting of the list based on the game description (which is more reliable than the short name of the game)
        self.lo_romsets.sort(key=lambda o_game: o_game.u_desc.encode('utf8', 'strict'), reverse=False)

    def _get_i_bads(self):
        i_bads = 0
        for o_romset in self:
            if o_romset.b_bad:
                i_bads += 1
        return i_bads

    def _get_i_romsets(self):
        return len(self.lo_romsets)

    i_bads = property(fget=_get_i_bads, fset=None)
    i_romsets = property(fget=_get_i_romsets, fset=None)


class RomSet(object):
    """
    Class to store information about a RomSet.
    """
    def __init__(self, pu_name, pu_description):
        # Properties: Basic ones
        self.u_name = pu_name         # Usually, the file name for the game. MAME uses a short 8 char or less name here.
        self.u_desc = pu_description  # Usually, the full and long name of the game i.e. 'Super Mario World (Europe)'.

        # Properties: The rest
        self.lo_roms = []             # List containing all the ROM information objects.
        self.u_auth = u''             # Author, company that programmed the game (MAME dat support only, AFAIK).

        # Properties: iterator
        self._i_pos = None

    def __iter__(self):
        if len(self.lo_roms) > 0:
            self._i_pos = 0

        return self

    def __str__(self):
        return str(unicode(self))

    def __unicode__(self):
        u_output = u''
        u_output += u'<RomSet>\n'
        u_output += u'  .b_bad:    %s\n' % self.b_bad
        u_output += u'  .u_ccrc32: %s\n' % self.u_ccrc32
        u_output += u'  .u_cmd5:   %s\n' % self.u_cmd5
        u_output += u'  .u_csha1:  %s\n' % self.u_csha1
        u_output += u'  .i_csize:  %s\n' % self.i_csize
        u_output += u'  .u_dcrc32: %s\n' % self.u_dcrc32
        u_output += u'  .u_desc:   %s\n' % self.u_desc
        u_output += u'  .u_dmd5:   %s\n' % self.u_dmd5
        u_output += u'  .u_dsha1:  %s\n' % self.u_dsha1
        u_output += u'  .u_dsize:  %s\n' % self.i_dsize
        u_output += u'  .u_auth:   %s\n' % self.u_auth
        u_output += u'  .u_name:   %s\n' % self.u_name
        u_output += u'  .lo_roms:\n'

        for i_rom, o_rom in enumerate(self):
            u_rom_text = str(o_rom).decode('utf8')

            # Modification of u_rom_text to show the rom number
            u_rom_text = u_rom_text.replace(u'<Rom>', u'<Rom> #%i' % (i_rom + 1))

            lu_rom_raw_lines = u_rom_text.splitlines()
            lu_rom_clean_lines = []

            for u_line in lu_rom_raw_lines:
                u_extra_spaces = u' ' * 13
                lu_rom_clean_lines.append('%s%s' % (u_extra_spaces, u_line))

            u_output += u'%s\n\n' % (u'\n'.join(lu_rom_clean_lines))

        return u_output.encode('utf8')

    def add_rom(self, po_rom):
        """
        Method to add a ROM
        :param po_rom:
        :return:
        """
        self.lo_roms.append(po_rom)

    def next(self):
        """
        :type :return Rom
        """
        if (self._i_pos is not None) and (self._i_pos < len(self.lo_roms)):
            self._i_pos += 1
            return self.lo_roms[self._i_pos - 1]
        else:
            raise StopIteration()

    def _get_hash(self, pu_type='crc32', pb_clean=False):
        """
        Method to obtain the COMPOUND hash of the game. It means the hash of *all* the ROMs included in the game will be
        summed. For example, if the game contains two ROMs:

            - RomSet A
                - ROM a1: CRC32 = 01020304
                - ROM a2: CRC32 = 0a0b0c0d

        The output of this function will be 01020304 + 0a0b0c0d (remember that hash values are hex representations of
        numbers).

        Two comments about the behavior of the function:

            1. Different hashing methods are used: crc32, md5, sha1

            #TODO: Explain pb_clean parameter

            2. Only *relevant* ROMs are considered. For example, meta-data information is typically included in the form
               of .cue files for optical disc images. That information is not really included in the original media and
               its content would modify the hash result of the real data. Imagine two .cue files containing:

                   Track 1: Street Fighter.bin

                   Track 1: Street fighter.bin

               Although the content of the .bin file is the same, the .cue files are different (notice the
               capital-lowercase initial of "fighter"). In consequence, the hash of the .cue file is different and the
               global hash of the whole game will be different. SO, TO AVOID THIS ISSUE, .CUE FILES AND OTHER META-DATA
               FILES ARE NOT CONSIDERED WHEN CALCULATING THE HASH OF THE GAME.

        :return: A keyed dictionary with 'crc32', 'md5', and 'sha1' hashes in hex-string format
        """

        # The first step is to create a list with the real ROMs, avoiding meta-data ones like .cue files
        lo_relevant_roms = []

        for o_rom in self.lo_roms:
            o_rom_fp = files.FilePath(o_rom.u_name)

            # If discard is not activated, every ROM will be considered
            if not pb_clean:
                lo_relevant_roms.append(o_rom)

            # In other case, ROMs are filtered based on the file extension
            else:
                if not o_rom_fp.has_exts(*_tu_IGNORE_EXTS):
                    lo_relevant_roms.append(o_rom)

        # Calculation ROMset "compound" hash (which is the sum of all the relevant ROMs hashes
        #-------------------------------------------------------------------------------------
        lu_hexs = []
        for o_rom in lo_relevant_roms:

            if pu_type == 'crc32':
                lu_hexs.append(o_rom.u_crc32)
            elif pu_type == 'md5':
                lu_hexs.append(o_rom.u_md5)
            elif pu_type == 'sha1':
                lu_hexs.append(o_rom.u_sha1)
            else:
                raise Exception('Invalid hash type "%s"' % pu_type)

        u_hash = _compound_hash(lu_hexs)

        # Setting the proper length for each type of hash: crc32 = 8 chars, md5 = 32 chars, sha1 = 40 chars
        #--------------------------------------------------------------------------------------------------
        if u_hash:
            i_hash_length = 0
            if pu_type == 'crc32':
                i_hash_length = 8
            elif pu_type == 'md5':
                i_hash_length = 32
            elif pu_type == 'sha1':
                i_hash_length = 40

            u_hash = u_hash[-i_hash_length:]
            u_hash = u_hash.rjust(i_hash_length, u'0')

        else:
            pass

        return u_hash

    def _get_size(self, pb_clean=False):
        """
        Method to get the size of a romset taking into account all the files (dirty mode) or just relevant files (clean
        mode).

        :param pb_clean: True for clean mode, False for dirty mode
        """
        lo_relevant_roms = []
        i_global_size = 0

        for o_rom in self.lo_roms:
            # If discard is not activated, every ROM will be considered
            if not pb_clean:
                lo_relevant_roms.append(o_rom)

            # In other case, ROMs are filtered based on the file extension
            else:
                if u'.' in o_rom.u_name:
                    u_ext = o_rom.u_name.rpartition('.')[2].lower()

                    if u_ext not in _tu_IGNORE_EXTS:
                        lo_relevant_roms.append(o_rom)

        for o_rom in lo_relevant_roms:
            i_global_size += o_rom.i_size

        return i_global_size

    # Properties with a bit of code behind
    def _get_bad(self):
        """
        Method to indicate if the ROMset contains any bad ROM (either a bad-dump or a no-dump, MAME dat is the only one
        that I know containing this information.
        :return:
        """
        b_bad = False
        for o_rom in self:
            if o_rom.b_bad:
                b_bad = True
                break
        return b_bad

    def _get_ccrc32(self):
        return self._get_hash(pu_type='crc32', pb_clean=True)

    def _get_dcrc32(self):
        return self._get_hash(pu_type='crc32', pb_clean=False)

    def _get_cmd5(self):
        return self._get_hash(pu_type='md5', pb_clean=True)

    def _get_dmd5(self):
        return self._get_hash(pu_type='md5', pb_clean=False)

    def _get_csha1(self):
        return self._get_hash(pu_type='sha1', pb_clean=True)

    def _get_dsha1(self):
        return self._get_hash(pu_type='sha1', pb_clean=False)

    def _get_csize(self):
        return self._get_size(pb_clean=True)

    def _get_dsize(self):
        return self._get_size(pb_clean=False)

    b_bad = property(fget=_get_bad, fset=None)
    u_ccrc32 = property(fget=_get_ccrc32, fset=None)
    u_dcrc32 = property(fget=_get_dcrc32, fset=None)
    u_cmd5 = property(fget=_get_cmd5, fset=None)
    u_dmd5 = property(fget=_get_dmd5, fset=None)
    u_csha1 = property(fget=_get_csha1, fset=None)
    u_dsha1 = property(fget=_get_dsha1, fset=None)
    i_csize = property(fget=_get_csize, fset=None)
    i_dsize = property(fget=_get_dsize, fset=None)


class Rom:
    """
    Class to store all the information for a ROM file contained in a DAT file. Typically that information is the name
    of the ROM, the description, CRC-MD5-SHA1 check-sums...
    """

    def __init__(self):
        # Variable definition
        self.b_bad = False  # Indication that it's a no-dump or a bad-dump. (So far MAME is the only one to indicate it)
        self.u_name = u''   # name of the ROM. i.e. 'Super Mario World.sfc'
        self.u_crc32 = u''  # crc32 checksum of the file data i.e. 'a209fe80'
        self.u_md5 = u''    # md5 checksum of the file data
        self.u_sha1 = u''   # sha1 checksum of the file data
        self.i_size = 0     # file size in bytes

        # Variable population

    def __str__(self):
        u_output = u''
        u_output += u'<Rom>\n'
        u_output += u'  .b_bad:    %s\n' % self.b_bad
        u_output += u'  .i_size:   %i\n' % self.i_size
        u_output += u'  .u_crc32:  %s\n' % self.u_crc32
        u_output += u'  .u_md5:    %s\n' % self.u_md5
        u_output += u'  .u_name:   %s\n' % self.u_name
        u_output += u'  .u_sha1:   %s\n' % self.u_sha1

        return u_output.encode('utf8')


# Functions
#=======================================================================================================================
# TODO: This function doesn't belong here. It should be in another library called rom_tools or something like that.
def get_rom_header(pu_rom_file):
    """
    Function to return the year(s) found in a rom file.

    Only the first bytes of the ROM are scanned and only years 19xx and 20xx are searched for.

    :param pu_rom_file: Name of the file to search in.

    :return: A list with the found years as integers.
    """

    i_bytes = 2048
    i_min_year = 1970
    i_max_year = 2020

    li_years = []
    li_years_clean = []

    o_file = open(pu_rom_file, mode='rb')
    s_data_chunk = o_file.read(i_bytes)
    o_file.close()

    o_match = re.search(r'(\d{4})', s_data_chunk)

    if o_match:
        for s_year in o_match.groups():
            li_years.append(int(s_year))

    for i_year in li_years:
        if i_min_year <= i_year <= i_max_year:
            li_years_clean.append(i_year)

    return li_years_clean


# Helper Functions
#=======================================================================================================================
def _dat_vertical_parse(ls_lines, s_section, s_mode='single'):
    """Function to parse a group of lines which contains different information about the same item.

    So, the information follows a pattern similar to:

        field_1 data_a
        field_1 data_b
        field_2 data_c
        ...

        ls_lines: a list containing the individual lines as strings.

        s_section: name of the section (in the above example s_section = field_1, for example).

        s_mode: 'single', each field exists once and the function returns its data as a string.
                'multi', each field exists several times and the function returns its data as a list of strings.

        @rtype : string or list of strings
    """

    ls_data = []
    s_data = ''

    # Adding a space to the section because it has to exist a space between the section and the data.
    s_section += ' '

    for s_line in ls_lines:
        s_line = s_line.strip()

        if s_line.find(s_section) == 0:
            i_start_pos = len(s_section)
            s_data = s_line[i_start_pos:]
            s_data = s_data.strip()
            s_data = s_data.strip('"')
            ls_data.append(s_data)

    if s_mode == 'single':
        x_output = s_data
    elif s_mode == 'multi':
        x_output = ls_data
    else:
        raise Exception('Error: %s mode for _dat_vertical_parse() NOT known.' % s_mode)

    return x_output


def _dat_horizontal_parse(s_line, s_start, s_end):
    """
    Function to parse a SINGLE line containing information about a particular item.

    So, the information follows a pattern similar to:

        a_start DATA_A a_end b_start DATA_B b_end...

    :param s_line: string containing the line to be parsed.

    :param s_start: leading string for data. In the above example: "a_start", "b_start"...

    :param s_end: ending string for data. In the above example: "a_end", "b_end"...

    Comment: Typically, all the items inside the line are unique, so there is no need to 'multi' parameter like in
    _dat_vertical_parse() function.

        @rtype: string

    """

    s_output = ''

    if s_line.find(s_start) != -1:
        i_start_pos = s_line.find(s_start) + len(s_start)
        i_end_pos = s_line.find(s_end, i_start_pos)

        if i_end_pos != -1:
            s_output = s_line[i_start_pos:i_end_pos]

    # It shouldn't appear extra spaces around the real data but just in case...
    s_output = s_output.strip()
    s_output = s_output.strip('"')
    s_output = s_output.strip()

    return s_output


def _hex_add(pu_hex_a, pu_hex_b):
    """
    Function to add two hex digits
    :param pu_hex_a:
    :param pu_hex_b:
    :return:
    """

    s_hex_a = str(pu_hex_a)
    s_hex_b = str(pu_hex_b)

    # Padding the strings so they are LONGEST + 1 (the +1 is to keep the carryover)
    i_length = max(len(s_hex_a), len(s_hex_b)) + 1

    s_hex_a = s_hex_a.rjust(i_length, '0')
    s_hex_b = s_hex_b.rjust(i_length, '0')

    # We start the addition process
    #------------------------------
    s_hex_result = ''

    i_carry_over = 0

    for u_digit_a, u_digit_b in zip(s_hex_a[::-1], s_hex_b[::-1]):
        i_digit_c = int(u_digit_a, 16) + int(u_digit_b, 16) + i_carry_over
        s_digits_c = hex(i_digit_c).partition('x')[2]

        if len(s_digits_c) == 2:
            i_carry_over = int(s_digits_c[0])
            s_hex_result += s_digits_c[1]
        else:
            i_carry_over = 0
            s_hex_result += s_digits_c[0]

    s_hex_result = s_hex_result[::-1].lstrip('0')

    return unicode(s_hex_result)


def _compound_hash(plu_hexs):
    """
    Function to return the compound hex of a list of hexs
    :param plu_hexs:
    :return:
    """
    if None not in plu_hexs:
        u_result = u'0'
        for u_hex in plu_hexs:
            u_result = _hex_add(u_result, u_hex)
    else:
        u_result = None

    return u_result
