FROM ubuntu:latest
MAINTAINER "Andrew Rothstein" andrew.rothstein@gmail.com

RUN apt-get update \
 && apt-get install -y python python-pip python-dev \
 && pip install ansible boto aws awscli s3cmd

ADD ansible.cfg /etc/ansible/ansible.cfg
ADD localhost /etc/ansible/hosts
RUN ansible '*' -m ping