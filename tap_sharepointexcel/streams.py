"""Stream type classes for tap-sharepointexcel."""


from __future__ import annotations

from pathlib import Path

import requests

from singer_sdk import typing as th  # JSON Schema typing helpers

from singer_sdk.helpers.jsonpath import extract_jsonpath

from tap_sharepointexcel.client import sharepointexcelStream

from .utils import  find_row_with_target_string, delete_row, serialize_datetime, find_numbers

import json

import numpy as np

import pandas as pd

from memoization import cached

from typing import List

from singer_sdk import typing as th

from datetime import datetime



import io 

# TODO: Delete this is if not using json files for schema definition
#SCHEMAS_DIR = Path(__file__).parent / Path("./schemas")
# TODO: - Override `UsersStream` and `GroupsStream` with your own stream definition.
#       - Copy-paste as many times as needed to create multiple stream types.

class ExcelFile(sharepointexcelStream):
    """Define custom stream."""
    #calling the api so we can build a schema and keeping data data in memory so we don't have to call the api again. 
    
    def __init__(self, *args, **kwargs ):
        self.response_schema = None
        super().__init__(*args, **kwargs)
    
    #@cached    
    def get_initial_data(self):

        response = requests.get(self.url_base+self.path, headers=self.authenticator._auth_headers)
                 
        for objs in response.json()['value']:
            if objs['name'] == self.path.split("q='")[1].split("'")[0] + ".xlsx":
               response_objects = [metadata for metadata in response.json()['value'] ]
            else:
                break

        list_of_master_file_data = sorted( response_objects, key = lambda x: x['lastModifiedDateTime'])
        
        new_response = requests.get(self.url_base+f"/items/{list_of_master_file_data[-1]['id']}/content", headers=self.authenticator._auth_headers)
       
        excel_data_dict = (pd.read_excel(io.BytesIO(new_response.content), engine='openpyxl')
            .assign(last_sync_datetime= pd.Timestamp.now(tz='Europe/Oslo'), last_modified_datetime = list_of_master_file_data[-1]['lastModifiedDateTime'], file_name =list_of_master_file_data[-1]['name'], file_id = list_of_master_file_data[-1]['id'] )              
            #maybe this is overkill, since I have another, more complete one, a few lines below
            .apply(lambda x : [find_numbers(i) for i in x] )
            .to_dict()  
            )

        columns, row_index_list = find_row_with_target_string(excel_data_dict)
        _final_data = pd.DataFrame.from_dict(delete_row(excel_data_dict, columns, row_index_list)).fillna(np.nan).replace(np.nan, None)
        
        #converting columns into their natural data types (double down on that :) )
        for each in _final_data:
            if any(_final_data[each].apply(lambda x : x.replace('.', '').isnumeric() if isinstance(x, str) else ( True if isinstance(x, int) or isinstance(x, float) else False) )):           
                _final_data[each] = pd.to_numeric(_final_data[each] ,errors='coerce') 
        
        return _final_data


    #@cached
    def build_schema_from_data(self):
        if not self.response_schema:

            _final_data_types = self.get_initial_data().dtypes.to_dict()
            
            #creating a dictionary with the incoming dimensions and their value types
            response_schema = {}
            for name, type in _final_data_types.items():
                if type == 'float64': 
                    type = "number"
                elif type == 'int64':  
                    type = "number"
                else:
                    type = "string"     
                response_schema[name] = type

                self.response_schema = response_schema   
        
        return self.response_schema
    
    @property
    def schema(self) -> dict:
        response_schema = self.build_schema_from_data()
        properties: List[th.Property] = []
        
        for name, type in response_schema.items():
            if type == 'number':
                type = th.NumberType() 
            else:
                type = th.StringType()  
            properties.append(th.Property(name, type )) 
  
        return th.PropertiesList(*properties).to_dict()
    
    @property
    def path(self) -> str:
        file_name = self.config['search_query']
        file_query = f"/search(q='{file_name}')"
        return file_query

    name = "excelfile"
    primary_keys = ["ISIN"]
    #which date to use with the replication key? 
    replication_key = "ISIN"
    # Optionally, you may also use `schema_filepath` in place of `schema`:
    # schema_filepath = SCHEMAS_DIR / "users.json"  # noqa: ERA001
  
  
    
    def get_records(self, *args, **kwargs ):
        response = self.get_initial_data()
    
        json_final_data = json.loads(json.dumps(response.fillna(np.nan).replace(np.nan, None).to_dict('records') , default=serialize_datetime))
 
        yield from extract_jsonpath(self.records_jsonpath, input=json_final_data)


