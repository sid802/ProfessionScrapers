#-*-encode: utf-8 -*-

############
#Technion  #
#Professors#
############

from lxml import html
import urllib, re, sys
sys.path.append(r'C:\Python27\Scripts\Experiments\databases')
from export_classes import instances_to_file

class Professor(object):
	attributes_ordered = ['p_id', 'name', 'job', 'phone', 'fax', 'email', 'personal_site', 'room', 'specialties', 'pic_url']
	def __init__(self, p_id='', name='', job='', phone='', fax='', email='', personal_site='', room='', specialties='', pic_url=''):
		self.p_id=p_id
		self.name=name
		self.job=job
		self.phone=phone
		self.fax=fax
		self.email=email
		self.personal_site=personal_site
		self.room=room
		self.specialties=specialties
		self.pic_url=pic_url

	def __str__(self):
		return self.name

def clean_email(str_email):
	return re.sub('^mailto:', '', str_email).strip()

def clean_specialties(str_specialties):
	only_specialties = [str_specialty.strip() for str_specialty in str_specialties if str_specialty.strip()]
	return '|'.join(map(lambda x: unicode(re.sub(r'(^[\s*|]*)|([\s*|]*$)', '', x)), only_specialties))

def first_item_or_null(value_lst):
	if len(value_lst) > 0:
		value = value_lst[0]
		if type(value) == html.HtmlElement:
			#Get text of element
			value = value.text_content()

		#XML Element
		return unicode(value)

	return ''


def parse_professor_from_page(p_id, page_source):
	name_path = '//td[@class="TextBlack2"]/b[1]'
	job_path = '//td[@class="TextBlack2"]/font[1]'
	phone_path = '//td[@width="100" and @style="padding-top: 10px"]/font[contains(.,"T.")]/following-sibling::text()[1]'
	fax_path = '//td[@width="100" and @style="padding-top: 10px"]/font[contains(.,"F.")]/following-sibling::text()[1]'
	email_path = '//td[@width="100" and @style="padding-top: 10px"]/a[1]/@href'
	personal_site = '//td[@width="100" and @style="padding-top: 10px"]/a[2]/@href'
	room_path = '//td[@width="100" and @dir="rtl" and @align="right"][2]'
	specialties_path = '//td[@width="150" and @style="padding-bottom: 10px"]/text()'
	pic_url_path = '//td[@width="255"]/img[@border="0"]/@src'

	html_tree = html.fromstring(page_source)

	name = first_item_or_null(html_tree.xpath(name_path))
	if name != '':
		job = first_item_or_null(html_tree.xpath(job_path))
		phone = first_item_or_null(html_tree.xpath(phone_path))
		fax = first_item_or_null(html_tree.xpath(fax_path))
		email = clean_email(first_item_or_null(html_tree.xpath(email_path)))
		personal_site = first_item_or_null(html_tree.xpath(personal_site))
		room = first_item_or_null(html_tree.xpath(room_path))
		specialties = clean_specialties(html_tree.xpath(specialties_path)) #All items in results are relevant
		pic_url = first_item_or_null(html_tree.xpath(pic_url_path))
		
		professor = Professor(p_id = p_id, name=name, job=job, phone=phone, fax=fax, email=email, personal_site=personal_site, room=room, specialties=specialties, pic_url=pic_url)
		return professor
	return None

def parse_professors(base_url):
	""" parses professors from different URL's """

	professors_dict = {}
	for p_id in xrange(300):
		if p_id%5==0:
			print p_id
		page_source = urllib.urlopen(base_url.format(id=p_id)).read()
		professor = parse_professor_from_page(p_id, page_source)
		if professor != None:
			#print professor
			professors_dict[p_id] = professor

	return professors_dict

def main():
	BASE_URL=r'http://edu.technion.ac.il/show_details.php?id={id}'
	professors_dict = parse_professors(BASE_URL)
	instances_to_file(professors_dict.values())

	return professors_dict
