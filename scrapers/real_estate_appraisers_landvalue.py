__author__ = 'Sid'
#-*- encoding: utf-8 -*-

import requests, re, os, time
from glob import iglob
os.sys.path.append(r'C:\Users\Sid\Documents\GitHub\PhoneExtractor')
os.sys.path.append(r'C:\Python27\Scripts\Experiments\databases')
os.sys.path.append(r'C:\Users\Sid\Documents\GitHub\TableManager')
import canonization, export_classes
from lxml import html
import import_files


def get_charset_from_html(html_source, default_encoding='utf-8'):
    """
    :param html_source: HTML sourcepage
    :param default_encoding: Default encoding
    :return: charset if found, default_encoding otherwise
    """

    charset_xpath = '//meta[@charset]/@charset'
    tree = html.fromstring(html_source, parser=html.HTMLParser(encoding=default_encoding))
    charset_xpath_results = tree.xpath(charset_xpath)

    if charset_xpath_results:
        return charset_xpath_results[0]
    return default_encoding

# Download appraisers files
def download_appraiser_files(starting_id=1):
    """
    Download all pages with appraiser info
    """


    GET_URL = 'http://www.landvalue.org.il/index2.php?id=17&recordId={id}&lang=HEB'
    BASE_DIR = r'C:\Python27\Scripts\Experiments\databases\appraisers'


    if not os.path.exists(BASE_DIR):
        os.mkdir(BASE_DIR)

    response = requests.get(GET_URL.format(id=starting_id))
    html_encoding = get_charset_from_html(response.text)

    for appraiser_index in xrange(starting_id, 2000):
        # Try to get every appraiser

        time.sleep(2)  # So Server won't cut us off
        if appraiser_index % 150 == 0:
            print 'currently extracted appraiser:', appraiser_index

        response = requests.get(GET_URL.format(id=appraiser_index))

        if len(response.text) <= 16000:  # Empty appraiser
            continue

        current_appraiser_file = os.path.join(BASE_DIR, 'appraiser_landvalue{0}.html'.format(appraiser_index))
        with open(current_appraiser_file, 'wb') as output:
            output.write(response.text.encode('latin1'))  # No idea why its latin1, utf-8 doesnt work


# Downloaded files extraction
class Appraiser(object):
    attributes_ordered = [
                            'id', 'full_name', 'district', 'mobile', 'mobile_canonized',
                            'address_home', 'phone_home', 'phone_home_canonized', 'fax_home', 'fax_home_canonized',
                            'address_work', 'phone_work', 'phone_work_canonized', 'fax_work', 'fax_work_canonized',
                            'email', 'website', 'pic_url', 'facebook'
                         ]
    def __init__(self, appraiser_id, full_name=None, mobile=None, address_work=None, address_home=None,
                 phone_home=None, phone_work=None, fax_home=None, fax_work=None, website=None, email=None,
                 district=None, pic_url=None, facebook=None, canonizer=canonization.create_israeli_canonizer()):
        self._canonizer=canonizer
        self.id = appraiser_id
        self.full_name = full_name
        self.mobile = mobile
        self.mobile_canonized = ''
        self.phone_home = phone_home
        self.phone_home_canonized = ''
        self.phone_work = phone_work
        self.phone_work_canonized = ''
        self.fax_home = fax_home
        self.fax_home_canonized = ''
        self.fax_work = fax_work
        self.fax_work_canonized = ''
        self.email = email
        self.district = district
        self.address_work = address_work
        self.address_home = address_home
        self.website = website
        self.pic_url = pic_url
        self.facebook = facebook

    def __setattr__(self, name, value):
        """
        custom attributes setting
        canonize phone numbers while keeping original
        """
    
        if value is not None and name in ['phone_home', 'phone_work', 'mobile', 'fax_home', 'fax_work']:
            new_attr_name = "{0}_canonized".format(name)
            find_phones_regex = self._canonizer._country_phone.to_find_regex(strict=False, 
                                                                             optional_country=True, 
                                                                             canonized=False)
            matched_phones = find_phones_regex.finditer(value)
            if matched_phones:
                all_canonized_phones = set()
                for matched_phone in matched_phones:
                    # canonize each phone found 
                    phone = matched_phone.group('phone')
                    canonized_phones = self._canonizer.canonize(phone)
                    all_canonized_phones = all_canonized_phones.union(canonized_phones)
                setattr(self, new_attr_name, '|'.join(all_canonized_phones))

            super(Appraiser, self).__setattr__(name, value)  # Set original name and value

        elif name == 'email':
            if value is not None:
                value = value.lower()
            super(Appraiser, self).__setattr__(name, value)

        elif name == 'pic_url':
            if value is not None:
                value = "{website}/{path}".format(website="http/www.landvalue.org.il", path=value)
            super(Appraiser, self).__setattr__(name, value)

        else:
            super(Appraiser, self).__setattr__(name, value)


    def __str__(self):
        return self.full_name

    def __repr__(self):
        return self.full_name

