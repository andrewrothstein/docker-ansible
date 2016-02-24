
FROM ubuntu:vivid
MAINTAINER "Andrew Rothstein" andrew.rothstein@gmail.com

# install ansible
RUN apt-get update -y && apt install -y python python-dev python-pip python-apt aptitude curl wget ca-certificates && apt-get clean && pip install --upgrade pip && pip install ansible==2.0.0.2
RUN ansible --version

# configure ansible to target the localhost -- inside the container
ADD ansible.cfg /etc/ansible/ansible.cfg
ADD localhost /etc/ansible/hosts
RUN ansible '*' -m ping
