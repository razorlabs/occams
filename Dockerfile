# Dockerfile for for web application service
#
# Installs the web application in "edit" mode so that modifications are
# immediately reflected .
#
# DO NOT USE FOR PRODUCTION

FROM centos:7

RUN yum update -y
RUN yum groupinstall -y 'Development Tools'
RUN yum install -y epel-release
RUN yum install -y python-devel python-pip
RUN yum install -y wget

# Install bash script to allow us to wait for dependent services to be "ready"
RUN wget https://github.com/jwilder/dockerize/releases/download/v0.2.0/dockerize-linux-amd64-v0.2.0.tar.gz \
    && tar -C /usr/local/bin -xzvf dockerize-linux-amd64-v0.2.0.tar.gz

RUN yum install -y nodejs npm jsmin
RUN npm install -g less && npm install -g bower
RUN echo '{ "allow_root": true }' > /root/.bowerrc

# Install dependencies first so they are cached
COPY ./requirements*.txt /tmp/
RUN pip install --upgrade -r /tmp/requirements-develop.txt

ADD . /app
WORKDIR /app
RUN pip install -e .


