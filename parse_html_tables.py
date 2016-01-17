#-*- encoding: utf-8 -*-

##########################
#
#        parse pages
#      	with html tables
#
#
##########################

import re, urllib, sys, os
from datetime import datetime
sys.path.append(r'C:\Python27\Scripts\Experiments\databases')

import export_tables

class Table(object):
	def __init__(self, name='', source='', rows=''):
		self.name = name
		self.source = source
		self.headers = None
		self.update = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
		if not rows:
			self.rows = []
		else:
			self.rows = rows

	def add_row(self, row):
		self.rows.append(row)

	def create_row(self):
		""" creates new row """
		row_amount = len(self.rows)
		new_row = Row(index=row_amount, cells=[])
		self.rows.append(new_row)

		return new_row

	def set_headers(self, headers_row):
		self.headers = [header.value for header in headers_row.cells]

	def cancel_row(self):
		self.rows = self.rows[:-1] #remove last row


	def __unicode__(self):
		return unicode(self.rows)

	#def __repr__(self):
	#	return unicode(self.rows)

class Row(object):
	def __init__(self, index, cells=[]):
		self.index = index
		self.cells = cells

	def add_cell(self, value):
		last_index = len(self.cells) - 1
		new_cell = Cell(index=last_index + 1, value=value)
		self.cells.append(new_cell)
		return new_cell

	def get_cells(self):
		return [cell.value for cell in self.cells]

	def __unicode__(self):
		return '|'.join(self.get_cells())

	def __repr__(self):
		return self.__unicode__()

class Cell(object):
	def __init__(self, index, value):
		self.index = index
		self.value = value

	def __unicode__(self):
		return self.value

	def __repr__(self):
		return self.value


def clean_value(string):
	string = re.sub(r'\n*<br\s?\/?>\n*', '|', string, flags=re.IGNORECASE)
	string = re.sub(r'(^[^\d\wקראטוןםפשדגכעיחלךףזסבהנמצתץ]*)|([^\d\wקראטוןםפשדגכעיחלךףזסבהנמצתץ]*$)', '', string, flags=re.IGNORECASE|re.UNICODE)
	return string

def parse_html_table_header(html_table, dst_table):
	""" parses the html table headers. returns true if headers were found """

	HEADERS_REGEX = r'<th.*?>(?P<value>.*?)<\/th'
	table_headers = re.finditer(HEADERS_REGEX, html_table, flags=re.IGNORECASE)

	row = dst_table.create_row()

	for table_header in table_headers:
		row.add_cell(table_header.group('value'))

	if len(row.cells) == 0:
		#no headers have been found
		dst_table.cancel_row()
		return False

	dst_table.set_headers(row)

	return True

def parse_html_table_cells(html_table, dst_table, inner_cell_regex=''):
	""" parses html tables cells into dst_table rows """

	ROW_REGEX = r'<tr.*?<tr'
	CELL_REGEX = r'<td[^/]+?>(?P<value>.*?)<.*?<\/td'

	table_rows = re.findall(ROW_REGEX, html_table, flags=re.IGNORECASE|re.DOTALL)
	print len(table_rows)
	for table_row in table_rows:
		row_cells = re.finditer(CELL_REGEX, table_row, re.DOTALL)
		row = dst_table.create_row()
		any_value = False #to check if row contains any value
		for row_cell in row_cells:
			written = False #if there is no inner cell regex or no match, whole row will be written
			if inner_cell_regex:
				match = re.search(inner_cell_regex, row_cell.group('value'))
				if match:
					val = clean_value(match.group('value'))
					row.add_cell(val)
					written = True
					if val.strip():
						any_value = True
			else:
				written = True
				any_value = True
				cell_value = clean_value(row_cell.group('value'))
				row.add_cell(cell_value)

			if not written:
				row.add_cell(clean_value(row_cell.group('value')))

		if not any_value:
			#Row is empty, delete it
			dst_table.cancel_row()

def parse_html_table(html_table, file_source='', file_name='', inner_cell_regex=''):
	""" parse html table and return a Table object """
	
	table = Table(name=file_name, source=file_source)

	parse_html_table_header(html_table, table)
	parse_html_table_cells(html_table, table)

	return table

def parse_multiple_tables(all_text, file_source='', file_name='', table_id='', table_class='', inner_cell_regex=''):
	if table_class:
		TABLE_REGEX = '<table[^>]*?{0}.*?>.*?<\/tab'.format(table_class)
	else:
		TABLE_REGEX = '<table[^>]*?{0}.*?>.*?<\/tab'.format(table_id)

	html_tables = re.findall(TABLE_REGEX, all_text, flags=re.IGNORECASE|re.DOTALL)

	parsed_tables = []
	with open(r'C:\testTable.txt', 'wb') as output:
		for html_table in html_tables:
			output.write(html_table + '\r\n--------\r\n')
			parsed_table = parse_html_table(html_table, file_source=file_source, file_name=file_name, inner_cell_regex=inner_cell_regex)
			parsed_tables.append(parsed_table)

	return parsed_tables

def get_domain(url):
	domain_regex = r'(http://)?(www.)?(?P<domain>[^/]+)'
	match = re.search(domain_regex, url)
	if match:
		result = match.group('domain')
	else:
		result = raw_input('Enter file name:\n')
	return result

def get_page_title(page_source):
	""" parses the page title from html page """
	title_regex = r'<title.*?>(?P<title>.*?)<\/title>'
	match = re.search(title_regex, page_source, flags=re.IGNORECASE)
	if match:
		page_title = match.group('title')
		print page_title
		return re.sub('\s*\|\s*', '-', page_title)
	return 'unknown'

def main():
	URL = raw_input('Enter url with html pages:\n')
	page = urllib.urlopen(URL).read()
	file_source = get_domain(URL)
	file_title = get_page_title(page)

	table_params = raw_input("Enter regex of table param:\n")

	tables = parse_multiple_tables(page, file_source=file_source, file_name=file_title, table_class=table_params)
	dst_path_no_ext = os.path.join(r'C:\Python27\Scripts\Experiments\databases', file_title)
	success = export_tables.save_as_file(dst_path_no_ext, tables=tables, format='xlsx', one_sheet=True)
	return tables

	