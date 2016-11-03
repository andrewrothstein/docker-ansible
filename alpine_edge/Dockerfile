
FROM alpine:edge
MAINTAINER "Andrew Rothstein" andrew.rothstein@gmail.com

# install ansible
RUN apk update && apk upgrade && apk add python python-dev py2-pip build-base curl wget ca-certificates libffi-dev openssl-dev && pip install --upgrade pip && pip install --upgrade setuptools && pip install --upgrade ansible==2.2.0.0
WORKDIR /etc/ansible
# configure ansible to target the localhost -- inside the container
ADD ansible.cfg ansible.cfg
ADD localhost hosts
RUN ansible --version && ansible all --list-hosts && ansible all -m ping