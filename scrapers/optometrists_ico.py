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

def get_charset_from_html(html_source, default_encoding='UTF-8'):
    """
    :param html_source: HTML sourcepage
    :param default_encoding: Default encoding
    :return: charset if found, default_encoding otherwise
    """

    charset_xpath = '//meta[@charset]/@charset'
    tree = html.fromstring(html_source)
    charset_xpath_results = tree.xpath(charset_xpath)

    if charset_xpath_results:
        return charset_xpath_results[0]
    return default_encoding

# Download optometrists files
def download_optometrist_files(starting_id=1):
    """
    Download all pages with optometrist info
    """


    GET_URL = 'http://www.ico.org.il/index.php?option=com_comprofiler&user={id}'
    BASE_DIR = r'C:\Python27\Scripts\Experiments\databases\optometrists'


    if not os.path.exists(BASE_DIR):
        os.mkdir(BASE_DIR)

    response = requests.get(GET_URL.format(id=starting_id))
    html_encoding = get_charset_from_html(response.text)


    for optometrist_index in xrange(starting_id, 500):
        # Try to get every optometrist

        time.sleep(0.2)  # So Server won't cut us off
        if optometrist_index % 50 == 0:
            print 'currently extracted optometrist:', optometrist_index

        response = requests.get(GET_URL.format(id=optometrist_index))

        if len(response.text) <= 24000:  # Empty optometrist
            continue

        current_optometrist_file = os.path.join(BASE_DIR, 'optometrist_{0}.html'.format(optometrist_index))
        with open(current_optometrist_file, 'wb') as output:
            output.write(response.text.encode(html_encoding))


# Downloaded files extraction
class Optometrist(object):
    attributes_ordered = [
                            'optometrist_id', 'permit_id', 'full_name', 'first_name', 'last_name', 'birth_date',
                            'phone', 'phone_canonized', 'mobile', 'mobile_canonized', 'address', 'website',
                            'job_kind', 'sign_up_date', 'last_connection_date', 'watches', 'pic_url'
                         ]
    def __init__(self, optometrist_id, full_name=None, first_name=None, last_name=None, permit_id=None,
                 job_kind=None, birth_date=None, phone=None, mobile=None, address=None, website=None,
                sign_up_date=None, last_connection_date=None, watches=None, pic_url=None,
                 canonizer=canonization.create_israeli_canonizer()):
        self._canonizer=canonizer
        self.optometrist_id = optometrist_id
        self.full_name = full_name
        self.first_name = first_name
        self.last_name = last_name
        self.permit_id = permit_id
        self.job_kind = job_kind
        self.birth_date = birth_date
        self.phone = phone
        self.phone_canonized = ''
        self.mobile = mobile
        self.mobile_canonized = ''
        self.address = address
        self.website = website
        self.pic_url = pic_url
        self.sign_up_date = sign_up_date
        self.last_connection_date = last_connection_date
        self.watches = watches

    def __setattr__(self, name, value):
        """
        custom attributes setting
        canonize phone numbers while keeping original
        """
    
        if value is not None and name in ['phone', 'mobile']:
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

            super(Optometrist, self).__setattr__(name, value)  # Set original name and value

        else:
            super(Optometrist, self).__setattr__(name, value)


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

def get_all_headers(html_encoding='utf-8'):
    """
    Find header names from all the files
    that were downloaded
    """

    all_file_paths = iglob(r'C:\Python27\Scripts\Experiments\databases\optometrists\*')

    item_value_regex = re.compile(r'\<strong\>(?P<attribute>.+?)\<\/strong\>(?P<value>.*?)\<br\s\/\>')

    header_names = set()

    for file_path in all_file_paths:
        with open(file_path, 'rb') as optometrist_file:

            attribute_values = item_value_regex.finditer(optometrist_file.read())

            for attribute_value in attribute_values:
                # Values/attributes are ALREADY encoded in UTF-8
                attribute = edit_string(attribute_value.group('attribute'))
                header_names.add(attribute)

    return header_names

