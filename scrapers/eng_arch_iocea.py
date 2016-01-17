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
    tree = html.fromstring(html_source, parser=html.HTMLParser(encoding=default_encoding))
    charset_xpath_results = tree.xpath(charset_xpath)

    if charset_xpath_results:
        return charset_xpath_results[0]
    return default_encoding

# Download engineers files
def download_engineer_files(starting_id=1):
    """
    Download all pages with engineer info
    """


    GET_URL = 'http://iocea.org.il/Web/Chambers/MemberDisplay/Default.aspx?id={id}'
    BASE_DIR = r'C:\Python27\Scripts\Experiments\databases\engineers'


    if not os.path.exists(BASE_DIR):
        os.mkdir(BASE_DIR)

    response = requests.get(GET_URL.format(id=starting_id))
    html_encoding = get_charset_from_html(response.text)


    for engineer_index in xrange(starting_id, 4000):
        # Try to get every engineer

        time.sleep(0.2)  # So Server won't cut us off
        if engineer_index % 150 == 0:
            print 'currently extracted engineer:', engineer_index

        response = requests.get(GET_URL.format(id=engineer_index))

        if len(response.text) <= 102000:  # Empty engineer
            continue

        current_engineer_file = os.path.join(BASE_DIR, 'engineer_architect_{0}.html'.format(engineer_index))
        with open(current_engineer_file, 'wb') as output:
            output.write(response.text.encode(html_encoding))


# Downloaded files extraction
class Engineer(object):
    attributes_ordered = [
                            'id', 'association', 'full_name', 'phone', 'phone_canonized', 'mobile', 'mobile_canonized',
                            'fax', 'fax_canonized', 'email', 'address'
                         ]
    def __init__(self, engineer_id, full_name=None, mobile=None, phone=None, fax=None, address=None,
                 email=None, association=None, canonizer=canonization.create_israeli_canonizer()):
        self._canonizer=canonizer
        self.id = engineer_id
        self.full_name = full_name
        self.phone = phone
        self.phone_canonized = ''
        self.mobile = mobile
        self.mobile_canonized = ''
        self.fax = fax
        self.fax_canonized = ''
        self.email = email
        self.association = association
        self.address = address

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

            super(Engineer, self).__setattr__(name, value)  # Set original name and value

        elif name == 'email':
            if value is not None:
                value = value.lower()
            super(Engineer, self).__setattr__(name, value)

        else:
            super(Engineer, self).__setattr__(name, value)


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
    attribute_value_xpath = '//div[contains(@class,"displayRow")]//img/@src'

    file_paths = iglob(r'C:\Python27\Scripts\Experiments\databases\engineers\*')

    all_headers = set()

    for file_path in file_paths:

        with open(file_path, 'rb') as engineer_file:
            tree = html.fromstring(engineer_file.read())
            all_headers = all_headers.union(tree.xpath(attribute_value_xpath))
    return all_headers

def parse_engineer_file(file_path, html_encoding='utf-8'):
    """
    :param file_path: path to file we want to parse an engineer
    :param html_encoding: html encoding of file
    :return: Optometrist instance
    """

    attribute_value_xpath = '//div[contains(@class,"displayRow")]'
    attribute_label_xpath = './/img/@src'
    value_xpath = './div[contains(@class, "label")]'

    association_xpath = '//span[@id="ctl00_ContentPlaceHolderMiddle_lblChambers"]/text()'

    # There can be possibly 2 people written on same card, for example engineer_id=1
    engineer_owners_xpath = '//table[@id="ctl00_ContentPlaceHolderMiddle_gvOwners"]/tr'
    engineer_owners_name = './/div[@class="rightDiv"]/span/text()'
    engineer_owners_phone = './/div[@class="leftDiv"]/span/text()'



    engineer_id_pattern = re.compile(r'(?P<id>\d+).html$')

    title_to_prop_dict = {
            '/Rsrc/Images/email.jpg': 'email',
            '/Rsrc/Images/fax.jpg': 'fax',
            '/Rsrc/Images/house.jpg': 'address',
            '/Rsrc/Images/phone.jpg': 'phone',
            '/Rsrc/Images/web.jpg': 'website'
    }

    engineer_id_match = engineer_id_pattern.search(file_path)
    if engineer_id_match:
        engineer_id = engineer_id_match.group('id')
    else:
        engineer_id = ''

    with open(file_path, 'rb') as engineer_file:
        # Open it and parse

        current_engineer = Engineer(engineer_id=engineer_id)

        tree = html.fromstring(engineer_file.read(), parser=html.HTMLParser(encoding=html_encoding))

        association_results = tree.xpath(association_xpath)
        if association_results:
            current_engineer.association = edit_string(association_results[0], html_encoding)

        # Get all owners
        owners_results = tree.xpath(engineer_owners_xpath)
        owner_names = set()
        owner_mobiles = set()
        for owner in owners_results:
            owner_name = edit_string(owner.xpath(engineer_owners_name)[0], html_encoding)
            owner_phone_results = owner.xpath(engineer_owners_phone)
            if owner_phone_results:
                owner_phone = edit_string(owner_phone_results[0], html_encoding)
                owner_mobiles.add(owner_phone)

            owner_names.add(owner_name)

        current_engineer.full_name = '|'.join(owner_names)
        current_engineer.mobile = '|'.join(owner_mobiles)

        attribute_values = tree.xpath(attribute_value_xpath)[2:]  # two firsy attributes have been written already

        for attribute_value in attribute_values:
            attribute_result = attribute_value.xpath(attribute_label_xpath)
            value_result = attribute_value.xpath(value_xpath)

            attribute = edit_string(attribute_result[0], html_encoding)
            value = edit_string(value_result[0].text_content(), html_encoding)
            if attribute in title_to_prop_dict.keys():
                actual_attribute = title_to_prop_dict[attribute]
                setattr(current_engineer, actual_attribute, value)
    return current_engineer

def parse_engineer_files_gen(bulk_amount=200, html_encoding='utf-8'):
    """
    returns list of bulk_amount Lawyers
    that were parsed
    """

    all_file_paths = iglob(r'C:\Python27\Scripts\Experiments\databases\engineers\*')

    engineers_lst = []

    for file_path in all_file_paths:
        # Loop over every lawyer file

        current_engineer = parse_engineer_file(file_path)
        engineers_lst.append(current_engineer)

        if len(engineers_lst) == bulk_amount:
            # Yield a list of bulk_amount engineers
            yield engineers_lst
            engineers_lst = []

    yield engineers_lst  # Final yield

def save_engineers(bulk_amount=300):
    """
    Parse lawyer files and save them to an excel
    """

    engineers_gen = parse_engineer_files_gen(bulk_amount)
    file_path = export_classes.instances_to_file(engineers_gen, instance_class=Engineer)
    print 'DONE\n'
    return file_path


if __name__ == '__main__':
    #download_engineer_files(3600)
    #output_file_path = save_engineers()
    output_file_path = r"C:\Python27\Scripts\Experiments\databases\Professional Associations\Engineer_21-12-2015.xlsx"
    _, ext = os.path.splitext(output_file_path)
    # if next line is commented, it's because we want to edit the file before we import it
    import_files.file_to_db(output_file_path, 'engineers_architects_iocea', file_src_ext=ext[1:])
    pass