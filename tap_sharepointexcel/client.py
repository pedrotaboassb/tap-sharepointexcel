"""REST client handling, including sharepointexcelStream base class."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Iterable

import requests
from singer_sdk.authenticators import BearerTokenAuthenticator, SimpleAuthenticator
from singer_sdk.helpers.jsonpath import extract_jsonpath
from singer_sdk.pagination import BaseAPIPaginator  # noqa: TCH002
from singer_sdk.streams import RESTStream

from .utils import find_newest_file, find_row_with_target_string, delete_row, find_numbers

import json

import numpy as np


import pandas as pd

from datetime import datetime

import io 

from azure.identity import DefaultAzureCredential, ManagedIdentityCredential

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


_Auth = Callable[[requests.PreparedRequest], requests.PreparedRequest]
SCHEMAS_DIR = Path(__file__).parent / Path("./schemas")


class sharepointexcelStream(RESTStream):
    """sharepointexcel stream class."""

    @property
    def url_base(self) -> str:
        """Return the API URL root, configurable via tap settings."""
        # TODO: hardcode a value here, or retrieve it from self.config
        return self.config["api_url"] 

    #records_jsonpath = "$.value[*]"  # Or override `parse_response`.

    # Set this value or override `get_new_paginator`.
    #next_page_token_jsonpath = "$.next_page"  # noqa: S105

   
    @property
    def authenticator(self) -> BearerTokenAuthenticator:
        """Return a new authenticator object."""
        ad_scope = "https://graph.microsoft.com/.default"
        if self.config.get("client_id"):
            creds = ManagedIdentityCredential(client_id=self.config["client_id"])
            token = creds.get_token(ad_scope).token
        elif self.config.get("auth_token"):
            token =  self.config.get('auth_token')
        else:
            creds = DefaultAzureCredential()
            token = creds.get_token(ad_scope).token

        return BearerTokenAuthenticator.create_for_stream(self, token=token)
    '''
    def authenticator(self) -> BearerTokenAuthenticator:
        self.logger.info('The Bearer!!')    
        return BearerTokenAuthenticator.create_for_stream(self, token=self.config.get('auth_token'))
    '''

    @property
    def http_headers(self) -> dict:
        """Return the http headers needed.

        Returns:
            A dictionary of HTTP headers.
        """
        headers = {}
        if "user_agent" in self.config:
            headers["User-Agent"] = self.config.get("user_agent")
        # If not using an authenticator, you may also provide inline auth headers:
        # headers["Private-Token"] = self.config.get("auth_token")  # noqa: ERA001
        #headers['Authorization'] = self.config.get("auth_token")
        #print(headers)
        return headers


    def parse_response(self, response: requests.Response) -> Iterable[dict]:
        """Parse the response and return an iterator of result records."""
        # TODO: Parse response body and return a set of records.
        list_of_master_file_data = sorted([metadata for metadata in response.json()['value'] if metadata['name'] == 'EET Master File.xlsx'], key = lambda x: x['lastModifiedDateTime'])
        self.logger.info("was called! the parsinf on the client sheet")
        new_response = requests.get(self.url_base+f"/items/{list_of_master_file_data[-1]['id']}/content", headers=self.authenticator._auth_headers)
        excel_data_dict = (pd.read_excel(io.BytesIO(new_response.content))
            .apply(lambda x : [find_numbers(i) for i in x] )
            .to_dict()  
        )

        columns, row_index_list = find_row_with_target_string(excel_data_dict)
        
        _final_data = pd.DataFrame.from_dict(delete_row(excel_data_dict, columns, row_index_list)).fillna(np.nan).replace(np.nan, None)
        for each in _final_data:
            if any(_final_data[each].apply(lambda x : x.replace('.', '').isnumeric() if isinstance(x, str) else False) ):        
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


       
        with open(SCHEMAS_DIR /"sample_dict.json", "w") as outfile:
            json.dump([response_schema], outfile, default=str )
        
        
            
        return extract_jsonpath(self.records_jsonpath, input=list_of_master_file_data[-1])

    

       