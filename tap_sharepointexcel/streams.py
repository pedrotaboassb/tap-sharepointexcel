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

import openpyxl

import re

import io 

# TODO: Delete this is if not using json files for schema definition
#SCHEMAS_DIR = Path(__file__).parent / Path("./schemas")
# TODO: - Override `UsersStream` and `GroupsStream` with your own stream definition.
#       - Copy-paste as many times as needed to create multiple stream types.

class ExcelMasterFile(sharepointexcelStream):
    """Define custom stream."""
    #calling the api so we can build a schema and keeping data data in memory so we don't have to call the api again. 
    
    def __init__(self, *args, **kwargs ):
        self.response_schema = None
        self.response_built_object = None
        super().__init__(*args, **kwargs)
    
    #@cached    
    
    def get_response_object(self):
        
        response = requests.get(self.url_base+self.path, headers=self.authenticator._auth_headers)       
        for objs in response.json()['value']:
            if objs['name'] == self.path.split("q='")[1].split("'")[0] + ".xlsx":
                    response_objects = [metadata for metadata in response.json()['value'] ]
            else:
                 break

        list_of_master_file_data = sorted( response_objects, key = lambda x: x['lastModifiedDateTime'])
            
        new_response = requests.get(self.url_base+f"/items/{list_of_master_file_data[-1]['id']}/content", headers=self.authenticator._auth_headers)

        return new_response


    def read_workbook(self):
        #Needs function to do excel vs csv        
        response_file = self.get_response_object()
        
        file = io.BytesIO(response_file.content)
        workbook = openpyxl.load_workbook(file)
        
        json_headers = list()            
        json_rows = list()


        for col in workbook[self.config['sheet_name']].iter_cols(values_only=True):
            json_headers.append(col[0])
            json_rows.append(list(col[2:]))
            
        shelf_data = dict(zip(json_headers, json_rows))
        

        for values in shelf_data.values():
            #what if everything is "","" or if someone has used , to separe each 3 digits? does the lib read the excel format correctly? 
            if (any(isinstance(x, str)  for x in values) 
                and 
               (any(isinstance(x, float)  for x in values) 
                or 
                any(isinstance(x, int)  for x in values))):
                for i in values:
                    if i is not None:
                        values[values.index(i)] = float(str(i).replace(',', '.'))

        json_object = [dict(zip(shelf_data, col)) for col in zip(*shelf_data.values())]

        self.response_object = json.dumps(json_object, default=serialize_datetime)  
          
        return shelf_data
            

            
    
    def build_data_schema(self):
        
        date_types_list = list()
        
        for header, values in self.read_workbook().items():
            date_types = {}
            date_types[header] = list(map(lambda x: re.search(r"<[^>]+\'([^']+)\'>", str(type(x))).group(1), values ))
            date_types_list.append(date_types)

        self.response_schema = date_types_list


    
    @property
    def schema(self) -> dict:
        if not self.response_schema:
           self.build_data_schema()
        properties: List[th.Property] = []     
        for each in self.response_schema:
            for name, type in each.items():
                if any('int' in x for x in type) or any('float' in x for x in type):
                    type = th.NumberType() 
                elif any('datetime' in x for x in type):
                    type = th.DateTimeType()
                else:
                    type = th.StringType()  
                properties.append(th.Property(name, type )) 
        return th.PropertiesList(*properties).to_dict()
    

    @property
    def path(self) -> str:
        file_name = self.config['search_query']
        file_query = f"/search(q='{file_name}')"
        return file_query

    name = "ExcelMasterFile"
    primary_keys = ["ISIN"]
    #which date to use with the replication key? 
    replication_key = "ISIN"
    # Optionally, you may also use `schema_filepath` in place of `schema`:
    # schema_filepath = SCHEMAS_DIR / "users.json"  # noqa: ERA001
  
  
    
    def get_records(self, *args, **kwargs ):
        
        yield from extract_jsonpath(self.records_jsonpath, input=json.loads(self.response_object))


