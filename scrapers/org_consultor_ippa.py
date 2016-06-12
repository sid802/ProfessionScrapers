__author__ = 'Sid'
# -*- encoding: utf-8 -*-

import requests, re, os, time
from glob import iglob

os.sys.path.append(r'C:\Users\Sid\Documents\GitHub\PhoneExtractor')
os.sys.path.append(r'C:\Users\Sid\Documents\GitHub\TableManager')
import canonization, export_classes
from lxml import html
import import_files

cleaning_regex = re.compile(r'^\s*(?P<value>.+)\s*$', re.MULTILINE)
secondary_cleaning_regex = re.compile(r'(\s*\|\s*)+')

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


# Download consultors files
def download_consultor_files(starting_id=1):
    """
    Download all pages with consultor info
    """

    GET_URL = 'http://www.ippa.org.il/index.aspx?id=4152&userID={id}'
    BASE_DIR = r'C:\Python27\Scripts\Experiments\databases\consultors'

    if not os.path.exists(BASE_DIR):
        os.mkdir(BASE_DIR)

    response = requests.get(GET_URL.format(id=starting_id))
    html_encoding = get_charset_from_html(response.text)

    for consultor_index in xrange(starting_id, 4900):
        # Try to get every consultor
        time.sleep(1)  # So Server won't cut us off
        if consultor_index % 150 == 0:
            print u'currently extracted consultor:', consultor_index

        response = requests.get(GET_URL.format(id=consultor_index))

        if len(response.text) <= 291900:  # Empty consultor
            continue

        current_consultor_file = os.path.join(BASE_DIR, 'consultor{0}.html'.format(consultor_index))
        with open(current_consultor_file, 'wb') as output:
            output.write(response.text.encode('utf-8'))


# Downloaded files extraction
class OrgConsultor(object):
    attributes_ordered = [
        'id', 'full_name', 'phone', 'phone_canonized', 'mobile', 'mobile_canonized', 'fax',
        'fax_canonized',
        'email', 'website', 'city', 'address', 'expertise', 'practicing_areas', 'areas', 'customers',
        'case_studies', 'about', 'publishes', 'pic_url'
    ]

    def __init__(self, consultor_id, full_name=None, mobile=None, phone=None, fax=None, website=None, email=None,
                 city=None, address=None, pic_url=None, about=None, case_studies=None, expertise=None, customers=None,
                 publishes=None, areas=None, practicing_areas=None, canonizer=canonization.create_israeli_canonizer()):
        self._canonizer = canonizer
        self.id = consultor_id
        self.full_name = full_name
        self.mobile = mobile
        self.mobile_canonized = ''
        self.phone = phone
        self.phone_canonized = ''
        self.fax = fax
        self.fax_canonized = ''
        self.email = email
        self.city = city
        self.address = address
        self.website = website
        self.pic_url = pic_url
        self.case_studies = case_studies
        self.expertise = expertise
        self.customers = customers
        self.areas = areas
        self.practicing_areas = practicing_areas
        self.publishes = publishes
        self.about = about

    def __setattr__(self, name, value):
        """
        custom attributes setting
        canonize phone numbers while keeping original
        """

        if value is not None and name in ['phone', 'mobile', 'fax']:
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

            super(OrgConsultor, self).__setattr__(name, value)  # Set original name and value

        elif name == 'email':
            if value is not None:
                value = value.lower()
            super(OrgConsultor, self).__setattr__(name, value)

        elif name == 'pic_url':
            if value is not None:
                value = u"{website}/{path}".format(website=u"http://www.ippa.org.il/", path=value)
            super(OrgConsultor, self).__setattr__(name, value)

        else:
            if len(value) >= 1000:
                value = 'TOO LONG'
            super(OrgConsultor, self).__setattr__(name, value)

    def __unicode__(self):
        return unicode(self.full_name)

    def __repr__(self):
        return unicode(self.full_name)

def clean_string(src_string):
    """
    Removes white spaces and ':' at beginning and end.
    Replace consecutives whitespaces into a space
    """

    global cleaning_regex, secondary_cleaning_regex

    if len(src_string) == 0:
        return src_string

    cleaned_string = cleaning_regex.search(src_string).group('value')  # Clean whitespace and ':'
    temp_string = secondary_cleaning_regex.sub(u'|', cleaned_string)
    temp_string = re.sub(r'\s+', u' ', temp_string)  # Remove consecutive spaces
    return temp_string

def edit_string(src_string, html_encoding='utf-8'):
    """
    finally, encode the string
    """
    tmp_string = clean_string(src_string)
    return tmp_string.encode(html_encoding)


def get_headers():
    """
    :return: Set containing all possible headers
    """

    # Xpaths for infos
    infos_xpath = '//div[@class="profileColumn"]/div[contains(@class, "item")]/'
    boxes_xpath = '//div[contains(@class,"commonBox")]/h2/text()'

    file_paths = iglob(r'C:\Python27\Scripts\Experiments\databases\consultors\*')

    all_headers = set()

    for file_path in file_paths:

        with open(file_path, 'rb') as consultor_file:
            tree = html.fromstring(consultor_file.read())
            info_results = tree.xpath(infos_xpath)
            boxes_results = tree.xpath(boxes_xpath)

            all_headers = all_headers.union(info_results)
            all_headers = all_headers.union(boxes_results)

    return all_headers


