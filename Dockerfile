FROM ubuntu:trusty
MAINTAINER "Andrew Rothstein" andrew.rothstein@gmail.com

# use a proxy like docker run -d --name=http-replicator andrewrothstein/docker-http-replicator -p 8888:8888
# ENV http_proxy http://192.168.59.103:8888
# ENV https_proxy http://192.168.59.103:8888

RUN DEBIAN_FRONTEND=noninteractive apt-get update

RUN DEBIAN_FRONTEND=noninteractive apt-get install -y python python-pip python-dev
RUN pip install ansible boto aws awscli s3cmd

ADD ansible.cfg /etc/ansible/ansible.cfg
ADD localhost /etc/ansible/hosts
RUN ansible '*' -m ping