# This Makefile is responsible for building and installing RPMs and must be
# used inside the CentOS 7 container

PACKAGER = $(shell git config user.name) <$(shell git config user.email)>

# package info
PACKAGE_VERSION = $(shell python3 setup.py -V)
PACKAGE_NAME = $(shell python3 setup.py --name)
PACKAGE_FULLNAME = $(shell python3 setup.py --fullname)

GIT_VERSION=$(shell git rev-list HEAD -n 1)
GIT_BRANCH=$(shell git name-rev --name-only HEAD)

RPMBUILD_TOPDIR = /app/rpmbuild/
RPMS_DIR = $(RPMBUILD_TOPDIR)/RPMS
SPECS_DIR = $(RPMBUILD_TOPDIR)/SPECS
MAIN_SPECFILE = ip2w.spec

PYP2RPM_ENV = LC_ALL=en_US.utf8 LANG=en_US.utf8
PYP2RPM_FLAGS = -oepel7 -tepel7 -b3 -d $(RPMBUILD_TOPDIR)

# dependencies that must be built from PyPI packages manually using pyp2rpm
CACHETOOLS_RPM = $(RPMS_DIR)/noarch/python36-cachetools-3.1.1-1.el7.noarch.rpm
IPINFO_RPM = $(RPMS_DIR)/noarch/python36-ipinfo-3.0.0-1.el7.noarch.rpm
MANUAL_RPMS = $(CACHETOOLS_RPM) $(IPINFO_RPM)

TARGET_RPM = $(RPMS_DIR)/x86_64/ip2w-0.0.1-1.x86_64.rpm

.PHONY: install install-manual-deps clean test

all: $(TARGET_RPM)

# ~/.rpmmacros is required by rpmdev-setuptree and pyp2rpm
$(HOME)/.rpmmacros:
	echo "%_topdir $(RPMBUILD_TOPDIR)" > $@

$(RPMBUILD_TOPDIR): $(HOME)/.rpmmacros
	rpmdev-setuptree
	chmod -R a+rw $@

$(SPECS_DIR)/python-cachetools.spec: $(RPMBUILD_TOPDIR)
	$(PYP2RPM_ENV) pyp2rpm $(PYP2RPM_FLAGS) -v3.1.1 -s cachetools

$(SPECS_DIR)/python-ipinfo.spec: $(RPMBUILD_TOPDIR)
	$(PYP2RPM_ENV) pyp2rpm $(PYP2RPM_FLAGS) -v3.0.0 -s ipinfo

$(CACHETOOLS_RPM): $(SPECS_DIR)/python-cachetools.spec
	rpmbuild -ba --verbose --clean $?

$(IPINFO_RPM): $(SPECS_DIR)/python-ipinfo.spec
	rpmbuild -ba --verbose --clean $?

install-manual-deps: $(MANUAL_RPMS)
	echo "installing manually built dependencies..."
	yum localinstall -y $^

# before creating the main rpm, all build dependencies must be installed
$(TARGET_RPM): install-manual-deps
	echo "creating source tarball for $@..."
	$(shell git archive --format=tar.gz --prefix=$(PACKAGE_FULLNAME)/ \
		$(GIT_BRANCH) > $(RPMBUILD_TOPDIR)/SOURCES/$(PACKAGE_FULLNAME).tar.gz)

	echo "building $@..."
	rpmbuild -ba --verbose --clean $(MAIN_SPECFILE) \
	  --define "package_name $(PACKAGE_NAME)" \
	  --define "package_fullname $(PACKAGE_FULLNAME)" \
	  --define "package_version $(PACKAGE_VERSION)" \
	  --define "packager $(PACKAGER)" \
	  --define "git_version $(GIT_VERSION)" \
	  --define "git_branch $(GIT_BRANCH)"

install: $(RPM_TOPDIR)
	yum localinstall -y $(TARGET_RPM) || true

clean:
	rm -rf $(RPMBUILD_TOPDIR)
	rm -rf $(HOME)/.rpmmacros

test:
	python3 -m unittest tests
