# -*- encoding: utf-8 -*-

###################
#
#Export classes to 
#excel
#
###################

from xlsxwriter.workbook import Workbook
from datetime import date
import os

def create_full_path(dst_folder, objects, instance_class=None, format='xlsx'):
    """ create file name and join in to dst_folder """
    if instance_class:
        single_instance = instance_class(0, 0)
    else:
        single_instance = objects[0]
    obj_class = single_instance.__class__.__name__
    today_string = date.today().strftime('%d-%m-%Y')
    file_name = '{o_class}_{date}.{ext}'.format(o_class=obj_class, date=today_string, ext=format)
    return os.path.join(dst_folder, file_name)

def write_headers(sheet, headers):
    """ write headers in sheet """
    for index, header in enumerate(headers):
        sheet.write(0, index, header)

def write_instances(sheet, instances, attributes, encoding='utf-8'):
    """ write instances in sheet"""
    current_row = 1  # rows are 0-indexed and headers are in row 0
    for instance in instances:
        list_instance = list(instance)
        for sub_instance in list_instance:
            write_instance(sheet, sub_instance, attributes, current_row, encoding=encoding)
            current_row += 1
            if current_row % 200 == 0:
                print u'Just wrote in row {0}: {1}'.format(current_row, sub_instance)

def write_instance(sheet, instance, attributes, row, encoding='utf-8'):
    for attr_index, attribute in enumerate(attributes):
        #Loop attributes
        value = getattr(instance, attribute)
        if type(value) == str:
            try:
                value = value.decode(encoding)
            except Exception:
                print value
        sheet.write(row, attr_index, value) #instance_index + 1 (header is in row 0)

def instances_to_excel(instances, dst_path=r'Desktop/instance_output.xlsx', encoding='utf-8', instance_class=None):
    dst_wb = Workbook(dst_path)
    dst_sheet = dst_wb.add_worksheet('instances')

    if instance_class:
        attributes_ordered = instance_class(0, 0).attributes_ordered
    elif instance_class is None and type(instances) == list:
        attributes_ordered = instances[0].attributes_ordered
    else:
        raise Exception("No attributes_ordered exists")

    write_headers(sheet=dst_sheet, headers=attributes_ordered)
    write_instances(sheet=dst_sheet, instances=instances, encoding=encoding, attributes=attributes_ordered)

    dst_wb.close()

def instances_to_file(objects, dst_folder='Desktop/', format='xlsx', instance_class=None, encoding='utf-8'):
    """ Saves instances of a class into an excel """

    while not os.path.exists(dst_folder):
        dst_folder = raw_input('Enter existing folder to save file:\n')
    dst_path = create_full_path(dst_folder, objects, instance_class, format)
    if 'xls' in format:
        print 'creating file:', dst_path
        success = instances_to_excel(objects, dst_path, encoding=encoding, instance_class=instance_class)
    return dst_path


