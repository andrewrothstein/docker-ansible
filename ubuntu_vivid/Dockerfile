
FROM ubuntu:vivid
MAINTAINER "Andrew Rothstein" andrew.rothstein@gmail.com

# install ansible
RUN apt-get update -y && apt install -y python python-dev python-pip python-apt aptitude curl wget ca-certificates && apt-get clean && pip install --upgrade pip && pip install ansible==2.0.0.2
WORKDIR /etc/ansible
# configure ansible to target the localhost -- inside the container
ADD ansible.cfg ansible.cfg
ADD localhost hosts
RUN ansible --version && ansible all --list-hosts && ansible all -m ping