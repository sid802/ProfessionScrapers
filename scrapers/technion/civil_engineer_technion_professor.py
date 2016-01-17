#-*-encode: utf-8 -*-

#########################
#Technion               #
#CivilEngineerProfessors#
#########################

from lxml import html
import urllib, re, sys
sys.path.append(r'C:\Python27\Scripts\Experiments\databases')
from export_classes import instances_to_file

class CivilEngineerProfessor(object):
	attributes_ordered = ['p_id', 'name', 'job', 'phone', 'fax', 'email', 'personal_site', 'room', 'research_interests', 'pic_url', 'source']
	def __init__(self, p_id='', name='', job='', phone='', fax='', email='', personal_site='', room='', research_interests='', pic_url='', source=''):
		self.p_id=p_id
		self.name=name
		self.job=job
		self.phone=phone
		self.fax=fax
		self.email=email
		self.personal_site=personal_site
		self.room=room
		self.research_interests=research_interests
		self.pic_url=pic_url
		self.source = source

	def __str__(self):
		return self.name

def clean_email(str_email):
	return re.sub('^mailto:', '', str_email).strip()

def concat_results(str_specialties):
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


def parse_professor_from_page(p_id, page_source, page_url, domain):
	name_title_path = '//div[@class="managementItemTitle"]/h1/text()'
	job_path = '//table[@class="managementListTable"]//table//tr[1]/td/text()'
	phone_path = '//table[@class="managementListTable"]//table//tr[2]/td/text()'
	fax_path = '//table[@class="managementListTable"]//table//tr[3]/td/text()'
	email_path = '//table[@class="managementListTable"]//table//tr[4]/td/a/@href'
	room_path = '//table[@class="managementListTable"]//table//tr[5]/td/text()'
	personal_site = '//table[@class="managementListTable"]//table//tr[6]/td/a/@href'
	research_interests_path = '//table[@class="managementListTable"]//table//tr[8]/th/text()'
	pic_url_path = '//table[@class="managementListTable"]//img/@src'

	html_tree = html.fromstring(page_source)

	name_title = first_item_or_null(html_tree.xpath(name_title_path))
	if name_title != '':
		job = first_item_or_null(html_tree.xpath(job_path))
		phone = first_item_or_null(html_tree.xpath(phone_path))
		fax = first_item_or_null(html_tree.xpath(fax_path))
		email = clean_email(first_item_or_null(html_tree.xpath(email_path)))
		personal_site = first_item_or_null(html_tree.xpath(personal_site))
		room = concat_results(html_tree.xpath(room_path))
		research_interests = concat_results(html_tree.xpath(research_interests_path)) #All items in results are relevant
		pic_url = first_item_or_null(html_tree.xpath(pic_url_path))

		if pic_url.startswith('/'):
			pic_url = domain + pic_url
		
		professor = CivilEngineerProfessor(p_id = p_id, name=name_title, job=job, phone=phone, fax=fax, email=email, personal_site=personal_site, room=room, research_interests=research_interests, pic_url=pic_url, source=page_url)
		return professor
	return None

def get_domain(url):
	domain_regex = r'(http://)?(www.)?(?P<domain>[^/]+)'
	match = re.search(domain_regex, url)
	if match:
		result = match.group('domain')
	else:
		result = raw_input('Enter file name:\n')
	return result

def parse_professors(base_url):
	""" parses professors from different URL's """

	domain = get_domain(base_url)

	professors_dict = {}
	for p_id in xrange(500):
		if p_id%5==0:
			print p_id
		current_url = base_url.format(id=p_id)
		page_source = urllib.urlopen(current_url).read()
		professor = parse_professor_from_page(p_id, page_source, current_url, domain)
		if professor != None:
			#print professor
			professors_dict[p_id] = professor

	return professors_dict

def main():
	BASE_URL=r'http://cee.technion.ac.il/eng/Templates/ShowPage.asp?DBID=1&TMID=139&LNGID=1&FID=166&PID=0&IID={id}'
	professors_dict = parse_professors(BASE_URL)
	instances_to_file(professors_dict.values())

	return professors_dict
