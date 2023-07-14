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


def delete_row(the_dict, coll, row_idx):
    result = all(element == row_idx[0] for element in row_idx)
    if (result):
        for each in coll:     
            the_dict[each].pop(row_idx[0])
    else:
        print("All not equal")

    return the_dict


def find_row_with_target_string(d, cols = None, rows_index_list_ = None ):
    cols = [] if cols is None else cols
    rows_index_list_ = [] if rows_index_list_ is None else rows_index_list_
    for k, v in d.items():
        if not isinstance(v, dict) and v == "Master file":
           rows_index_list_.append(k) 
        elif isinstance(v, dict):
            cols.append(k)
            find_row_with_target_string(v, cols, rows_index_list_)

                
               
    return cols, rows_index_list_


def serialize_datetime(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError("Type not serializable")


def find_numbers(x):
    if isinstance(x, str):
        if x.isdigit():
            return int(x)
        elif ('.' in x) or (',' in x):
            try:
                return float(x)
            except ValueError:
                pass
    return x

