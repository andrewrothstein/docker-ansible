docker-ansible
==============
![Build Status](https://github.com/andrewrothstein/docker-ansible/actions/workflows/build.yml/badge.svg)

* Base container images ansible installed with uv
* Dagger CI for building the images

## Example CLI Usage

To build a docker-ansible image for Ubuntu Noble:

```bash
dagger call build --os=ubuntu --os-ver=noble
```
