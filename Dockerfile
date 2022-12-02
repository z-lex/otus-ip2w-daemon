FROM centos:7

# https://github.com/docker-library/docs/tree/master/centos#systemd-integration
ENV container docker

# install the EPEL repository to get access to a wider range of packages
RUN yum install -y epel-release && yum update -y && \
    yum install -y gcc systemd systemd-rpm-macros nginx python3 python3-devel python3-pip && \
    yum install -y rpm-build rpmdevtools && \
    yum install -y git vim vifm

RUN pip3 install pyp2rpm

# install python dependencies for ip2w rpm package
RUN yum install -y python3-sphinx && \
    yum install -y python3-requests && \
    yum install -y uwsgi uwsgi-plugin-python3

RUN yum clean all

# https://github.com/docker-library/docs/tree/master/centos#systemd-integration
RUN (cd /lib/systemd/system/sysinit.target.wants/; for i in *; do [ $i == \
	systemd-tmpfiles-setup.service ] || rm -f $i; done); \
	rm -f /lib/systemd/system/multi-user.target.wants/*; \
	rm -f /etc/systemd/system/*.wants/*; \
	rm -f /lib/systemd/system/local-fs.target.wants/*; \
	rm -f /lib/systemd/system/sockets.target.wants/*udev*; \
	rm -f /lib/systemd/system/sockets.target.wants/*initctl*; \
	rm -f /lib/systemd/system/basic.target.wants/*; \
	rm -f /lib/systemd/system/anaconda.target.wants/*

VOLUME [ "/sys/fs/cgroup" ]

COPY . /app
WORKDIR /app

# build and install RPM package
RUN make && make install

# can't enable the ip2w service from the .spec file: operation not permitted,
# enabling manually:
RUN systemctl enable ip2w

# enable nginx
COPY ./nginx.conf /etc/nginx/nginx.conf
RUN systemctl enable nginx

EXPOSE 80
CMD ["/usr/sbin/init"]