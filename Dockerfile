FROM python:2.7
MAINTAINER "Andrew Rothstein" andrew.rothstein@gmail.com

RUN pip install ansible boto aws awscli s3cmd
ADD ansible.cfg /etc/ansible/ansible.cfg
ADD localhost /etc/ansible/hosts
RUN ln -s /usr/local/bin/python /usr/bin/python
RUN ansible '*' -m ping