def parse_optometrist_file(file_path, html_encoding='utf-8'):
    """
    :param file_path: path to file we want to parse an optometrist
    :param html_encoding: html encoding of file
    :return: Optometrist instance
    """

    attribute_value_xpath = '//tr[contains(@class,"sectiontableentry")]'
    attribute_xpath = './td[@class="titleCell"]/label/text()'
    value_xpath = './td[@class="fieldCell"]'

    pic_url_xpath = '//tr[contains(@class, "cbavatar_tr")]//img/@src'
    optometrist_id_pattern = re.compile(r'(?P<id>\d+).html$')

    title_to_prop_dict = {
            'צפיות': 'watches',
            'נרשם לאתר': 'sign_up_date',
            'חיבור אחרון': 'last_connection_date',
            'שם פרטי': 'first_name',
            'שם משפחה': 'last_name',
            'מספר רישיון': 'permit_id',
            'סוג עובד': 'job_kind',
            'תאריך לידה': 'birth_date',
            'טלפון': 'phone',
            'טלפון נייד': 'mobile',
            'כתובת': 'address',
            'אתר אינטרנט': 'website',
    }

    optometrist_id_match = optometrist_id_pattern.search(file_path)
    if optometrist_id_match:
        optometrist_id = optometrist_id_match.group('id')
    else:
        optometrist_id = ''

    with open(file_path, 'rb') as optometrist_file:
        # Open it and parse

        current_optometrist = Optometrist(optometrist_id=optometrist_id)

        tree = html.fromstring(optometrist_file.read())

        attribute_values = tree.xpath(attribute_value_xpath)
        pic_url_results = tree.xpath(pic_url_xpath)
        if pic_url_results and not pic_url_results[0].endswith('nophoto_n.png'):
            current_optometrist.pic_url = pic_url_results[0]

        for attribute_value in attribute_values:
            attribute_result = attribute_value.xpath(attribute_xpath)
            value_result = attribute_value.xpath(value_xpath)
            if value_result and not attribute_result:
                # Full Name doesn't have an attribute in source file
                current_optometrist.full_name = edit_string(value_result[0].text_content(), html_encoding)
            elif attribute_result and value_result:
                attribute = edit_string(attribute_result[0], html_encoding)
                value = edit_string(value_result[0].text_content(), html_encoding)
                if attribute in title_to_prop_dict.keys():
                    actual_attribute = title_to_prop_dict[attribute]
                    setattr(current_optometrist, actual_attribute, value)
    return current_optometrist

def parse_optometrist_files_gen(bulk_amount=200, html_encoding='utf-8'):
    """
    returns list of bulk_amount Lawyers 
    that were parsed
    """

    all_file_paths = iglob(r'C:\Python27\Scripts\Experiments\databases\optometrists\*')

    optometrists_lst = []

    for file_path in all_file_paths:
        # Loop over every lawyer file

        current_optometrist = parse_optometrist_file(file_path)
        optometrists_lst.append(current_optometrist)

        if len(optometrists_lst) == bulk_amount:
            # Yield a list of bulk_amount optometrists
            yield optometrists_lst
            optometrists_lst = []

    yield optometrists_lst  # Final yield

def save_optometrists(bulk_amount=300):
    """
    Parse lawyer files and save them to an excel
    """

    optometrists_gen = parse_optometrist_files_gen(bulk_amount)
    file_path = export_classes.instances_to_file(optometrists_gen, instance_class=Optometrist)
    print 'DONE\n'
    return file_path


if __name__ == '__main__':
    #output_file_path = save_optometrists()
    output_file_path = r"C:\Python27\Scripts\Experiments\databases\Professional Associations\Optometrist_20-12-2015.xlsx"
    _, ext = os.path.splitext(output_file_path)
    # if next line is commented, it's because we want to edit the file before we import it
    import_files.file_to_db(output_file_path, 'optometrists_ico', file_src_ext=ext[1:])