#-*-encode: utf-8 -*-

##############
#Technion    #
#Architecture#
#Professors  #
##############

from lxml import html
import urllib, re, sys
sys.path.append(r'C:\Python27\Scripts\Experiments\databases')
from export_classes import instances_to_file

class ArchitectProfessor(object):
	attributes_ordered = ['name', 'job', 'phone', 'email', 'office_location', 'specialties', 'pic_url']
	def __init__(self, name='', job='', phone='', office_location='', email='', pic_url='', specialties=''):
		self.name=name
		self.job=job
		self.phone=phone
		self.email=email
		self.office_location=office_location
		self.specialties=specialties
		self.pic_url=pic_url

	def __str__(self):
		return self.name

def clean_email(str_email):
	return re.sub('^mailto:', '', str_email).strip()

def clean_specialties(str_specialties):

	if isinstance(str_specialties, list):
		only_specialties = [str_specialty.strip() for str_specialty in str_specialties if str_specialty.strip()]
		return '|'.join(map(lambda x: unicode(re.sub(r'(^[\s*|]*)|([\s*|]*$)', '', x)), only_specialties))
	return str_specialties

def first_item_or_null(value_lst):
	if len(value_lst) > 0:
		value = value_lst[0]
		if type(value) == html.HtmlElement:
			#Get text of element
			value = value.text_content()

		#XML Element
		return unicode(value)

	return ''


def parse_professor_from_row(professor_row_element):
	name_path = './/td[@class="fullName"]//a/text()'
	job_path = './/td[@class="commentBottom"]/text()'
	phone_path = './/td[@class="phoneNumber"]/text()'
	email_path = './/td[@class="EmailAddress"]/a/text()'
	office_location_path = './/td[@class="officeLocation"]/text()'
	specialties_path = './/td[@class="commentBottom"]//*[self::p or self::pre or self::span]/text()'
	pic_url_path = './/td[@class="headPicture"]//img/@src'


	name = first_item_or_null(professor_row_element.xpath(name_path))
	if name != '':
		job = first_item_or_null(professor_row_element.xpath(job_path))
		phone = first_item_or_null(professor_row_element.xpath(phone_path))
		email = first_item_or_null(professor_row_element.xpath(email_path))
		office_location = first_item_or_null(professor_row_element.xpath(office_location_path))
		specialties = clean_specialties(professor_row_element.xpath(specialties_path)) #All items in results are relevant
		pic_url = first_item_or_null(professor_row_element.xpath(pic_url_path))
		
		professor = ArchitectProfessor(name=name, job=job, phone=phone, email=email, office_location=office_location, specialties=specialties, pic_url=pic_url)
		return professor
	return None

def parse_professors(base_url):
	""" parses professors from different URL's """

	row_xpath = '//tr/td/table'

	professors_lst = []
	page_source=urllib.urlopen(base_url).read()

	page_tree = html.fromstring(page_source)
	professor_rows = page_tree.xpath(row_xpath)

	for professor_row in professor_rows:
		professor = parse_professor_from_row(professor_row)
		if professor != None:
			professors_lst.append(professor)

	return professors_lst

def main():
	BASE_URL=r'http://architecture.technion.ac.il/people/faculty/'
	professors_lst = parse_professors(BASE_URL)
	instances_to_file(professors_lst)

	return professors_lst
