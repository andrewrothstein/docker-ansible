#!/usr/bin/env python

import argparse
from jinja2 import Environment
from subprocess import call
import os
import shutil

Dockerfile = """
FROM {{baseimage}}
MAINTAINER "Andrew Rothstein" andrew.rothstein@gmail.com

RUN {{pkg_update}} && {{python_and_pip_install}} && pip install ansible
ADD ansible.cfg /etc/ansible/ansible.cfg
ADD localhost /etc/ansible/hosts
RUN ansible '*' -m ping
"""

def copy_file(tag, file) :
	shutil.copyfile(file, '{0}/{1}'.format(tag, file))

def copy_artifacts(tag) :
	copy_file(tag, 'ansible.cfg')
	copy_file(tag, 'localhost')

def write(params) :
	tag = params["tag"]
	if (not os.path.isdir(tag)) :
		os.mkdir(tag)
	fq_dockerfile = "{0}/Dockerfile".format(tag) 
	print "writing {0}...".format(fq_dockerfile)
	f = open(fq_dockerfile, 'w')
	f.write(Environment().from_string(Dockerfile).render(params))
	f.close()
	copy_artifacts(tag)
	
def build(params) :
	tag = params["tag"]
	container_name = 'andrewrothstein/docker-ansible'
	print "building the {0}:{1} container...".format(container_name, tag)
	cmd = ['docker', 'build',
				 '-t', '{0}:{1}'.format(container_name, tag),
				 tag]
	os.chdir
	call(cmd, shell=False)

def push(registry) :
	def pusher(params) :
		tag = params["tag"]
		container_name = 'andrewrothstein/docker-ansible'
		url = "{0}/{1}:{2}".format(registry, container_name, tag)
		print "pushing building to {0}...".format(url)
		cmd = ['docker', 'push', url]
		os.chdir
		call(cmd, shell=False)
	return pusher

def pull(params) :
	baseimg = params["baseimage"]
	cmd = ['docker', 'pull', baseimg]
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
	parser.add_argument(
		'-p',
		'---push',
		help='push to the given docker registry'
		)
	parser.add_argument(
		'-f',
		'--pull',
		action='store_true',
		help='pull base images'
		)
	
	args = parser.parse_args()
	
	apt_update = 'apt-get update -y'
	apt_python_and_pip_install = 'apt-get install -y python python-dev python-pip python-apt aptitude'

	yum_update = 'yum update -y'
	yum_fedora_python_and_pip_install = 'yum install -y python python-devel python-pip bzip2 file findutils git gzip mercurial procps subversion sudo tar debianutils unzip xz-utils zip && yum -y groupinstall "Development tools"'
	yum_centos_python_and_pip_install = 'yum install -y epel-release && yum install -y python python-devel python-pip bzip2 file findutils git gzip mercurial procps subversion sudo tar debianutils unzip xz-utils zip && yum -y groupinstall "Development tools"'

	configs = [
		{ "baseimage" : "fedora:21",
			"tag" : "fedora_21",
			"pkg_update" : yum_update,
			"python_and_pip_install" : yum_fedora_python_and_pip_install
		},
		{ "baseimage" : "centos:7.1.1503",
			"tag" : "centos_7.1.1503",
			"pkg_update" : yum_update,
			"python_and_pip_install" : yum_centos_python_and_pip_install,
		},
		{ "baseimage" : "ubuntu:trusty",
			"tag" : "ubuntu_trusty",
			"pkg_update" : apt_update,
			"python_and_pip_install" : apt_python_and_pip_install
		},
		{ "baseimage" : "ubuntu:vivid",
			"tag" : "ubuntu_vivid",
			"pkg_update" : apt_update,
			"python_and_pip_install" : apt_python_and_pip_install
		},
		{ "baseimage" : "ubuntu:wily",
			"tag" : "ubuntu_wily",
			"pkg_update" : apt_update,
			"python_and_pip_install" : apt_python_and_pip_install
		}
	]

	if (args.pull) :
		map(pull, configs)
	
	if (args.write) :
		map(write, configs)

	if (args.build) :
		map(build, configs)

	if (args.push) :
		map(push(args.push), configs)