def edit_string(src_string, html_encoding='utf-8'):
    """
    Removes white spaces and ':' at beginning and end.
    Replace consecutives whitespaces into a space

    finally, encode the string
    """

    cleaning_regex = re.compile(r'^[:\s]*(?P<value>.+?)[:\s]*$')
    temp_string = re.sub(r'\s+', ' ', src_string)  # Remove consecutive spaces
    match = cleaning_regex.search(temp_string)  # Clean whitespace and ':'
    if not match:
        return temp_string.encode(html_encoding)
    return match.group('value').encode(html_encoding)

def get_headers():
    """
    :return: Set containing all possible headers
    """

    # Xpaths for infos
    attribute_infos_xpath = '//td[contains(@id, "memberPage_") and not(contains(@id, "_col"))]/@id'
    attribute_phones_xpath = '//td/div[contains(@id, "memberPage_") and not(contains(@id, "_col"))]/@id'

    # Xpaths for first line
    attribute_header_xpath = '//div[@id="memberPage_topDetails"]/span/@class'

    file_paths = iglob(r'C:\Python27\Scripts\Experiments\databases\appraisers\appraiser_landvalue*')

    all_headers = set()

    for file_path in file_paths:

        with open(file_path, 'rb') as appraiser_file:
            tree = html.fromstring(appraiser_file.read())
            info_results = tree.xpath(attribute_infos_xpath)
            phone_results = tree.xpath(attribute_phones_xpath)
            header_results = tree.xpath(attribute_header_xpath)

            all_headers = all_headers.union(info_results)
            all_headers = all_headers.union(phone_results)
            all_headers = all_headers.union(header_results)

    return all_headers

