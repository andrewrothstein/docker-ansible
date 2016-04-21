
FROM alpine:3.3
MAINTAINER "Andrew Rothstein" andrew.rothstein@gmail.com

# install ansible
RUN apk update && apk upgrade && apk add python python-dev py-pip build-base curl wget ca-certificates && pip install --upgrade pip && pip install ansible==2.0.2.0
WORKDIR /etc/ansible
# configure ansible to target the localhost -- inside the container
ADD ansible.cfg ansible.cfg
ADD localhost hosts
RUN ansible --version && ansible all --list-hosts && ansible all -m ping