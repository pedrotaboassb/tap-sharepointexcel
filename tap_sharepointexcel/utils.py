from datetime import date, datetime
import re

def find_newest_file(d, objs):
    if isinstance(d, list):
       for each in d:
           find_newest_file(each, objs)
    elif isinstance(d, dict):
         if 'name' in d and d['name'] == 'EET Master File.xlsx':
             for k, v in d.items():
                data = {'lastModifiedDateTime': d['lastModifiedDateTime'],
                        'name': d['name'],
                        'id': d['id'] }
                
             objs.append(data)
         else: 
           for k, v in d.items(): 
               if isinstance(v, dict):
                  find_newest_file(v, objs)
    
       
    return  objs


def delete_row(excel_data_dict, columns, row_index):
    result = all(element == row_index[0] for element in row_index)
    if (result):
        for each in columns:
            excel_data_dict[each].pop(row_index[0])
    else:
        print("All not equal")

    return excel_data_dict


def find_row_with_target_string(d, columns = [], row_index_list = [] ):
    for k, v in d.items():
        if not isinstance(v, dict) and v == "Master file":
           row_index_list.append(k) 
        elif isinstance(v, dict):
            columns.append(k)
            find_row_with_target_string(v, columns, row_index_list)

                
               
    return columns, row_index_list


def serialize_datetime(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError("Type not serializable")


def find_numbers(x):
    if isinstance(x, str):
        if x.isdigit():
            return int(x)
        elif '.' in x:
            try:
                return float(x)
            except ValueError:
                pass
    return x


"""
def find_numbers(x):
    if isinstance(x, str) and (re.search(r"[-+]?(?:\d*\.*\d+)",  str(x))):

            if re.search(r"\.",  x):
               x = float( re.search(r"[-+]?(?:\d*\.*\d+)",  str(x)).group())
            else:

               x = int( re.search(r"[-+]?(?:\d*\.*\d+)",  str(x)).group())

    else: 
        x          
    return  x  

"""    