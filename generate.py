#!/usr/bin/env python

import argparse
from jinja2 import Environment
import multiprocessing

Dockerfile = """
FROM {{baseimage}}
MAINTAINER "Andrew Rothstein" andrew.rothstein@gmail.com

{% if pkg_setup %}
RUN {{pkg_setup}}
{% endif %}
RUN {{pkg_update}} && {{pkg_ansible_install}}
ADD ansible.cfg /etc/ansible/ansible.cfg
ADD localhost /etc/ansible/hosts
RUN ansible '*' -m ping
"""

def checkout(tag) :
	print "checking out {0} branch...".format(tag)
	cmd = ['git', 'checkout', '-b', tag]
	call(cmd, shell=False)

def commit_dockerfile(msg) :
	print "committing..."
	call(['git', 'add', 'Dockerfile'], shell=False)
	call(['git', 'commit', '-m', msg], shell=False)
	
def write(params) :
	tag = params["tag"]
	checkout(tag)
	print "writing Dockerfile for tag {0}".format(tag)
	f = open('Dockerfile', 'w')
	f.write(Environment().from_string(Dockerfile).render(params))
	f.close()
	commit_dockerfile('update to Dockerfile for {0} tag'.format(tag))

def build(params) :
	tag = params["tag"]
	checkout(tag)
	container_name = 'andrewrothstein/docker-ansible'
	print "building the {0}:{1} container...".format(container_name, tag)
	cmd = ['docker', 'build',
				 '-t', '{0}:{1}'.format(container_name, tag),
				 '.']
	call(cmd, shell=False)
	
if __name__ == '__main__' :

	parser = argparse.ArgumentParser(
		description='generates a bunch of Docker base containers for use with Ansible'
	)
	parser.add_argument(
		'-w',
		'--write',
		action='store_true',
		help='write the Dockerfiles'
	)
	parser.add_argument(
		'-b',
		'--build',
		action='store_true',
		help='build the Docker containers'
	)
	args = parser.parse_args()
	
	apt_update = 'apt-get update -y'
	apt_ansible_install = 'apt-get install -y ansible'

	yum_update = 'yum update -y'
	yum_ansible_install = 'yum install -y ansible'

	configs = [
		{ "baseimage" : "fedora:21",
			"tag" : "fedora_21",
			"pkg_update" : yum_update,
			"pkg_ansible_install" : yum_ansible_install
		},
		{ "baseimage" : "centos:7.1.1503",
			"tag" : "centos_7.1.1503",
			"pkg_update" : yum_update,
			"pkg_ansible_install" : yum_ansible_install,
			"pkg_setup" : 'rpm -iUvh http://dl.fedoraproject.org/pub/epel/7/x86_64/e/epel-release-7-5.noarch.rpm'
		},
		{ "baseimage" : "ubuntu:trusty",
			"tag" : "ubuntu_trusty",
			"pkg_update" : apt_update,
			"pkg_ansible_install" : apt_ansible_install
		} ]

	pool = multiprocessing.Pool()
	
	if (args.write) :
		pool.map(write, configs)

	if (args.build) :
		pool.map(build, configs)
	
