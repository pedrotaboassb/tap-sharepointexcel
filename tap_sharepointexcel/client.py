"""REST client handling, including sharepointexcelStream base class."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Iterable

import requests
from singer_sdk.authenticators import BearerTokenAuthenticator, SimpleAuthenticator
from singer_sdk.helpers.jsonpath import extract_jsonpath
from singer_sdk.pagination import BaseAPIPaginator  # noqa: TCH002
from singer_sdk.streams import RESTStream

from .utils import find_newest_file, find_row_with_target_string, delete_row

import json

import pandas as pd

from datetime import datetime

import io 

from azure.identity import DefaultAzureCredential, ManagedIdentityCredential

_Auth = Callable[[requests.PreparedRequest], requests.PreparedRequest]
SCHEMAS_DIR = Path(__file__).parent / Path("./schemas")


class sharepointexcelStream(RESTStream):
    """sharepointexcel stream class."""

    @property
    def url_base(self) -> str:
        """Return the API URL root, configurable via tap settings."""
        # TODO: hardcode a value here, or retrieve it from self.config
        return self.config["api_url"] 

    records_jsonpath = "$[*]"  # Or override `parse_response`.

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


    