def parse_appraiser_file(file_path, html_encoding='utf-8'):
    """
    :param file_path: path to file we want to parse an appraiser
    :param html_encoding: html encoding of file
    :return: Optometrist instance
    """

    # Xpaths for infos
    attribute_value_infos_xpath = '//td[contains(@id, "memberPage_") and not(contains(@id, "_col"))]'
    attribute_value_phones_xpath = '//td/div[contains(@id, "memberPage_") and not(contains(@id, "_col"))]'
    attibute_info_phone_xpath = './@id'
    value_info_phone_xpath = './div/text()'

    # Xpaths for first line
    attribute_value_header_xpath = '//div[@id="memberPage_topDetails"]/span'
    attribute_header_xpath = './@class'
    # No xpath for value, just text_content() the attribute_value_header_xpath results

    # Xpath for right-side info (facebook and pic)
    picture_url_xpath = '//td[@id="memberPage_col2"]//img/@src'
    facebook_url_xpath = '//td[@id="memberPage_col1"]//a/@href'



    appraiser_id_pattern = re.compile(r'(?P<id>\d+).html$')

    title_to_prop_dict = {'memberPage_cellphone': 'mobile', 'memberPage_district': 'district',
                          'memberPage_email': 'email', 'memberPage_homeAddress': 'address_home',
                          'memberPage_homeFax': 'fax_home', 'memberPage_homePhone': 'phone_home',
                          'memberPage_name': 'full_name', 'memberPage_siteUrl': 'website',
                          'memberPage_workAddress': 'address_work', 'memberPage_workFax': 'fax_work',
                          'memberPage_workPhone': 'phone_work'}

    appraiser_id_match = appraiser_id_pattern.search(file_path)
    if appraiser_id_match:
        appraiser_id = appraiser_id_match.group('id')
    else:
        appraiser_id = ''

    with open(file_path, 'rb') as appraiser_file:
        # Open it and parse

        current_appraiser = Appraiser(appraiser_id=appraiser_id)

        tree = html.fromstring(appraiser_file.read(), parser=html.HTMLParser(encoding='utf-8'))

        # Manual parsing
        picture_url_result = tree.xpath(picture_url_xpath)
        if picture_url_result:
            current_appraiser.pic_url = picture_url_result[0]

        facebook_url_result = tree.xpath(facebook_url_xpath)
        if facebook_url_result:
            current_appraiser.facebook = facebook_url_result[0]

        # Get All attribute values from all xpaths
        all_attribute_values = set()
        info_attribute_values = tree.xpath(attribute_value_infos_xpath)
        phone_attribute_values = tree.xpath(attribute_value_phones_xpath)

        all_attribute_values = all_attribute_values.union(info_attribute_values)
        all_attribute_values = all_attribute_values.union(phone_attribute_values)

        for attribute_value in all_attribute_values:
            attribute_result = attribute_value.xpath(attibute_info_phone_xpath)
            value_result = attribute_value.xpath(value_info_phone_xpath)

            if value_result:
                attribute = edit_string(attribute_result[0], html_encoding)
                value = edit_string(value_result[0], html_encoding)
                if attribute in title_to_prop_dict.keys():
                    actual_attribute = title_to_prop_dict[attribute]
                    setattr(current_appraiser, actual_attribute, value)
                else:
                    print 'COULD NOT FIND ATTRIBUTE FOR', attribute
            else:
                pass  # Simply means its an empty string

        # I know it's almost a duplicate, not important enough to write it better
        all_attribute_values = tree.xpath(attribute_value_header_xpath)
        for attribute_value in all_attribute_values:
            attribute_result = attribute_value.xpath(attribute_header_xpath)
            attribute = edit_string(attribute_result[0], html_encoding)
            value = edit_string(attribute_value.text_content(), html_encoding)
            if attribute in title_to_prop_dict.keys():
                actual_attribute = title_to_prop_dict[attribute]
                setattr(current_appraiser, actual_attribute, value)
            else:
                print 'COULD NOT FIND ATTRIBUTE FOR', attribute

    if current_appraiser.full_name:
        return current_appraiser
    return None

def parse_appraiser_files_gen(bulk_amount=200, html_encoding='utf-8'):
    """
    returns list of bulk_amount Lawyers 
    that were parsed
    """

    all_file_paths = iglob(r'C:\Python27\Scripts\Experiments\databases\appraisers\*')

    appraisers_lst = []

    for file_path in all_file_paths:
        # Loop over every lawyer file

        current_appraiser = parse_appraiser_file(file_path)
        if current_appraiser is not None:
            appraisers_lst.append(current_appraiser)

        if len(appraisers_lst) == bulk_amount:
            # Yield a list of bulk_amount appraisers
            yield appraisers_lst
            appraisers_lst = []

    yield appraisers_lst  # Final yield

def save_appraisers(bulk_amount=300):
    """
    Parse lawyer files and save them to an excel
    """

    appraisers_gen = parse_appraiser_files_gen(bulk_amount)
    file_path = export_classes.instances_to_file(appraisers_gen, instance_class=Appraiser)
    print 'DONE\n'
    return file_path


if __name__ == '__main__':
    #download_appraiser_files(87)
    #output_file_path = save_appraisers()
    output_file_path = r"C:\Python27\Scripts\Experiments\databases\Professional Associations\Appraiser_22-12-2015.xlsx"
    _, ext = os.path.splitext(output_file_path)
    # if next line is commented, it's because we want to edit the file before we import it
    import_files.file_to_db(output_file_path, 'appraisers_landvalue', file_src_ext=ext[1:])
    pass