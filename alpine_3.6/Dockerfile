FROM alpine:3.6
MAINTAINER "Andrew Rothstein" andrew.rothstein@gmail.com

# install ansible
RUN apk update \
 && apk upgrade \
 && apk add \
   python2 \
   py2-pip \
   py2-crypto \
   py2-cffi \
   py2-yaml \
   py2-jinja2 \
   py2-paramiko \
   ca-certificates \
 && pip install --upgrade pip \
 && pip install ansible==2.5.0.0 \
 && rm -rf /var/cache/apk/*

WORKDIR /etc/ansible
# configure ansible to target the localhost -- inside the container
ADD ansible.cfg ansible.cfg
ADD localhost hosts

RUN ansible --version \
 && ansible all --list-hosts \
 && ansible all -m ping
