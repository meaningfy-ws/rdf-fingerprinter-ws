#  RDF Fingerprinter
This service provides the possibility to fingerprint an RDF file or SPARQL endpoint.

# Installation

Make sure that you are running `Docker` and have the correct permissions set. If not, run the following lines to install it. 

```bash
sudo apt -y install docker.io docker-compose

sudo groupadd docker
sudo usermod -aG docker $USER
newgrp docker
```

To build 
```bash
make build-services
```
and run the containers:
```bash
make start-services
```

Install test/dev dependencies:

```bash
make install-dev
```

To run the tests:
> Make sure that fuseki is running and you have the python dependencies installed and your virtual environment activated (if you're using one).
```bash
make fuseki-create-test-dbs
make test
```


# Usage

## Start services
To run the docker containers for the `rdf-fingerprinter` `api` and `ui`, and `fuseki`:

```bash
make start-services
```

The diffing services are split into:

service | URL | info
------- | ------- | ----
`fingerprinter-api` | [localhost:4020](http://localhost:4020) | _access [localhost:4020/ui](http://localhost:4020/ui) for the swagger interface_ 
`fingerprinter-ui` | [localhost:8020](http://localhost:8020) |

## Fingerprinter API

> Go to this link [localhost:4020/ui](http://localhost:4020/ui) to access the online definition of the API.

![fingerprinter-api](resources/images/fingerprinter-api.png)

## Fingerprinter UI

> To fingerprint a file access [http://localhost:8020/fingerprint-file](http://localhost:8020/fingerprint-file)

![file-ui](resources/images/file-ui.png)


> To fingerprint a file access [http://localhost:8020/fingerprint-sparql-endpoint](http://localhost:8020/fingerprint-sparql-endpoint)

![sparql-endpoint-ui](resources/images/sparql-endpoint-ui.png)

### Report example
![sparql-endpoint-ui](resources/images/report-example.png)


## Stop services
To stop the containers run:
```bash
make stop-services
```

# Contributing
You are more than welcome to help expand and mature this project. We adhere to [Apache code of conduct](https://www.apache.org/foundation/policies/conduct), please follow it in all your interactions on the project.   

When contributing to this repository, please first discuss the change you wish to make via issue, email, or any other method with the maintainers of this repository before making a change.

## Licence 
This project is licensed under [GNU GPLv3](https://www.gnu.org/licenses/gpl-3.0.en.html) licence. 

Powered by [Meaningfy](https://github.com/meaningfy-ws).