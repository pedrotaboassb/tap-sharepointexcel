"""Stream type classes for tap-sharepointexcel."""

from __future__ import annotations

from pathlib import Path
import typing as t

import requests

from singer_sdk import typing as th  # JSON Schema typing helpers

from singer_sdk.helpers.jsonpath import extract_jsonpath

from tap_sharepointexcel.client import sharepointexcelStream

from .utils import find_newest_file, find_row_with_target_string, delete_row, serialize_datetime, find_numbers

import json

import numpy as np

import pandas as pd

from datetime import datetime


import io 

# TODO: Delete this is if not using json files for schema definition
SCHEMAS_DIR = Path(__file__).parent / Path("./schemas")
FILES_DIR = Path(__file__).parent / Path("./files")
# TODO: - Override `UsersStream` and `GroupsStream` with your own stream definition.
#       - Copy-paste as many times as needed to create multiple stream types.


class DriveItemsStream(sharepointexcelStream):
    """Define custom stream."""
    
    name = "driveitems"
    path =  "/search(q='EET Master File')"
    primary_keys = ["id"]
    replication_key = None
    # Optionally, you may also use `schema_filepath` in place of `schema`:
    # schema_filepath = SCHEMAS_DIR / "users.json"  # noqa: ERA001
    schema_filepath = SCHEMAS_DIR / "driveitems.json" 
    
    

    def get_child_context(self, record, context: dict) -> dict:
       
        """Return a context dictionary for child streams."""
        list_of_master_file_data = sorted(find_newest_file(record, objs = []), key = lambda x: x['lastModifiedDateTime'])
        return {
           'file_id': list_of_master_file_data[-1]['id'],
           'lastModifiedDateTime': list_of_master_file_data[-1]['lastModifiedDateTime'],
           'file_name': list_of_master_file_data[-1]['name']
               }
    


class ExcelFile(sharepointexcelStream):
    

    name = "excelfile"
    parent_stream_type = DriveItemsStream
    ignore_parent_replication_keys = True
    path = "/items/{file_id}/content"
    primary_keys = ["ISIN"]
    replication_key = "ISIN"
    schema_filepath = SCHEMAS_DIR / "excelfields.json"
    content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    state_partitioning_keys = []
    

    def get_records(self, context):
        
        self.file_id = context['file_id']
        self.lastModifiedDateTime = context['lastModifiedDateTime']
        self.file_name = context['file_name']

        return super().get_records(context)


    def parse_response(self, response: requests.Response):
        
        excel_data_dict = (pd.read_excel(io.BytesIO(response.content))
            .assign(last_sync_datetime= pd.Timestamp.now(tz='Europe/Oslo'), last_modified_datetime = self.lastModifiedDateTime, file_name =self.file_name, file_id = self.file_id )
            .apply(lambda x : [find_numbers(i) for i in x] )
            .to_dict()  
                          )
        
        columns, row_index_list = find_row_with_target_string(excel_data_dict)
        
        json_final_data = json.loads(json.dumps(pd.DataFrame.from_dict(delete_row(excel_data_dict, columns, row_index_list)).fillna(np.nan).replace(np.nan, None).to_dict('records') , default=serialize_datetime))
 
        return extract_jsonpath(self.records_jsonpath, input=json_final_data)


    
   