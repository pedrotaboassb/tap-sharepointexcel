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

_Auth = Callable[[requests.PreparedRequest], requests.PreparedRequest]
SCHEMAS_DIR = Path(__file__).parent / Path("./schemas")


class sharepointexcelStream(RESTStream):
    """sharepointexcel stream class."""

    @property
    def url_base(self) -> str:
        """Return the API URL root, configurable via tap settings."""
        # TODO: hardcode a value here, or retrieve it from self.config
        return "https://graph.microsoft.com/v1.0/sites/storebrand.sharepoint.com,5eacacfb-9932-40b7-a16c-4fa9b74d5d68,050842a3-92f8-4445-9412-7dd46c05616d/drives/b!-6ysXjKZt0ChbE-pt01daKNCCAX4kkVElBJ91GwFYW3f3z6xi1K0QriBhDbkk-x0"

    records_jsonpath = "$[*]"  # Or override `parse_response`.

    # Set this value or override `get_new_paginator`.
    #next_page_token_jsonpath = "$.next_page"  # noqa: S105

   
    @property
    def authenticator(self) -> BearerTokenAuthenticator:
        self.logger.info('The Bearer!!')    
        return BearerTokenAuthenticator.create_for_stream(self, token=self.config.get('auth_token'))
    

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


    


