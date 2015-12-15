
FROM ubuntu:vivid
MAINTAINER "Andrew Rothstein" andrew.rothstein@gmail.com

RUN apt-get update -y && apt-get install -y python python-dev python-pip python-apt aptitude && pip install ansible
ADD ansible.cfg /etc/ansible/ansible.cfg
ADD localhost /etc/ansible/hosts
RUN ansible '*' -m ping