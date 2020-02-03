#!/usr/bin/env python

import codecs
import os
import subprocess
import sys
import tkinter
import tkinter.filedialog
import tkinter.ttk
import urllib2
import webbrowser

import libs.sitemap
import libs.romdb_tools_v2.romdb_rom_info as romdb_rom_info

# Constants
#=======================================================================================================================
u_ROMDB_SITEMAP = u'https://romdb.geeklogger.com/sitemap.xml'
_tu_PLATFORMS = (
    u'a26     | Atari 2600',
    u'a52     | Atari 5200',
    u'a78     | Atari 7800',
    u'amg-a5c | Amiga 500',
    u'arc     | Arcade (MAME)',
    u'ast     | Atari ST',
    u'nes-fds | Famicom Disk System',
    u'gba-crt | Game Boy Advance',
    u'gbc     | Game Boy Color',
    u'gbo     | Game Boy',
    u'sgg     | Game Gear',
    u'jag-crt | Jaguar (cartridge)',
    u'lnx     | Lynx',
    u'sms     | Master System',
    u'mdr-mcd | Mega CD',
    u'mdr-32x | Megadrive 32X',
    u'mdr-crt | Megadrive',
    u'ms1-crt | MSX (cartridge)',
    u'ms2-crt | MSX2 (cartridge)',
    u'nes-crt | NES',
    u'ps1     | Playstation',
    u'snt-sat | Satellaview',
    u'zxs-dsk | Spectrum +3 (disk)',
    u'snt-crt | Super Nintendo',
    u'tgx-crt | Turbofrafx',
    )


