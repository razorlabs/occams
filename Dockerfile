# Dockerfile for for web application service
#
# Installs the web application in "edit" mode so that modifications are
# immediately reflected .
#
# DO NOT USE FOR PRODUCTION

FROM python:2.7.17-slim

RUN apt-get update \
    && apt-get install curl wget git gcc libmagic1 -y \
    && curl -sL https://deb.nodesource.com/setup_10.x  | bash - \
    && apt-get install nodejs -y \
    && apt-get clean

RUN npm install -g less \
    && npm install -g bower \
    && echo '{ "allow_root": true }' > /root/.bowerrc

RUN wget https://github.com/jwilder/dockerize/releases/download/v0.2.0/dockerize-linux-amd64-v0.2.0.tar.gz \
    && tar -C /usr/local/bin -xzvf dockerize-linux-amd64-v0.2.0.tar.gz

WORKDIR /app

# Install dependencies first so they are cached
COPY ./constraints.txt ./requirements*.txt ./
RUN pip install --upgrade -c constraints.txt -r requirements-develop.txt

ADD . /app
RUN pip install -e .
