FROM python:3.8.5-buster

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY . /usr/src/app

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

CMD gunicorn -w 2 --bind 0.0.0.0:${RDF_FINGERPRINTER_API_PORT} --reload --log-level=debug fingerprinter.entrypoints.api.run:app