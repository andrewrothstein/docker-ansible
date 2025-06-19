docker-ansible
==============
![Build Status](https://github.com/andrewrothstein/docker-ansible/actions/workflows/build.yml/badge.svg)

* Base container images ansible installed with uv
* Dagger CI for building the images

## Example CLI Usage

To build and publish a docker-ansible image for Alpine 3.20:

```bash
python3 -m docker_ansible.cli build-and-publish \
  --os alpine \
  --os-ver 3.20 \
  --target-image-semver 1.0.0 \
  --dockerhub-username <your-dockerhub-username> \
  --dockerhub-password <your-dockerhub-password>
```

Replace the username and password with your Docker Hub credentials. Additional options are available; run:

```bash
python3 -m docker_ansible.cli build-and-publish --help
```

to see all available options.

Andrew Rothstein <andrew.rothstein@gmail.com>
