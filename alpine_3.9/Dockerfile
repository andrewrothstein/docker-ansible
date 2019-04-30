FROM alpine:3.9
MAINTAINER "Andrew Rothstein" andrew.rothstein@gmail.com

# install ansible
ADD ansible-install /usr/bin/ansible-install
RUN /usr/bin/ansible-install

# configure ansible to target the localhost -- inside the container
ADD ansible.cfg /etc/ansible/ansible.cfg

RUN mkdir -p /etc/ansible/inventories
ADD localhost /etc/ansible/inventories/hosts


ADD ansible-ping-localhost /usr/bin/ansible-ping-localhost
RUN  /usr/bin/ansible-ping-localhost
