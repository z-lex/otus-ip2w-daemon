License:        BSD
Vendor:         Otus
Group:          Otus-students
URL:            https://github.com/z-lex/otus-ip2w-daemon
Source0:        %{package_fullname}.tar.gz
BuildRoot:      %{_tmppath}/%{package_fullname}
Name:           %{package_name}
Version:        %{package_version}
Release:        1
BuildArch:      x86_64

BuildRequires: systemd
BuildRequires: systemd-rpm-macros
BuildRequires: python3
BuildRequires: python3-devel
BuildRequires: python3-setuptools
BuildRequires: python%{python3_pkgversion}-requests
BuildRequires: python%{python3_pkgversion}-ipinfo

Requires: python3
Requires: python%{python3_pkgversion}-requests
Requires: python%{python3_pkgversion}-ipinfo
Requires: uwsgi
Requires: uwsgi-plugin-python3

%systemd_requires

Summary:  Otus weather uWSGI daemon

%define __etcdir        /usr/local/etc
%define __logdir        /val/log/
%define __bindir        /usr/local/ip2w/
%define __systemddir	%{_unitdir}


%description
Otus weather uWSGI daemon

Git version: %{git_version} (branch: %{git_branch})

%prep
%autosetup -p1 -n ip2w-%{version}

%build
%{py3_build}

%install
%{py3_install}

# ip2w.service
%{__mkdir} -p %{buildroot}/%{__systemddir}
%{__install} -pD -m 0644 %{name}.service %{buildroot}/%{__systemddir}/%{name}.service

# python source
%{__mkdir} -p %{buildroot}/%{__bindir}
%{__install} -pD -m 744 %{name}.py %{buildroot}/%{__bindir}/%{name}.py

# config files
%{__mkdir} -p %{buildroot}/%{__etcdir}
%{__install} -pD -m 644 %{name}.ini %{buildroot}/%{__etcdir}/%{name}.ini
%{__install} -pD -m 644 %{name}-uwsgi.ini %{buildroot}/%{__etcdir}/%{name}-uwsgi.ini

%post
%systemd_post %{name}.service
systemctl daemon-reload

%preun
%systemd_preun %{name}.service

%postun
%systemd_postun %{name}.service

%check
%{__python3} -m unittest tests

%clean
[ "%{buildroot}" != "/" ] && rm -fr %{buildroot}


%files
%doc README.md

# sources
%dir %{__bindir}
%{__bindir}/%{name}.py
%{__bindir}/%{name}.py[co]

# python deps
%dir %{python3_sitelib}
%{python3_sitelib}/*

# config files
%{__etcdir}/%{name}.ini
%{__etcdir}/%{name}-uwsgi.ini
%{__systemddir}/%{name}.service

%changelog
* Tue Dec 18 2023 %{packager} - 0.0.1-1
- First ip2w release
