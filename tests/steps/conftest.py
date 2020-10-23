#!/usr/bin/python3

# conftest.py
# Date:  22/10/2020
# Author: Mihai Coșleț
# Email: coslet.mihai@gmail.com 

"""
Helper fixtures for steps implementation
"""

from pathlib import Path

import pytest
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver


@pytest.fixture(scope="session")
def scenario_context():
    return {}


@pytest.fixture(scope="session")
def scenario_context():
    return {}


@pytest.fixture(scope="session")
def browser():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_driver_args = ["--whitelisted-ips=", "--log-path=chromedriver.log"]
    # location to the chromedriver
    path_to_driver = str(Path(__file__).parents[1] / 'resources/chromedriver')
    _browser = WebDriver(executable_path=path_to_driver,
                         chrome_options=chrome_options,
                         service_args=chrome_driver_args)
    yield _browser
    _browser.close()
    _browser.quit()