# Classes
#=======================================================================================================================
class MainWindow:
    def __init__(self):

        self._o_window = tkinter.Tk()
        self._o_window.title("ROMdb Screenshot Downloader v1.0")

        self._lu_urls = []
        self._u_log = u''

        self._o_var_overwrite = tkinter.IntVar()
        self._o_var_crc_name = tkinter.IntVar()

        # Top notification
        #-----------------
        u_msg = u'ROMdb doesn\'t contain any advertisement, doesn\'t sell its users data or any other nasty thing.' \
                u'Please be kind: Don\'t download several big systems (e.g. arcade, megadrive, super nintendo, game ' \
                u'boy advance...) at once, and consider making a donation to support the web at Patreon.'

        o_disclaimer = tkinter.Label(
            master=self._o_window,
            padx=20,
            justify=tkinter.LEFT,
            text=u_msg,
            wraplength=500,
        )
        o_disclaimer.grid(
            row=0,
            column=0,
            columnspan=4,
            padx=10,
            pady=10,)

        o_romdb_link = tkinter.Button(
            borderwidth=0,
            command=self._callback_website,
            cursor='hand1',
            fg='blue',
            text=u'https://romdb.geeklogger.com')
        o_romdb_link.grid(
            row=1,
            column=0,
            columnspan=4,
        )

        o_patreon_link = tkinter.Button(
            borderwidth=0,
            command=self._callback_patreon,
            cursor='hand1',
            fg='blue',
            text=u'https://www.patreon.com/geeklogger')
        o_patreon_link.grid(
            row=2,
            column=0,
            columnspan=4,
            pady=(0, 20))

        # Checkboxes to choose which systems to download images for
        #----------------------------------------------------------
        self.lo_platforms = []
        self._o_output_dir = tkinter.StringVar()

        # TODO: Improve list slicing so the first part always is equal or bigger to the second one (for aesthetics)
        i_split = len(_tu_PLATFORMS) // 2
        lu_platforms_1 = _tu_PLATFORMS[:i_split]
        lu_platforms_2 = _tu_PLATFORMS[i_split:]

        for i_platform_list, lu_platform_list in enumerate((lu_platforms_1, lu_platforms_2)):
            for i_platform, u_platform in enumerate(lu_platform_list):
                u_platform_long = u_platform.split(u'|')[1].strip()

                o_var = tkinter.IntVar()
                self.lo_platforms.append(o_var)
                o_checkbox = tkinter.Checkbutton(
                                self._o_window,
                                font=('courier', 9),
                                text=u_platform_long,
                                variable=o_var)
                o_checkbox.grid(
                    column=i_platform_list * 2,
                    columnspan=2,
                    padx=20,
                    row=i_platform + 3,
                    sticky=tkinter.W)

        # Separator
        #----------
        o_separator = tkinter.ttk.Separator(
            self._o_window,
            orient=tkinter.HORIZONTAL)
        o_separator.grid(
            column=0,
            row=i_split + 4,
            columnspan=4,
            padx=20,
            pady=20,
            sticky='we')

        # Output directory browser
        #-------------------------
        o_label_output = tkinter.Label(
                             master=self._o_window,
                             text=u'Output:',
                             )
        o_label_output.grid(
            row=i_split + 5,
            column=0,
            pady=(0, 20),
            sticky='e',
            )

        o_label_output_dir = tkinter.Label(
            anchor='e',
            bg='white',
            borderwidth=1,
            master=self._o_window,
            textvariable=self._o_output_dir,
            width=52)
        o_label_output_dir.grid(
            row=i_split + 5,
            column=1,
            columnspan=3,
            pady=(0, 20),
            sticky='w')

        # Buttons
        #--------
        o_button_browse = tkinter.Button(
                              text=u'Choose',
                              command=self._callback_set_output_dir,
                              width=7,
                              )
        o_button_browse.grid(
            row=i_split + 6,
            column=2,
            sticky='e',
            )

        o_button_open = tkinter.Button(
                            text=u'Open',
                            command=self._callback_open_output_dir,
                            width=7,
                            )
        o_button_open.grid(
            row=i_split + 6,
            column=3,
            )

        # Download button
        #----------------
        o_dl_button = tkinter.Button(
                          self._o_window,
                          text=u'Download',
                          command=self._download_screenshots,
                          width=7)
        o_dl_button.grid(
            column=3,
            row=i_split + 7,
            )

        # Checkbox for overwriting
        #-------------------------
        o_check_overwrite = tkinter.Checkbutton(
                                self._o_window,
                                font=('courier', 9),
                                text=u'Overwrite',
                                variable=self._o_var_overwrite)
        o_check_overwrite.grid(column=1,
                               row=i_split + 6,
                               sticky='w')

        # Checkbox for naming
        #--------------------
        o_checkbox = tkinter.Checkbutton(
                        self._o_window,
                        font=('courier', 9),
                        text=u'CRC32 name',
                        variable=self._o_var_crc_name)
        o_checkbox.grid(
            column=1,
            row=i_split + 7,
            sticky='w')

        # Save log
        #---------
        o_log_button = tkinter.Button(
                           self._o_window,
                           text=u'Save log',
                           command=self._callback_save_log,
                           width=7,
                           )
        o_log_button.grid(
            column=2,
            row=i_split + 7,
            sticky='e',
        )

        # Output text widget
        #-------------------
        self._o_text_var = tkinter.StringVar()

        self._o_text = tkinter.Label(
                           self._o_window,
                           anchor='nw',
                           font=('courier', 10),
                           justify=tkinter.LEFT,
                           textvariable=self._o_text_var,
                           width=60,
                           height=2,
                           borderwidth=1,
                           relief='sunken',
                           )

        self._o_text.grid(
            column=0,
            columnspan=4,
            padx=20,
            pady=20,
            row=i_split + 8,
            sticky='nsew',
            )

        self._o_window.mainloop()

    @staticmethod
    def _callback_website():
        webbrowser.open_new(u'https://romdb.geeklogger.com')

    @staticmethod
    def _callback_patreon():
        webbrowser.open_new(u'https://www.patreon.com/geeklogger')

    def _get_all_urls(self):
        """
        Function to get all the version URLs stored in the sitemap.xml of ROMdb
        :return:
        """
        if not self._lu_urls:
            self._lu_urls = libs.sitemap.get_urls(u_ROMDB_SITEMAP)

    def _create_output_dirs(self, plu_platforms):
        """
        Method to create the output directory for downloaded images
        :param plu_platforms:
        :return:
        """
        # [?/?] Output dirs creation
        #---------------------------
        u_output_dir = self._o_output_dir.get()
        for u_platform in plu_platforms:
            u_dir_title = _build_save_dir(u_output_dir, u_platform, ps_type='title')
            u_dir_ingame = _build_save_dir(u_output_dir, u_platform, ps_type='ingame')

            try:
                os.makedirs(u_dir_title)
            except OSError:
                pass

            try:
                os.makedirs(u_dir_ingame)
            except OSError:
                pass

            # The excepts above will catch the situation where the folder can't be created so we have to additionally
            # check for that unwanted circumstance
            if not os.path.isdir(u_dir_title) or not os.path.isdir(u_dir_ingame):
                raise OSError

    def _download_screenshots(self):
        """
        Function to download the selected systems' screenshots.
        :return:
        """

        # [0/?] Initialisation
        #---------------------
        du_download_result_codes_to_log = {'downloaded':     u'O',
                                           'skipped':        u'o',
                                           'missing':        u'-',
                                           'download_error': u'd',
                                           'write_error':    u'w'}

        self._o_text_var.set(u'')

        # [1/?] Download checks
        #----------------------

        # Output directory exists
        #------------------------
        u_output_root = self._o_output_dir.get()
        if not os.path.isdir(u_output_root):
            if u_output_root == u'':
                u_msg = u'ERROR: Output directory not selected'
            else:
                u_msg = u'ERROR: Output directory doesn\'t exist'

            self._o_text_var.set(u_msg)
            return

        # At least one platform selected
        #-------------------------------
        li_platforms = []
        for o_platform in self.lo_platforms:
            li_platforms.append(o_platform.get())
        if 1 not in li_platforms:
            u_msg = u'ERROR: You must select at least one platform'
            self._o_text_var.set(u_msg)
            return

        # [1/?] We build a tuple with the platform alias to be considered
        #----------------------------------------------------------------
        lu_selected_platforms = []
        for o_platform, u_platform in zip(self.lo_platforms, _tu_PLATFORMS):
            if o_platform.get() == 1:
                u_platform_alias = u_platform.split(u'|')[0].strip()
                lu_selected_platforms.append(u_platform_alias)

        # [?/?] Output dirs creation
        #---------------------------
        try:
            self._create_output_dirs(lu_selected_platforms)
        except OSError:
            u_msg = u'ERROR: I couldn\'t create the output dirs to download the images'
            self._o_text_var.set(u_msg)
            return

        # [2/?] Getting the URLs for the systems selected
        #------------------------------------------------
        self._get_all_urls()
        lu_filtered_urls = []

        for u_url in self._lu_urls:
            lu_components = u_url.split(u'/')
            if lu_components[3] == u'versions':
                u_platform = lu_components[4]
                if u_platform in lu_selected_platforms:
                    lu_filtered_urls.append(u_url)

        # [3/?] Downloading images for selected URLs
        #-------------------------------------------
        i_romdb_title = 0    # Number of ROMdb title screenshots found
        i_romdb_ingame = 0   # Number of ROMdb ingame screenshots found

        i_dl_title = 0       # Number of local title screenshots
        i_dl_ingame = 0      # Number of local ingame screenshots

        i_local_title = 0    # Number of local title screenshots
        i_local_ingame = 0   # Number of local ingame screenshots

        i_total = len(lu_filtered_urls)
        u_total = unicode(i_total)
        i_total_char_len = len(u_total)
        self._u_log = u''
        for i_current_url_pos, u_url in enumerate(tuple(lu_filtered_urls)):
            u_current_url_pos = u'%s' % (i_current_url_pos + 1)
            u_current_url_pos = u_current_url_pos.rjust(i_total_char_len, u' ')
            u_platform, u_crc32 = _platform_and_crc32_from_url(u_url)
            o_romdb_version = romdb_rom_info.query_romset_by_crc32(pu_platform=u_platform, pu_crc32=u_crc32)

            if o_romdb_version is None:
                u_window_msg = u'FOO'
                u_log_msg = u'BAR'

            else:
                # Downloading title screenshots
                #------------------------------
                u_output_dir = _build_save_dir(u_output_root, u_platform, ps_type='title')

                if self._o_var_crc_name.get():
                    s_filename = u_crc32
                else:
                    s_filename = o_romdb_version.u_romset_title

                u_output_file = os.path.join(u_output_dir, u'%s.png' % s_filename)
                s_result = _download_file(
                               o_romdb_version.u_screenshot_title,
                               u_output_file,
                               pb_overwrite=self._o_var_overwrite.get())

                # Keeping track of online/downloaded/local images to make some stats
                if o_romdb_version.u_screenshot_title is not None:
                    i_romdb_title += 1
                if s_result == 'downloaded':
                    i_dl_title += 1
                if s_result in ('downloaded', 'skipped'):
                    i_local_title += 1

                u_title = du_download_result_codes_to_log[s_result]

                # Downloading ingame screenshots
                #------------------------------
                u_output_dir = _build_save_dir(u_output_root, u_platform, ps_type='ingame')

                if self._o_var_crc_name.get():
                    s_filename = u_crc32
                else:
                    s_filename = o_romdb_version.u_romset_title

                u_output_file = os.path.join(u_output_dir, u'%s.png' % s_filename)
                s_result = _download_file(
                               o_romdb_version.u_screenshot_ingame,
                               u_output_file,
                               pb_overwrite=self._o_var_overwrite.get())

                # Keeping track of online/downloaded/local images to make some stats
                if o_romdb_version.u_screenshot_ingame is not None:
                    i_romdb_ingame += 1
                if s_result == 'downloaded':
                    i_dl_ingame += 1
                if s_result in ('downloaded', 'skipped'):
                    i_local_ingame += 1

                u_ingame = du_download_result_codes_to_log[s_result]

                u_face = u'%s_%s' % (u_title, u_ingame)
                u_top_left = u'%s %s %s' % (u_face, u_platform, u_crc32)
                u_progress = u'[%s/%s]' % (u_current_url_pos, u_total)
                u_progress = u_progress.rjust(64 - len(u_top_left), u' ')
                u_top = u'%s %s\n' % (u_top_left, u_progress)
                u_bottom = u'    %s' % o_romdb_version.u_romset_title
                u_window_msg = u'%s%s' % (u_top, u_bottom)

                # log message doesn't contain version name because it'll be resorted before saving to disk
                u_log_msg = u'%s %s %s | %s' % (
                                u_face,
                                u_platform,
                                u_crc32,
                                o_romdb_version.u_romset_title,
                                )

            self._o_text_var.set(u_window_msg)
            self._u_log += u'%s\n' % u_log_msg
            self._o_window.update_idletasks()

        self._u_log += u'\nIngame: ROMdb %i/%i  local %i (%.1f %%)  downloaded %i' % (
            i_romdb_title,
            i_total,
            i_local_title,
            100.0 * i_local_title / i_romdb_title,
            i_dl_title)
        self._u_log += u'\nTitle:  ROMdb %i/%i  local %i (%.1f %%)  downloaded %i' % (
            i_romdb_ingame,
            i_total,
            i_local_ingame,
            100.0 * i_local_ingame / i_romdb_ingame,
            i_dl_ingame)
        self._u_log += u'\n'
        self._u_log += u'\nX_Y  X = Title screenshot  Y = Ingame screenshot'
        self._u_log += u'\nO_O  OK, screenshots downloaded'
        self._u_log += u'\no_o  OK, screenshots skipped because they were previously downloaded'
        self._u_log += u'\nd_d  Error when downloading the images'
        self._u_log += u'\nw_w  Error when writing the images'
        self._u_log += u'\n-_-  Screenshots not available in ROMdb'

    def _callback_set_output_dir(self):
        u_output_dir = tkinter.filedialog.askdirectory()
        self._o_output_dir.set(u_output_dir)

    def _callback_open_output_dir(self):
        """
        Method to open a file browser to the output directory.
        :return: Nothing
        """
        u_output_dir = self._o_output_dir.get()

        if sys.platform == 'win32':
            subprocess.Popen(['start', u_output_dir], shell=True)

        elif sys.platform == 'darwin':
            subprocess.Popen(['open', u_output_dir])

        else:
            try:
                subprocess.Popen(['xdg-open', u_output_dir])
            except OSError:
                pass
                # er, think of something else to try
                # xdg-open *should* be supported by recent Gnome, KDE, Xfce

    def _callback_save_log(self):
        """
        Method to save the download log to disk.
        :return:
        """

        # [1/?] Sorting the log
        #----------------------
        # The files are downloaded in the order dictated by sitemap.xml. Which means different systems are mixed (if
        # several systems are downloaded at once) and versions won't appear alphabetically sorted by title. To solve
        # this issue, the log should be resorted before saving by platform/rom title
        lu_log_lines = self._u_log.splitlines()
        lu_vers_lines = lu_log_lines[:-10]
        lu_stat_lines = lu_log_lines[-10:]

        lu_sorting_strings = []
        for u_line in lu_vers_lines:
            lu_words = u_line.split()
            u_platform = lu_words[1]
            u_title = lu_words[4]
            u_sorting_string = u'%s %s' % (u_platform, u_title)
            lu_sorting_strings.append(u_sorting_string)

        lu_vers_lines_sorted = [u_version_line for _, u_version_line in sorted(zip(lu_sorting_strings, lu_vers_lines))]

        # [2/?] Adding the numbers at the beginning of each line
        #-------------------------------------------------------
        i_total = len(lu_vers_lines_sorted)
        u_total = unicode(i_total)
        i_total_chars = len(u_total)

        lu_version_lines_final = []
        for i_line, u_version_line in enumerate(lu_vers_lines_sorted):
            u_line = u'%s' % (i_line + 1)
            u_line = u_line.rjust(i_total_chars, u' ')

            u_version_line = u'[%s/%s] %s' % (u_line, u_total, u_version_line)
            lu_version_lines_final.append(u_version_line)

        u_log = u'%s\n%s' % (u'\n'.join(lu_version_lines_final),
                             u'\n'.join(lu_stat_lines))

        u_file = os.path.join(self._o_output_dir.get(), u'romdb_screenshot_downloader.log')

        with codecs.open(u_file, 'w', 'utf8') as o_file:
            o_file.write(u_log)

        self._o_text_var.set(u'Log saved in output directory!')


