FROM alpine:3.3
MAINTAINER "Andrew Rothstein" andrew.rothstein@gmail.com

# install ansible
RUN apk update \
 && apk upgrade \
 && apk add \
   python \
   python-dev \
   py-pip \
   build-base \
   libffi-dev \
   openssl-dev \
   ca-certificates \
 && pip install --upgrade pip \
 && pip install ansible==2.3.1.0 \
 && apk del \
   build-base \
   libffi-dev \
   openssl-dev \
 && rm -rf /var/cache/apk/*

WORKDIR /etc/ansible
# configure ansible to target the localhost -- inside the container
ADD ansible.cfg ansible.cfg
ADD localhost hosts

RUN ansible --version \
 && ansible all --list-hosts \
 && ansible all -m ping
