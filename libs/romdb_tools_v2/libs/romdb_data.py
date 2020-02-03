#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
_File to define the classes representing the contents of ROMdb website.
"""

import string_operators


# Version classes
# =======================================================================================================================
class Version:
    def __init__(self):
        self.u_dat_name = None
        self.u_dat_version = None
        self.u_dat_updated = None
        self.u_romset_platform = None
        self.u_romset_title = None
        self.u_romset_crc32 = None
        self.i_romset_size = None

        self.o_mdata_screen_titles = _ScreenTitles()
        self.u_mdata_date = None
        self.u_serial_number = None
        self.lu_mdata_language_text = []
        self.lu_mdata_language_voice = None
        self.lu_mdata_views = []
        self.o_mdata_overscan = None
        self.o_mdata_media = None
        self.o_mdata_multiplayer = None
        self.o_mdata_rating = None
        self.lo_mdata_differences = None

        self.lo_siblings = []
        self.lo_parent_games = []

        self.u_screenshot_title = None
        self.u_screenshot_ingame = None

    def __str__(self):
        return unicode(self).encode('utf8')

    def __unicode__(self):
        u_out = u'<Version>\n'
        u_out += u'  -----------------------\n'
        u_out += u'  .u_dat_name:            %s\n' % self.u_dat_name
        u_out += u'  .u_dat_version:         %s\n' % self.u_dat_version
        u_out += u'  .u_dat_updated:         %s\n' % self.u_dat_updated
        u_out += u'  -----------------------\n'
        u_out += u'  .u_romset_platform:     %s\n' % self.u_romset_platform
        u_out += u'  .u_romset_title:        %s\n' % self.u_romset_title
        u_out += u'  .u_romset_crc32:        %s\n' % self.u_romset_crc32
        u_out += u'  .u_romset_size:         %s\n' % self.i_romset_size
        u_out += u'  -----------------------\n'
        u_out += u'  .o_mdata_overscan:      %s\n' % self.o_mdata_overscan.to_oneline()
        u_out += u'  .o_mdata_screen_titles: %s\n' % self.o_mdata_screen_titles.to_oneline(26)
        u_out += u'  .u_mdata_date:          %s\n' % self.u_mdata_date
        u_out += u'  .o_mdata_media:         %s\n' % self.o_mdata_media
        u_out += u'  .o_mdata_multiplayer:   %s\n' % self.o_mdata_multiplayer
        u_out += u'  .o_mdata_rating:        %s\n' % self.o_mdata_rating
        u_out += u'  .lo_mdata_differences:  %s\n' % self.lo_mdata_differences.to_oneline(26)
        u_out += u'  .lo_siblings:           %s\n'

        for o_sibling in self.lo_siblings:
            u_sibling = unicode(o_sibling)
            for u_line in u_sibling.splitlines():
                u_out += u'%s%s\n' % (u' ' * 26, u_line)

        u_out += u'  -> NEW PROPERTY <-\n'

        return u_out

    def from_json(self, pdx_json):
        """
        Method to parse the data from a ROMdb json.
        :param pdx_json:
        :return:
        """
        self.u_dat_name = pdx_json['s_dat_name']
        self.u_dat_version = pdx_json['s_dat_version']
        self.u_dat_updated = pdx_json['s_dat_outdated']

        self.u_romset_platform = pdx_json['s_romset_platform']
        self.u_romset_title = pdx_json['s_romset_title']
        self.u_romset_crc32 = pdx_json['s_romset_crc32']

        try:
            self.i_romset_size = int(pdx_json['i_romset_size'])
        except TypeError:
            pass

        self.o_mdata_overscan = _Overscan(pdx_json['s_mdata_overscan'])

        for u_entry in pdx_json['as_mdata_screen_titles']:
            self.o_mdata_screen_titles.add_title(u_entry)

        self.u_mdata_date = pdx_json['s_mdata_date']
        self.o_mdata_media = _Media(pdx_json['s_mdata_media_type'], pdx_json['i_mdata_media_number'])
        self.o_mdata_multiplayer = _Multiplayer(pdx_json['ai_mdata_players'], pdx_json['as_mdata_multiplayer'])
        self.o_mdata_rating = _Rating(pdx_json['f_mdata_rating_value'], pdx_json['i_mdata_rating_votes'])
        self.lo_mdata_differences = _Differences(pdx_json['s_mdata_differences'])
        self.lu_mdata_language_text = pdx_json['as_mdata_lang_text']
        self.lu_mdata_language_voice = pdx_json['as_mdata_lang_voice']
        self.lu_mdata_views = pdx_json['as_mdata_views']
        self.u_screenshot_title = pdx_json['s_screenshot_title']
        self.u_screenshot_ingame = pdx_json['s_screenshot_ingame']

        # Siblings
        #---------
        for dx_entry in pdx_json['ao_sibling_versions']:
            o_sibling_version = Version()
            o_sibling_version.from_json(dx_entry)
            self.lo_siblings.append(o_sibling_version)

        # Parent Games
        #-------------
        for dx_entry in pdx_json['ao_parent_games']:
            o_parent_game = Game()
            o_parent_game.from_json(dx_entry)
            self.lo_parent_games.append(o_parent_game)

    def nice_text(self, ps_format='short'):
        if ps_format == 'short':
            u_out = self._nice_text_short()
        elif ps_format == 'medium':
            u_out = self._nice_text_medium()
        else:
            raise ValueError('Invalid ps_format "%s"' % ps_format)

        return u_out

    def _nice_text_medium(self):
        """
        Function to generate a nice medium-size text output of the object ready to be printed.

        :return: An unicode string.
        """
        u_out = u''
        u_out += u'┌[Version]───────────────\n'
        u_out += u'│             u_dat_name: %s\n' % self.u_dat_name
        u_out += u'│          u_dat_version: %s\n' % self.u_dat_version
        u_out += u'│          u_dat_updated: %s\n' % self.u_dat_updated
        u_out += u'├───────────────────────\n'
        u_out += u'│      u_romset_platform: %s\n' % self.u_romset_platform
        u_out += u'│         u_romset_title: %s\n' % self.u_romset_title
        u_out += u'│         u_romset_crc32: %s\n' % self.u_romset_crc32
        u_out += u'│          u_romset_size: %s\n' % self.i_romset_size
        u_out += u'├────────────────────────\n'
        u_out += u'│       o_mdata_overscan: %s\n' % self.o_mdata_overscan.to_oneline()
        u_out += u'│         lu_mdata_views: %s\n' % u', '.join(self.lu_mdata_views)
        u_out += u'│  o_mdata_screen_titles: %s\n' % self.o_mdata_screen_titles.to_oneline(26)
        u_out += u'│           u_mdata_date: %s\n' % self.u_mdata_date
        u_out += u'│ lu_mdata_language_text: %s\n' % u', '.join(self.lu_mdata_language_text)
        u_out += u'│lu_mdata_language_voice: %s\n' % u', '.join(self.lu_mdata_language_voice)
        u_out += u'│          o_mdata_media: %s\n' % self.o_mdata_media
        u_out += u'│    o_mdata_multiplayer: %s\n' % self.o_mdata_multiplayer
        u_out += u'│         o_mdata_rating: %s\n' % self.o_mdata_rating
        u_out += u'│   lo_mdata_differences: %s\n' % self.lo_mdata_differences.to_oneline(26)

        # Sibling versions
        # -----------------
        lu_lines = []
        if self.lo_siblings:
            for o_sibling in self.lo_siblings:
                u_line = o_sibling.nice_text(ps_format='short')
                lu_lines.append(u_line)
            u_out += _lines_indent(u'│            lo_siblings: ', lu_lines, u'│                         ')
        else:
            u_out += u'│            lo_siblings:\n'

        # Parent games
        # -------------
        u_out += u'├────────────────────────\n'
        if self.lo_parent_games:
            u_games = u''
            for o_game in self.lo_parent_games:
                u_games += o_game.nice_text(ps_format='short')

            u_out += _lines_indent(u'│        lo_parent_games: ', u_games.splitlines(), u'│                         ')
        else:
            u_out += u'│        lo_parent_games:\n'

        # Screenshots
        # ------------
        u_out += u'├────────────────────────\n'
        u_out += u'│     u_screenshot_title: %s\n' % self.u_screenshot_title
        u_out += u'│    u_screenshot_ingame: %s\n' % self.u_screenshot_ingame
        u_out += u'└────────────────────────\n'
        return u_out

    def _nice_text_short(self):
        u_out = u'[%s/%s] %s %s%% %s' % (self.u_romset_platform.rjust(7, u' '),
                                         self.u_romset_crc32,
                                         unicode(self.u_mdata_date)[0:4],
                                         unicode(int(self.o_mdata_rating.f_average)).rjust(2, u' '),
                                         self.u_romset_title)
        return u_out


class _Media:
    def __init__(self, pu_type, pi_number):
        self.u_type = pu_type
        self.i_number = pi_number

    def __str__(self):
        return unicode(self).encode('utf8')

    def __unicode__(self):
        u_out = u'%s × %s' % (self.u_type, self.i_number)
        return u_out


class _Multiplayer:
    def __init__(self, plu_players, plu_multiplayer_type):
        self.lu_players = []
        self.lu_multiplayer_type = []

        for u_item in plu_players:
            self.lu_players.append(u_item)

        for u_item in plu_multiplayer_type:
            self.lu_multiplayer_type.append(u_item)

    def __str__(self):
        return unicode(self).encode('utf8')

    def __unicode__(self):
        if self.lu_players and self.lu_multiplayer_type:
            u_join = u' | '
        else:
            u_join = u''

        u_out = u'%s%s%s' % (u', '.join(self.lu_players), u_join, u', '.join(self.lu_multiplayer_type))

        return u_out


class _Overscan:
    def __init__(self, pu_line):
        self.i_top = 0
        self.i_bottom = 0
        self.i_left = 0
        self.i_right = 0

        self._from_oneline(pu_line)

    def __str__(self):
        return unicode(self).encode('utf8')

    def __unicode__(self):
        u_out = u'<_Overscan>\n'
        u_out += u'  .i_top:    %s\n' % self.i_top
        u_out += u'  .i_bottom: %s\n' % self.i_bottom
        u_out += u'  .i_left:   %s\n' % self.i_left
        u_out += u'  .i_right:  %s\n' % self.i_right
        return u_out

    def _from_oneline(self, pu_line):
        """
        Method to parse the overscan line produced by ROMdb.
        :return:
        """
        if pu_line:
            lu_words = pu_line.split(u', ')
            self.i_top = int(lu_words[0])
            self.i_right = int(lu_words[1])
            self.i_bottom = int(lu_words[2])
            self.i_left = int(lu_words[3])

    def to_oneline(self):
        u_out = u'%s, %s, %s, %s' % (self.i_top, self.i_right, self.i_bottom, self.i_left)
        return u_out


class _Rating:
    """
    Class to store a rating field
    """

    def __init__(self, pf_average, pi_votes):
        try:
            self.f_average = float(pf_average)
        except TypeError:
            self.f_average = 0.0

        try:
            self.i_votes = int(pi_votes)
        except TypeError:
            self.i_votes = 0

    def __str__(self):
        return unicode(self).encode('utf8')

    def __unicode__(self):
        u_out = u'%s%% based on %s votes' % (int(self.f_average), self.i_votes)
        return u_out


class _ScreenTitles:
    def __init__(self):
        self._lo_titles = []

    def __str__(self):
        return unicode(self).encode('utf8')

    def __unicode__(self):
        lu_titles = []
        for o_title in self._lo_titles:
            lu_titles.append(o_title.to_oneline())
        u_out = u'\n'.join(lu_titles)
        return u_out

    def add_title(self, pu_title):
        o_new_title = _ScreenTitle(pu_title)
        self._lo_titles.append(o_new_title)

    def to_oneline(self, pi_indentation=0):
        lu_out = []
        for i_index, o_screen_title in enumerate(self._lo_titles):
            if i_index == 0:
                lu_out.append(u'%s' % o_screen_title.to_oneline())
            else:
                lu_out.append(u'%s%s' % (u' ' * pi_indentation, o_screen_title.to_oneline()))

        return u'\n'.join(lu_out)


class _ScreenTitle:
    def __init__(self, pu_line):
        self.u_country = None  # Country where the title appears
        self.u_title_original = None  # Title written with original characters (kanjis, for example)
        self.u_title_western = None  # Western characters title

        self._from_oneline(pu_line)

    def __str__(self):
        return unicode(self).encode('utf8')

    def __unicode__(self):
        u_out = u'<_ScreenTitle>\n'
        u_out += u'  .u_country:        %s\n' % self.u_country
        u_out += u'  .u_title_western:  %s\n' % self.u_title_western
        u_out += u'  .u_title_original: %s\n' % self.u_title_original
        return u_out

    def _from_oneline(self, pu_line):
        self.u_country = pu_line[1:4]
        self.u_title_western = pu_line[5:].partition(u' / ')[0].strip()
        self.u_title_original = pu_line[5:].partition(u' / ')[2].strip()

    def to_oneline(self):
        if self.u_title_original:
            u_line = u'[%s] %s / %s' % (self.u_country, self.u_title_western, self.u_title_original)
        else:
            u_line = u'[%s] %s' % (self.u_country, self.u_title_western)
        return u_line


class _Differences:
    def __init__(self, pu_differences):
        self.lo_differences = []

        if pu_differences:
            for u_line in pu_differences.splitlines():
                o_difference = _Difference(u_line)
                self.lo_differences.append(o_difference)

    def __str__(self):
        return unicode(self).encode('utf8')

    def __unicode__(self):
        lu_out = []
        for o_difference in self.lo_differences:
            lu_out.append(unicode(o_difference))

        return u'\n'.join(lu_out)

    def to_oneline(self, pi_indentation=0):
        lu_lines = []
        for i_index, o_diff in enumerate(self.lo_differences):
            if i_index == 0:
                u_indent = u''
            else:
                u_indent = u' ' * pi_indentation

            lu_lines.append(u'%s%s' % (u_indent, o_diff))

        return u'\n'.join(lu_lines)


class _Difference:
    def __init__(self, pu_difference):
        self.u_type = pu_difference[0]
        self.u_description = pu_difference[2:].strip()

    def __str__(self):
        return unicode(self).encode('utf8')

    def __unicode__(self):
        u_out = u'%s %s' % (self.u_type, self.u_description)
        return u_out


# Game classes
# =======================================================================================================================
class Game:
    def __init__(self):
        self.i_nid = u''
        self.u_title = u''
        self.u_synopsis = u''
        self.u_years = u''
        self.lu_genres = []
        self.lo_sagas = []

    def from_json(self, pdx_json):
        self.i_nid = pdx_json['i_nid']
        self.u_title = pdx_json['s_title']
        self.u_years = pdx_json['s_years']
        self.u_synopsis = pdx_json['s_synopsis']
        self.lu_genres = pdx_json['as_genres']

        for dx_entry in pdx_json['ao_sagas']:
            o_saga = Saga(dx_entry)
            self.lo_sagas.append(o_saga)

    def nice_text(self, ps_format='short'):
        if ps_format == 'short':
            u_out = self._nice_text_short()
        elif ps_format == 'medium':
            u_out = u''
            u_out += u'┌[Game]─────\n'
            u_out += u'│     i_nid: %s\n' % self.i_nid
            u_out += u'│   u_titl: %s\n' % self.u_title
            u_out += u'│   u_years: %s\n' % self.u_years
            u_out += u'│ lu_genres: %s\n' % u', '.join(self.lu_genres)

            u_out += _lines_indent(u'│u_synopsis: ', string_operators.sentence_split(self.u_synopsis), u'│            ')

            for o_saga in self.lo_sagas:
                u_out += _lines_indent(u'│  lo_sagas: ', o_saga.nice_text().splitlines(), u'│            ')

            u_out += u'└───────────\n'

        else:
            raise ValueError('Invalid ps_format "%s"' % ps_format)

        return u_out

    def _nice_text_short(self):
        u_out = u''
        u_out += u'[%s] %s\n' % (self.i_nid, self.u_title)
        # u_out += u'lu_genres: %s\n' % u', '.join(self.lu_genres)
        return u_out


class Saga:
    def __init__(self, pdx_json):
        self.i_nid = None
        self.u_title = u'---'
        self.u_synopsis = u'---'
        self.u_years = u'---'

        self._from_json(pdx_json)

    def _from_json(self, pdx_json):
        self.i_nid = pdx_json['i_nid']
        self.u_title = pdx_json['s_title']
        self.u_synopsis = pdx_json['s_synopsis']
        self.u_years = pdx_json['s_years']

    def nice_text(self, ps_format='short'):
        if ps_format == 'short':
            u_out = self._nice_text_short()
        elif ps_format == 'medium':
            u_out = u''
            u_out += u'┌[Saga]─────\n'
            u_out += u'│     i_nid: %s\n' % self.i_nid
            u_out += u'│   u_titl: %s\n' % self.u_title
            u_out += u'│   u_years: %s\n' % self.u_years
            u_out += u'│u_synopsis: %s\n' % self.u_synopsis
            u_out += u'└───────────\n'

        else:
            raise ValueError('Invalid ps_format "%s"' % ps_format)

        return u_out

    def _nice_text_short(self):
        u_out = u'[nid: %s] %s\n' % (self.i_nid, self.u_title)
        return u_out


# Helper Functions
# =======================================================================================================================
def _lines_indent(pu_start, plu_lines, pu_indent):
    lu_lines = []

    for i_line, u_line in enumerate(plu_lines):
        if i_line == 0:
            u_left = pu_start
        else:
            u_left = pu_indent

        u_line = u'%s%s' % (u_left, u_line)
        lu_lines.append(u_line)

    return u'\n'.join(lu_lines) + u'\n'
