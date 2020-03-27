# Dockerfile for for web application service
#
# Installs the web application in "edit" mode so that modifications are
# immediately reflected .
#

FROM python:3.7.7-slim AS base

ENV NODE_MAJOR_VERSION=12
RUN apt-get update \
    && apt-get install curl wget git libmagic1 -y \
    && curl -sL https://deb.nodesource.com/setup_${NODE_MAJOR_VERSION}.x | bash - \
    && apt-get install nodejs -y \
    && apt-get clean

RUN npm install -g less \
    && npm install -g bower \
    && echo '{ "allow_root": true }' > /root/.bowerrc

ENV DOCKERIZE_VERSION v0.6.1
RUN wget https://github.com/jwilder/dockerize/releases/download/$DOCKERIZE_VERSION/dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && tar -C /usr/local/bin -xzvf dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && rm dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz

ENV ENVIRONMENT "development"

# Don't buffer STDOUT so that logs show immediately
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Install requirements first before copying source files
COPY ./constraints.txt ./requirements*.txt ./
RUN pip install \
    -c constraints.txt \
    -r $( [ "$ENVIRONMENT" = "development" ] && echo "requirements-develop.txt" || echo "requirements.txt" )

ADD . ./

FROM base AS development
ENV PYTHONDONTWRITEBYTECODE 1
ENV ENVIRONMENT "development"
RUN pip install -e .

FROM base AS production
ENV ENVIRONMENT "production"
RUN pip install .
