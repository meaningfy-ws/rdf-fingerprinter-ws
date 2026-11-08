#!/usr/bin/python3

# sparql_adapter.py
# Date:  17/10/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com

"""
Adapter for the SPARQL wrapper library
"""

from abc import ABC, abstractmethod
from json import JSONDecodeError
from typing import Any
from urllib.parse import urljoin

from requests.auth import HTTPBasicAuth

from fingerprinter.adapters.helpers import get_file_format
from fingerprinter.config import config


class FusekiException(Exception):  # noqa: N818  (public name kept; stage 2 replaces this adapter)
    """
    An exception when Fuseki server interaction has failed.
    """


class AbstractSPARQLAdapter(ABC):
    """
    Abstract adapter for performing operations on a triple store server
    """

    @abstractmethod
    def create_dataset(self, dataset_name: str):
        """
            Create the dataset for the __ store
        :param dataset_name: The dataset identifier. This should be short alphanumeric string uniquely
        identifying the dataset
        """

    @abstractmethod
    def delete_dataset(self, dataset_name: str):
        """
            Delete the dataset from the __ store
        :param dataset_name: The dataset identifier. This should be short alphanumeric string uniquely
        identifying the dataset
        """

    @abstractmethod
    def get_dataset(self, dataset_name: str) -> Any:
        """
            Get dataset general info
        :param dataset_name: The dataset identifier. This should be short alphanumeric string uniquely
        :return: dataset info
        """

    @abstractmethod
    def upload_file(self, dataset_name: str, file_path: str):
        """
            Upload a data file to the dataset
        :param dataset_name: The dataset identifier. This should be short alphanumeric string uniquely
        :param file_path: path to the data file to be uploaded
        """


class FusekiSPARQLAdapter(AbstractSPARQLAdapter):
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
            raise ValueError("Dataset name cannot be empty.")

        data = {"dbType": "tdb", "dbName": dataset_name}

        response = self.http_client.post(
            urljoin(self.triplestore_service_url, "/$/datasets"),
            auth=HTTPBasicAuth(
                config.RDF_FINGERPRINTER_FUSEKI_USERNAME, config.RDF_FINGERPRINTER_FUSEKI_PASSWORD
            ),
            data=data,
        )

        if response.status_code == 409:
            raise FusekiException("A dataset with this name already exists.")

    def delete_dataset(self, dataset_name: str):
        """
            Delete the dataset from the Fuseki store
        :param dataset_name: The dataset identifier. This should be short alphanumeric string uniquely
        identifying the dataset
        """
        response = self.http_client.delete(
            urljoin(self.triplestore_service_url, f"/$/datasets/{dataset_name}"),
            auth=HTTPBasicAuth(
                config.RDF_FINGERPRINTER_FUSEKI_USERNAME, config.RDF_FINGERPRINTER_FUSEKI_PASSWORD
            ),
        )

        if response.status_code == 404:
            raise FusekiException("The dataset to be deleted doesn't exist.")

    def get_dataset(self, dataset_name: str) -> Any:
        """
            Get dataset general info
        :param dataset_name: The dataset identifier. This should be short alphanumeric string uniquely
        :return: dataset info
        """
        response = self.http_client.get(
            urljoin(self.triplestore_service_url, f"/$/datasets/{dataset_name}"),
            auth=HTTPBasicAuth(
                config.RDF_FINGERPRINTER_FUSEKI_USERNAME, config.RDF_FINGERPRINTER_FUSEKI_PASSWORD
            ),
        )
        if response.status_code == 404:
            raise FusekiException(f"The dataset <{dataset_name}> doesn't exist.")
        if response.status_code != 200:
            raise FusekiException(f"Error connecting to fuseki: {response.text}")

        try:
            return response.json()
        except JSONDecodeError:
            return response.text

    def upload_file(self, dataset_name: str, file_path: str) -> Any:
        """
            Upload the file to the Fuseki dataset
        :param dataset_name: The dataset identifier. This should be short alphanumeric string uniquely
        :param file_path: path to the data file to be uploaded
        :return a dict of the structure:
        {
          "count": 36286,
          "tripleCount": 36286,
          "quadCount": 0
        }
        """
        # the file object is streamed as the request body (Graph Store Protocol), so large files are not loaded in memory
        with open(file_path, "rb") as data:
            response = self.http_client.post(
                urljoin(self.triplestore_service_url, f"/{dataset_name}/data"),
                data=data,
                auth=HTTPBasicAuth(
                    config.RDF_FINGERPRINTER_FUSEKI_USERNAME,
                    config.RDF_FINGERPRINTER_FUSEKI_PASSWORD,
                ),
                headers={"Content-Type": get_file_format(file_path)},
            )

        if not 200 <= response.status_code < 300:
            raise FusekiException(f"Error connecting to fuseki: {response.text}")

        try:
            return response.json()
        except JSONDecodeError:
            return response.text
