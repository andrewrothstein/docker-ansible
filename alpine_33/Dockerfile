
FROM alpine:3.3
MAINTAINER "Andrew Rothstein" andrew.rothstein@gmail.com

# install ansible
RUN apk update && apk upgrade && apk add python python-dev py-pip build-base && pip install --upgrade pip && pip install ansible==2.0.0.2
RUN ansible --version

# configure ansible to target the localhost -- inside the container
ADD ansible.cfg /etc/ansible/ansible.cfg
ADD localhost /etc/ansible/hosts
RUN ansible '*' -m ping