# Helper functions
#=======================================================================================================================
def _platform_and_crc32_from_url(pu_url):
    """
    Function to obtain the platform alias and the version CRC32 from the URL
    :param pu_url: URL from ROMdb
    :type pu_url: unicode

    :return: The platform alias, and the version CRC32
    :rtype  unicode, unicode
    """
    u_platform = None
    u_crc32 = None

    lu_elements = pu_url.split(u'/')
    if lu_elements[-3] == u'versions':
        u_platform = lu_elements[-2]
        u_crc32 = lu_elements[-1]

    return u_platform, u_crc32


def _build_save_dir(pu_root, pu_platform, ps_type):
    """
    Function to build the path of the local directory for screenshots
    :param pu_root: Root of the screenshots
    :type pu_root: unicode

    :param pu_platform: Alias of the platform. e.g. u'snt-crt'
    :type pu_platform: unicode

    :param ps_type: Type of screenshot: 'title' or 'ingame'
    :type ps_type: str

    :return: The path to save the screenshots.
    :rtype unicode
    """
    if ps_type == 'title':
        u_type = u'titles'
    elif ps_type == 'ingame':
        u_type = u'ingame'
    else:
        raise ValueError

    u_dir = os.path.join(pu_root, pu_platform, u_type)
    return u_dir


def _download_file(pu_source, pu_destination, pb_overwrite=False):
    """
    Function to download a file.

    :param pu_source:
    :param pu_destination:

    :return:
    :rtype str
    """

    # Image missing in ROMdb
    if pu_source is None:
        s_result = 'missing'

    elif (not pb_overwrite) and os.path.isfile(pu_destination):
        s_result = 'skipped'

    else:
        o_remote_file = urllib2.urlopen(pu_source)
        s_remote_data = o_remote_file.read()

        try:
            with open(pu_destination, 'wb') as o_file:
                o_file.write(s_remote_data)
                s_result = 'downloaded'
        except IOError:
            s_result = 'write_error'

    return s_result


if __name__ == '__main__':
    o_main_window = MainWindow()
