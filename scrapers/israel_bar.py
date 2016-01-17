# -*- encoding: utf-8 -*-

import requests, os, time
from glob import iglob
from lxml import html
import re, canonization

os.sys.path.append(r'C:\Python27\Scripts\Experiments\databases')
import export_classes

# Download lawyer files
def download_lawyer_files(starting_id=1):
    """
    Download all pages with lawyers info
    """

    headers = {
                'Origin': 'http//www.israelbar.org.il', 
                'X-Requested-With': 'XMLHTTPRequest',  # Without this header, response will be empty
                'Connection': 'keep-alive', 
                'Referer': 'http://www.israelbar.org.il/lawyer_list.asp?sent=1', 
                'Content-Type': 'application/x-www-form-urlencoded'
            }

    POST_URL = 'http://www.israelbar.org.il/asp_include/getLawyerAjax.asp'
    DATA_TEMPLATE = "lawyerId={0}"
    BASE_DIR = r'C:\Python27\Scripts\Experiments\databases\lawyers'

    for lawyer_index in xrange(starting_id, 40000):
        # Try to get every lawyer

        time.sleep(1.1)  # So Server won't cut us off
        if lawyer_index % 200 == 0:
            print 'currently extracted lawyer:', lawyer_index

        response = requests.post(url=POST_URL, 
                      data=DATA_TEMPLATE.format(lawyer_index),
                      headers=headers)

        if 1850 < len(response.text) < 1890 or 235 < len(response.text) < 250:
            # Inexistant or doesn't exist in current DB
            continue

        current_lawyer_file = os.path.join(BASE_DIR, 'laywer_{0}.html'.format(lawyer_index))
        with open(current_lawyer_file, 'wb') as output:
            output.write(response.text.encode('utf-8'))


# Downloaded files extraction
class Lawyer(object):
    attributes_ordered = ['lawyer_id', 'name', 'specialty', 'phone', 'phone_canonized', 'mobile', 'mobile_canonized', 'fax', 'fax_canonized', 'email', 'address', 'po_box', 'language', 'notary']
    def __init__(self, lawyer_id, name=None, specialty=None, phone=None, mobile=None, fax=None,
                 email=None, address=None, po_box=None, language=None, notary=None, 
                 canonizer=canonization.create_israeli_canonizer()):
        self._canonizer=canonizer
        self.lawyer_id = lawyer_id
        self.name = name
        self.specialty = specialty
        self.phone = phone
        self.phone_canonized = None
        self.mobile = mobile
        self.mobile_canonized = None
        self.fax = fax
        self.fax_canonized = None
        self.email = email
        self.address = address
        self.po_box = po_box
        self.language = language
        self.notary = notary

    def __setattr__(self, name, value):
        """
        custom attributes setting
        canonize phone numbers while keeping original
        """
    
        if value and name in ['phone', 'mobile', 'fax']:
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

            super(Lawyer, self).__setattr__(name, value)  # Set original name and value

        elif name == 'notary':
            """
            Default value is None and then evalyates to False
            if he is a notary, it will be parsed from the html as an empty string (if he isnt, it wont event show up),
            which will evaluate to True
            """
            if value is None:
                super(Lawyer, self).__setattr__(name, False)
            else:
                super(Lawyer, self).__setattr__(name, True)
        else:
            super(Lawyer, self).__setattr__(name, value)  # Set original name and value


    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

def edit_string(src_string, encoding='utf-8'):
    """
    Removes white spaces and ':' at beginning and end.
    Replace consecutives whitespaces into a space

    finally, encode the string
    """
    cleaning_regex = re.compile(r'^[:\s]*(?P<value>.+?)[:\s]*$')
    temp_string = re.sub(r'\s+', ' ', src_string)  # Remove consecutive spaces
    match = cleaning_regex.search(temp_string)  # Clean whitespace and ':'
    if not match:
        return temp_string.encode(encoding)
    return match.group('value').encode(encoding)



