#-*- encoding: utf-8 -*-

import requests, re, os, time
from glob import iglob
os.sys.path.append(r'C:\Users\Sid\Documents\GitHub\PhoneExtractor')
os.sys.path.append(r'C:\Python27\Scripts\Experiments\databases')
import canonization, export_classes

# Download lawyer files
def download_tax_consultor_files(starting_id=14500):
    """
    Download all pages with tax_consultor info
    """


    GET_URL = 'http://www.ymas.org.il/consultantsPrint?c=;{id}'
    BASE_DIR = r'C:\Python27\Scripts\Experiments\databases\tax consultors'

    if not os.path.exists(BASE_DIR):
    	os.mkdir(BASE_DIR)

    for consultor_index in xrange(starting_id, 15600):
        # Try to get every tax consultor

        time.sleep(0.2)  # So Server won't cut us off
        if consultor_index % 200 == 0:
            print 'currently extracted consultor:', consultor_index

        response = requests.get(GET_URL.format(id=consultor_index))

        if 'strong' not in response.text:  # Strong tag
        	continue

        current_consultor_file = os.path.join(BASE_DIR, 'consultor_{0}.html'.format(consultor_index))
        with open(current_consultor_file, 'wb') as output:
            output.write(response.text.encode('utf-8'))


# Downloaded files extraction
class TaxConsultor(object):
    attributes_ordered = ['consultor_id', 'name', 'city', 'address', 'phone_office', 'phone_office_canonized', 
    					  'phone_direct', 'phone_direct_canonized', 'email'
    					 ]
    def __init__(self, consultor_id, name=None, city=None, phone_office=None, 
    			 phone_direct=None, address=None, email=None, 
                 canonizer=canonization.create_israeli_canonizer()):
        self._canonizer=canonizer
        self.consultor_id = consultor_id
        self.name = name
        self.city = city
        self.phone_office = phone_office
        self.phone_office_canonized = ''
        self.phone_direct = phone_direct
        self.phone_direct_canonized = ''
        self.address = address
        self.email = email

    def __setattr__(self, name, value):
        """
        custom attributes setting
        canonize phone numbers while keeping original
        """
    
        if value and name in ['phone_office', 'phone_direct']:
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

            super(TaxConsultor, self).__setattr__(name, value)  # Set original name and value

        elif name == 'email':
            # lowers email
            if value is None:
            	super(TaxConsultor, self).__setattr__(name, value)
            else:
            	super(TaxConsultor, self).__setattr__(name, value.lower())  # Set original name and value
        else:
        	super(TaxConsultor, self).__setattr__(name, value)


    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

def edit_string(src_string):
    """
    Removes white spaces and ':' at beginning and end.
    Replace consecutives whitespaces into a space

    finally, encode the string
    """
    cleaning_regex = re.compile(r'^[:\s]*(?P<value>.+?)[:\s]*$')
    temp_string = re.sub(r'\s+', ' ', src_string)  # Remove consecutive spaces
    match = cleaning_regex.search(temp_string)  # Clean whitespace and ':'
    if not match:
        return temp_string
    return match.group('value')

def get_all_headers(html_encoding='windows-1255'):
    """
    Find header names from all the files
    that were downloaded
    """

    all_file_paths = iglob(r'C:\Python27\Scripts\Experiments\databases\tax consultors\*')

    item_value_regex = re.compile(r'\<strong\>(?P<attribute>.+?)\<\/strong\>(?P<value>.*?)\<br\s\/\>')

    header_names = set()

    for file_path in all_file_paths:
        with open(file_path, 'rb') as consultor_file:

            attribute_values = item_value_regex.finditer(consultor_file.read())

            name = attribute_values.next().group('attribute')

            for attribute_value in attribute_values:
            	# Values/attributes are ALREADY encoded in UTF-8
            	attribute = edit_string(attribute_value.group('attribute'))
            	value = edit_string(attribute_value.group('value'))
            	header_names.add(attribute)

    return header_names

def parse_consultor_files_gen(bulk_amount=200, html_encoding='utf-8'):
    """
    returns list of bulk_amount Lawyers 
    that were parsed
    """

    all_file_paths = iglob(r'C:\Python27\Scripts\Experiments\databases\tax consultors\*')

    item_value_regex = re.compile(r'\<strong\>(?P<attribute>.+?)\<\/strong\>(?P<value>.*?)\<br\s\/\>')

    title_to_prop_dict = {
            'עיר': 'city',
            'כתובת לדואר': 'address',
            'דוא"ל': 'email',
            'טלפון משרד': 'phone_office',
            'טלפון ישיר': 'phone_direct',
    }

    consultors_lst = []
    consultor_id_pattern = re.compile(r'(?P<id>\d+).html$')
    item_value_regex = re.compile(r'\<strong\>(?P<attribute>.+?)\<\/strong\>(?P<value>.*?)\<br\s\/\>')

    for file_path in all_file_paths:
        # Loop over every lawyer file


        #  Look for consultor in 
        consultor_id_match = consultor_id_pattern.search(file_path)
        if consultor_id_match:
            consultor_id = consultor_id_match.group('id')
        else:
            consultor_id = ''

        with open(file_path, 'rb') as consultor_file:
            # Open it and parse

            attribute_values = item_value_regex.finditer(consultor_file.read())

            name = attribute_values.next().group('attribute')

            current_consultor = TaxConsultor(consultor_id=consultor_id, name=name)

            for attribute_value in attribute_values:
            	# Values/attributes are ALREADY encoded in UTF-8
            	attribute = edit_string(attribute_value.group('attribute'))
            	value = edit_string(attribute_value.group('value'))

            	actual_attribute = title_to_prop_dict[attribute]

            	setattr(current_consultor, actual_attribute, value)

            consultors_lst.append(current_consultor)

            if len(consultors_lst) == bulk_amount:
                # Yield a list of bulk_amount consultors
                yield consultors_lst
                consultors_lst = []

    yield consultors_lst  # Final yield

def save_tax_consultors(bulk_amount=300):
    """
    Parse lawyer files and save them to an excel
    """

    consultors_gen = parse_consultor_files_gen(bulk_amount)
    export_classes.instances_to_file(consultors_gen, instance_class=TaxConsultor)
    print 'DONE\n'


