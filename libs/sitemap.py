import chardet
import lxml.etree
import random
import re
import requests


def _get_sitemaps(pu_sitemap_url):
    """
    Big sitemaps are divided into small .xml files and one single sitemap.xml pointing to all of them. This function
    returns a list of all the xml files to read. If the sitemap.xml is not pointing to any other file, the function will
    simply return a list pointing to the sitemap.xml file itself.

    Reading .xml files with sitemap names add another level of complexity. Read the information below:

        - https://stackoverflow.com/questions/31276001/parse-xml-sitemap-with-python
        - https://stackoverflow.com/questions/31177707/parsing-xml-containing-default-namespace-to-get-an-element-value-using-lxml/31178720

    To avoid the extra complexity, we simply access the .xml elements by position. Not very robust but the code is
    simpler and I assume that the format of the sitemap is pretty much standardised.

    :param pu_sitemap_url:
    :type pu_sitemap_url: unicode

    :return: A list of xml files to read.
    :rtype list[unicode]
    """

    o_request = requests.get(pu_sitemap_url)
    s_xml = o_request.content
    s_enc = chardet.detect(s_xml)['encoding']
    u_xml = s_xml.decode(s_enc)

    u_xml = _remove_namespace(u_xml)

    o_root = lxml.etree.fromstring(u_xml.encode('utf8'))

    # [1/?] We try to get all the actual sitemap.xml files contained in this "index" of sitemaps
    #-------------------------------------------------------------------------------------------
    lu_sitemaps = []

    for o_elem in o_root.findall(u'sitemap/loc'):
        lu_sitemaps.append(o_elem.text)

    # [2/?] If no actual sitemaps are found, it means the file itself is a proper sitemap
    #------------------------------------------------------------------------------------
    if not lu_sitemaps:
        lu_sitemaps.append(pu_sitemap_url)

    return lu_sitemaps


def _get_urls(plu_sitemap_urls):
    """
    Function to obtain a list of urls from a list of sitemap.xml files.

    :param plu_sitemap_urls: List of sitemap files.
    :type plu_sitemap_urls: list[unicode]

    :return: A list of URLs contained in the sitemap.
    :rtype list[unicode]
    """

    lu_urls = []
    for u_sitemap_url in plu_sitemap_urls:
        o_request = requests.get(u_sitemap_url)
        s_xml = o_request.content
        s_enc = chardet.detect(s_xml)['encoding']
        u_xml = s_xml.decode(s_enc)
        u_xml = _remove_namespace(u_xml)

        o_root = lxml.etree.fromstring(u_xml.encode('utf8'))

        for i_elem, o_elem in enumerate(o_root.findall(u'url/loc')):
            lu_urls.append(o_elem.text)

    random.shuffle(lu_urls)

    return lu_urls


def _remove_namespace(pu_xml_string):
    """
    Function to remove the namespace from xml strings. That way the parsing is much simpler.

    e.g. {http://www.sitemaps.org/schemas/sitemap/0.9}url => url

    :param pu_xml_string: A string containing a namespace at the beginning.
    :type pu_xml_string: unicode

    :return:
    :rtype
    """

    s_pattern = r' xmlns="[^"]+"'
    u_out = re.sub(s_pattern, u'', pu_xml_string, count=1)
    return u_out


def get_urls(pu_sitemap_url):
    """
    Function to get all the URLs stored in a sitemap.xml
    :param pu_sitemap_url:
    :return:
    """
    lu_sitemaps = _get_sitemaps(pu_sitemap_url)
    lu_urls = _get_urls(lu_sitemaps)
    return lu_urls