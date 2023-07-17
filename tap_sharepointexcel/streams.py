"""Stream type classes for tap-sharepointexcel."""


from __future__ import annotations

from pathlib import Path


import requests

from singer_sdk import typing as th  # JSON Schema typing helpers

from singer_sdk.helpers.jsonpath import extract_jsonpath

from tap_sharepointexcel.client import sharepointexcelStream

from .utils import find_newest_file, find_row_with_target_string, delete_row, serialize_datetime, find_numbers

import json

import numpy as np

import pandas as pd
from memoization import cached

from typing import List

from singer_sdk import typing as th

from datetime import datetime
from singer_sdk.typing import (
    DateTimeType,
    ObjectType,
    PropertiesList,
    Property,
    StringType,
)


import io 

# TODO: Delete this is if not using json files for schema definition
SCHEMAS_DIR = Path(__file__).parent / Path("./schemas")
FILES_DIR = Path(__file__).parent / Path("./files")
# TODO: - Override `UsersStream` and `GroupsStream` with your own stream definition.
#       - Copy-paste as many times as needed to create multiple stream types.
last_id =  None

class ExcelFile_six(sharepointexcelStream):
    """Define custom stream."""
    
    @cached
    def get_file_to_make_schema_from(self):
        
        response = requests.get(self.url_base+self.path, headers=self.authenticator._auth_headers)
        list_of_master_file_data = sorted([metadata for metadata in response.json()['value'] if metadata['name'] == 'EET Master File.xlsx'], key = lambda x: x['lastModifiedDateTime'])
        new_response = requests.get(self.url_base+f"/items/{list_of_master_file_data[-1]['id']}/content", headers=self.authenticator._auth_headers)
        excel_data_dict = (pd.read_excel(io.BytesIO(new_response.content), engine='openpyxl')
            .apply(lambda x : [find_numbers(i) for i in x] )
            .to_dict()  
            )
        columns, row_index_list = find_row_with_target_string(excel_data_dict)
        _final_data = pd.DataFrame.from_dict(delete_row(excel_data_dict, columns, row_index_list)).fillna(np.nan).replace(np.nan, None)
        for each in _final_data:
            if any(_final_data[each].apply(lambda x : x.replace('.', '').isnumeric() if isinstance(x, str) else ( True if isinstance(x, int) or isinstance(x, float) else False) )):           
                _final_data[each] = pd.to_numeric(_final_data[each] ,errors='coerce') 
        _final_data = _final_data.dtypes.to_dict()
        response_schema = {}
        for name, type in _final_data.items():
            if type == 'float64': 
               type = "number"
            elif type == 'int64':  
               type = "number"
            else:
               type = "string"     
            response_schema[name] = type


         
        return response_schema
    
    @property
    def schema(self) -> dict:
        response_schema = self.get_file_to_make_schema_from()
        properties: List[th.Property] = []
        for name, type in response_schema.items():
            if type == 'number':
                type = th.NumberType() 
            else:
                type = th.StringType()  
            properties.append(th.Property(name, type )) 
            properties.append(th.Property('file_id', th.StringType())) 
            properties.append(th.Property('last_modified_datetime', th.StringType())) 
            properties.append(th.Property('last_sync_datetime', th.StringType()))
            properties.append(th.Property('file_name', th.StringType()))  
        return th.PropertiesList(*properties).to_dict()


    name = "excelfile_six"
    path =  "/search(q='EET Master File')"
    primary_keys = ["ISIN"]
    replication_key = "ISIN"
    # Optionally, you may also use `schema_filepath` in place of `schema`:
    # schema_filepath = SCHEMAS_DIR / "users.json"  # noqa: ERA001
    #content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
  
    
    def parse_response(self, response: requests.Response) -> Iterable[dict]:
        """Parse the response and return an iterator of result records."""
        # TODO: Parse response body and return a set of records.
        list_of_master_file_data = sorted([metadata for metadata in response.json()['value'] if metadata['name'] == 'EET Master File.xlsx'], key = lambda x: x['lastModifiedDateTime'])
        self.file_id = list_of_master_file_data[-1]['id']
        self.last_modified_datetime = list_of_master_file_data[-1]['lastModifiedDateTime']
        self.file_name = list_of_master_file_data[-1]['name']   
        
        parsed_response = requests.get(self.url_base+f"/items/{list_of_master_file_data[-1]['id']}/content", headers=self.authenticator._auth_headers)
        excel_data_dict_ = (pd.read_excel(io.BytesIO(parsed_response.content))
            .assign(last_sync_datetime= pd.Timestamp.now(tz='Europe/Oslo'), last_modified_datetime = self.last_modified_datetime, file_name =self.file_name, file_id = self.file_id )
            .apply(lambda x : [find_numbers(i) for i in x] )
            .to_dict()  
                          )
        
        columns_, row_index_list_ = find_row_with_target_string(excel_data_dict_)
        
        json_final_data = json.loads(json.dumps(pd.DataFrame.from_dict(delete_row(excel_data_dict_, columns_, row_index_list_)).fillna(np.nan).replace(np.nan, None).to_dict('records') , default=serialize_datetime))
 
        yield from extract_jsonpath(self.records_jsonpath, input=json_final_data)