
FROM centos:7.1.1503
MAINTAINER "Andrew Rothstein" andrew.rothstein@gmail.com

RUN yum update -y && yum install -y python python-devel python-pip bzip2 file findutils git gzip mercurial procps subversion sudo tar debianutils unzip xz-utils zip && yum -y groupinstall "Development tools" && pip install ansible
ADD ansible.cfg /etc/ansible/ansible.cfg
ADD localhost /etc/ansible/hosts
RUN ansible '*' -m ping