def get_all_headers(html_encoding='utf-8'):
    """
    Find header names from all the files
    that were downloaded
    """

    all_file_paths = iglob(r'C:\Python27\Scripts\Experiments\databases\lawyers\*')



    header_item_xpath = 'div[contains(@class,"reference_item")]'
    item_title_xpath = './div[@class="title"]/text()'
    item_value_xpath = './span/text()'

    header_names = set()

    current_file = 0

    for file_path in all_file_paths:
        with open(file_path, 'rb') as lawyer_file:
            html_tree = html.fromstring(lawyer_file.read(), parser=html.HTMLParser(encoding=html_encoding))
            all_headers = html_tree.xpath(header_item_xpath)
            for header in all_headers:
                title = edit_string(header.xpath(item_title_xpath)[0], html_encoding)
                values = header.xpath(item_value_xpath)
                values = map(lambda x: edit_string(x), values)
                header_names.add(title)
            current_file += 1
            if current_file >= 15000:
                break
    return header_names

def parse_lawyer_files_gen(bulk_amount=200, html_encoding='utf-8'):
    """
    returns list of bulk_amount Lawyers 
    that were parsed
    """

    all_file_paths = iglob('C:\Python27\Scripts\Experiments\databases\lawyers\*')

    name_xpath = '//div[@class="screen_name"]//span/text()'

    header_item_xpath = 'div[contains(@class,"reference_item")]'
    item_title_xpath = './div[@class="title"]/text()'
    item_value_xpath = './span'

    title_to_prop_dict = {
            'טלפון': 'phone',
            'פקס': 'fax',
            'נייד': 'mobile',
            'תחום עיסוק': 'specialty',
            'כתובת דוא"ל': 'email',
            'כתובת': 'address',
            'ת.ד': 'po_box',
            'שפה': 'language',
            'נוטריון': 'notary'
    }

    lawyers_lst = []
    lawyer_id_pattern = re.compile(r'laywer_(?P<id>\d+).html$')

    for file_path in all_file_paths:
        # Loop over every lawyer file


        #  Look for lawyer_id in 
        lawyer_id_match = lawyer_id_pattern.search(file_path)
        if lawyer_id_match:
            lawyer_id = lawyer_id_match.group('id')
        else:
            lawyer_id = ''

        with open(file_path, 'rb') as lawyer_file:
            # Open it and parse

            html_tree = html.fromstring(lawyer_file.read(), parser=html.HTMLParser(encoding=html_encoding))

            name = edit_string(html_tree.xpath(name_xpath)[0], html_encoding)  #Lawyer name
            current_lawyer = Lawyer(lawyer_id=lawyer_id, name=name)

            all_headers = html_tree.xpath(header_item_xpath)
            for header in all_headers:
                # Loop over every attribute of the lawyer found in HTML file
                attribute_name = edit_string(header.xpath(item_title_xpath)[0], html_encoding)

                attribute_values = header.xpath(item_value_xpath)
                attribute_value = ' '.join(map(lambda x: edit_string(x.text_content()), attribute_values))  # join to 1 string

                # Get actual attribute name, and set it to the given value
                actual_attribute_name = title_to_prop_dict[attribute_name]
                setattr(current_lawyer, actual_attribute_name, attribute_value)

            lawyers_lst.append(current_lawyer)

            if len(lawyers_lst) == bulk_amount:
                # Yield a list of bulk_amount lawyers
                yield lawyers_lst
                lawyers_lst = []

    yield lawyers_lst  # Final yield


def save_lawyers(bulk_amount=300):
    """
    Parse lawyer files and save them to an excel
    """

    lawyers_gen = parse_lawyer_files_gen(bulk_amount)
    export_classes.instances_to_file(lawyers_gen, instance_class=Lawyer)
    print 'DONE\n'


def print_new_name(headers):

    title_to_prop_dict = {
            'טלפון': 'phone',
            'פקס': 'fax',
            'נייד': 'mobile',
            'תחום עיסוק': 'specialty',
            'כתובת דוא"ל': 'email',
            'כתובת': 'address',
            'ת.ד': 'po_box',
            'שפה': 'language',
            'נוטריון': 'notary'
    }

    for header in headers:
        print "{0} is {1}".format(header, title_to_prop_dict[header])

if __name__ == '__main__':
    download_lawyer_files()
    save_lawyers()

