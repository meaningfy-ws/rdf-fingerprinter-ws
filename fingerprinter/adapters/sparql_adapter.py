#!/usr/bin/python3

# sparql_adapter.py
# Date:  17/10/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com 

"""
Adapter for the SPARQL wrapper library
"""
from json import JSONDecodeError
from urllib.parse import urljoin

from requests.auth import HTTPBasicAuth
from requests_toolbelt import MultipartEncoder

from fingerprinter import config
from fingerprinter.adapters.helpers import get_file_format


class FusekiException(Exception):
    """
        An exception when Fuseki server interaction has failed.
    """


class SPARQLWrapperAdapter:
    def __init__(self, triplestore_service_url: str, http_client):
        self.triplestore_service_url = triplestore_service_url
        self.http_client = http_client

    def create_dataset(self, dataset_name: str):
        """
            Create the dataset for the Fuseki store
        :param dataset_name: The dataset identifier. This should be short alphanumeric string uniquely
        identifying the dataset
        """
        if not dataset_name:
            raise ValueError('Dataset name cannot be empty.')

        data = {
            'dbType': 'tdb',
            'dbName': dataset_name
        }

        response = self.http_client.post(urljoin(self.triplestore_service_url, f"/$/datasets"),
                                         auth=HTTPBasicAuth(config.FUSEKI_USERNAME, config.FUSEKI_PASSWORD),
                                         data=data)

        if response.status_code == 409:
            raise FusekiException('A dataset with this name already exists.')

    def delete_dataset(self, dataset_name: str):
        """
            Delete the dataset from the Fuseki store
        :param dataset_name: The dataset identifier. This should be short alphanumeric string uniquely
        identifying the dataset
        """
        response = self.http_client.delete(urljoin(self.triplestore_service_url, f"/$/datasets/{dataset_name}"),
                                           auth=HTTPBasicAuth(config.FUSEKI_USERNAME,
                                                              config.FUSEKI_PASSWORD))

        if response.status_code == 404:
            raise FusekiException('The dataset to be deleted doesn\'t exist.')

    def upload_file(self, dataset_name: str, file: str) -> dict:
        """
            Upload the file to the Fuseki dataset
        :param dataset_name: The dataset identifier. This should be short alphanumeric string uniquely
        :param file:
        :return a dict of the structure:
        {
          "count": 36286,
          "tripleCount": 36286,
          "quadCount": 0
        }
        """
        # as mentioned in the official requests documentation
        # https://requests.readthedocs.io/en/master/user/quickstart/#post-a-multipart-encoded-file
        # for larger requests, it has to be streamed, which requests doesn't support by default.
        # requests_toolbelt solution - https://toolbelt.readthedocs.io/en/latest/uploading-data.html
        multipart_encoder = MultipartEncoder(
            fields={'file': (file, open(file, 'rb'), get_file_format(file))}
        )

        response = self.http_client.post(urljoin(self.triplestore_service_url, f"/{dataset_name}/data"),
                                         data=multipart_encoder,
                                         auth=HTTPBasicAuth(config.FUSEKI_USERNAME,
                                                            config.FUSEKI_PASSWORD),
                                         headers={'Content-Type': multipart_encoder.content_type})

        if response.status_code != 200:
            raise FusekiException(f'Error connecting to fuseki: {response.text}')

        try:
            return response.json()
        except JSONDecodeError:
            return response.text