def parse_consultor_file(file_path, html_encoding='utf-8'):
    """
    :param file_path: path to file we want to parse an consultor
    :param html_encoding: html encoding of file
    :return: Optometrist instance
    """

    # Xpaths for infos
    name_xpath = '//div[@class="name"]/text()'
    picture_xpath = '//div[@class="personBox"]/div/img/@src'

    attribute_infos_xpath = '//div[@class="profileColumn"]/div[contains(@class, "item") and contains(@style, "block")]'
    attribute_xpath = './@class'  # Relative to attribute_infos_xpath
    label_xpath = './label'
    info_xpath = './span'  # Relative to attribute_infos_xpath

    boxes_xpath = '//div[contains(@class,"commonBox")]'
    box_attribute_xpath = './h2/text()'  # Relative to boxes_xpath
    box_info_xpath = './div'  # Relative to boxes_xpath

    consultor_id_pattern = re.compile(r'(?P<id>\d+).html$')

    title_to_prop_dict = {u'adress': 'address', u'cellular': 'mobile',
                          u'city': 'city', u'email': 'email', u'phone': 'phone', u'fax': 'fax',
                          u'Case Study': 'case_studies', u'אודותי': 'about', u'כתובת האתר': 'website',
                          u'פרסומים': 'publishes',
                          u'רשימת לקוחות': 'customers', u'תחומי היתמחות': 'expertise', u'תחומי עיסוק': 'practicing_areas',
                          u'תחומים': 'areas'}

    consultor_id_match = consultor_id_pattern.search(file_path)

    if consultor_id_match:
        consultor_id = consultor_id_match.group('id')
    else:
        consultor_id = ''

    with open(file_path, 'rb') as consultor_file:
        # Open it and parse

        current_consultor = OrgConsultor(consultor_id=consultor_id)

        tree = html.fromstring(consultor_file.read(), parser=html.HTMLParser(encoding=html_encoding))

        # Manual parsing
        picture_url_result = tree.xpath(picture_xpath)
        if picture_url_result:
            current_consultor.pic_url = unicode(picture_url_result[0])

        name_result = tree.xpath(name_xpath)
        if name_result:
            current_consultor.full_name = unicode(name_result[0])

        # Get All attribute values from all xpaths
        info_attribute_values = tree.xpath(attribute_infos_xpath)

        for attribute_value in info_attribute_values:
            attribute_result = attribute_value.xpath(attribute_xpath)
            value_result = attribute_value.xpath(info_xpath)

            if value_result:
                attribute = unicode(attribute_result[0].split()[1])


                value = value_result[0].text_content()

                if len(attribute_value.xpath(label_xpath)) == 0:
                    # <span>ATTRIBUTE: VALUE</span> style
                    value_result_match = re.search(r'^(?:.*?)\:\s*(?P<value>.*?)$', value, re.MULTILINE)
                    if value_result_match:
                        value = value_result_match.group('value')

                value = unicode(value)
                if attribute in title_to_prop_dict.keys():
                    actual_attribute = title_to_prop_dict[attribute]
                    setattr(current_consultor, actual_attribute, value)
                else:
                    print 'COULD NOT FIND ATTRIBUTE FOR', attribute
            else:
                pass  # Simply means its an empty string

        boxes_results = tree.xpath(boxes_xpath)
        for box_atribute_value in boxes_results:
            attribute_result = box_atribute_value.xpath(box_attribute_xpath)
            value_result = box_atribute_value.xpath(box_info_xpath)

            if value_result:
                attribute = unicode(attribute_result[0])
                value = unicode(value_result[0].text_content())
                value = clean_string(value)
                if attribute in title_to_prop_dict.keys():
                    actual_attribute = title_to_prop_dict[attribute]
                    setattr(current_consultor, actual_attribute, value)
                else:
                    if attribute != u'פרטי התקשרות':
                        print 'COULD NOT FIND ATTRIBUTE FOR', attribute
            else:
                pass  # Simply means its an empty string


    if current_consultor.full_name is not None:
        return current_consultor
    return None


def parse_consultor_files_gen(bulk_amount=200, html_encoding='utf-8'):
    """
    returns list of bulk_amount Lawyers 
    that were parsed
    """

    all_file_paths = iglob(r'C:\Python27\Scripts\Experiments\databases\consultors\*')

    consultors_lst = []

    for file_path in all_file_paths:
        # Loop over every lawyer file

        current_consultor = parse_consultor_file(file_path)
        if current_consultor is not None:
            consultors_lst.append(current_consultor)

        if len(consultors_lst) == bulk_amount:
            # Yield a list of bulk_amount consultors
            yield consultors_lst
            consultors_lst = []

    yield consultors_lst  # Final yield


def save_consultors(bulk_amount=300):
    """
    Parse lawyer files and save them to an excel
    """

    consultors_gen = parse_consultor_files_gen(150)
    file_path = export_classes.instances_to_file(consultors_gen, instance_class=OrgConsultor)
    print 'DONE\n'
    return file_path


if __name__ == '__main__':
    #download_consultor_files(10)
    output_file_path = save_consultors()
    #output_file_path = r"C:\Python27\Scripts\Experiments\databases\Professional Associations\consultor_22-12-2015.xlsx"
    #_, ext = os.path.splitext(output_file_path)
    # if next line is commented, it's because we want to edit the file before we import it
    #import_files.file_to_db(output_file_path, 'consultors_landvalue', file_src_ext=ext[1:])
    pass