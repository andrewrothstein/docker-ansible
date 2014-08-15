FROM ubuntu
MAINTAINER "Andrew Rothstein" andrew.rothstein@gmail.com

# use a proxy like docker run -d --name=http-replicator andrewrothstein/docker-http-replicator -p 8888:8888
# ENV http_proxy localhost:8888
# ENV https_proxy localhost:8888

RUN DEBIAN_FRONTEND=noninteractive apt-get update

RUN DEBIAN_FRONTEND=noninteractive apt-get install -y python
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y python-pip
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y python-dev
RUN pip install ansible
RUN pip install boto
RUN pip install aws
RUN pip install awscli
RUN pip install s3cmd

ADD inventories/empty /etc/ansible/hosts 
ADD ansible.cfg /etc/ansible/ansible.cfg
VOLUME ["/inventories"]
VOLUME ["/playbooks"]
