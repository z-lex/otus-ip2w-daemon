Otus ip2w daemon
================

CentOS-based uWSGI daemon that returns weather info associated with the IP
address passed in the HTTP request. Docker container with daemon handles GET
requests on the `/ip2w/<IPv4-address>` endpoint.

# Usage example

```bash
$ curl 0.0.0.0:4000/ip2w/94.19.73.10
```

## Dependencies

### Runtime dependencies

#### Host

* docker
* git
 
#### Container

* systemd
* nginx/1.20.1
* uwsgi
* uwsgi-plugin-python3
* python 3.6 
* python3-sphinx
* python3-requests

### Build dependencies

#### Container

* rpm-build
* rpmdevtools
* pyp2rpm

## Configuration

Set the correct tokens for [openweathermap](https://openweathermap.org/current)
and [ipinfo](https://ipinfo.io/developers) sevices in the `ip2w.ini`
configuration file before building the docker image. Or alternatively, you can
do this later by editing `/usr/local/etc/ip2w.ini` and restarting the ip2w
service.

## Running from Docker

```shell
$ git clone https://github.com/z-lex/otus-ip2w-daemon && cd otus-ip2w-daemon
$ docker-compose up
```
### Possible problems

Doesn't work on Ubuntu 21.04 and newer hosts, systemctl calls inside the
CentOS container return messages like "Failed to get D-Bus connection: Operation not permitted".
Reason: CentOS 7 container does not understand unified cgroup hierarchy (cgroup v2) added
in Ubuntu 21.04 release.

Solution: 

1. Edit `/etc/default/grub` to switch off cgroup v2 for systemd:
```bash
GRUB_CMDLINE_LINUX="systemd.unified_cgroup_hierarchy=0"
```

2. Update grub config:
```bash
sudo update-grub
```

3. Reboot

Related links:

* [centos systemd integration](https://github.com/docker-library/docs/tree/master/centos#systemd-integration)
* [comment on lxc github](https://github.com/lxc/lxc/issues/4072#issuecomment-1034254421)
* [redhat bugzilla](https://bugzilla.redhat.com/show_bug.cgi?id=1970237)
* [Ubuntu 21.04 Release notes](https://discourse.ubuntu.com/t/impish-indri-release-notes/21951)


## Related documentation:
* uWSGI: https://uwsgi-docs.readthedocs.io/en/latest/
* CentOS 7: https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/7