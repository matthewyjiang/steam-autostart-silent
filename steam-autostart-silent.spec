# Fedora package; mirrors the files PKGBUILD installs, with RPM triggers on
# the steam package in place of the libalpm hook. Build from a checkout:
#   git archive --prefix=steam-autostart-silent-VERSION/ \
#     -o ~/rpmbuild/SOURCES/steam-autostart-silent-VERSION.tar.gz HEAD
#   rpmbuild -bb steam-autostart-silent.spec
# .github/workflows/publish-fedora-package.yml does exactly this.

Name:           steam-autostart-silent
# Keep Version in sync with pkgver in PKGBUILD; bump both together.
Version:        1.1.0
Release:        1%{?dist}
Summary:        Maintain a Steam XDG autostart entry that launches with -silent
License:        MIT
URL:            https://github.com/matthewyjiang/steam-autostart-silent
Source0:        %{name}-%{version}.tar.gz
BuildArch:      noarch

Requires:       gtk4
Requires:       libadwaita
Requires:       polkit
Requires:       python3
Requires:       python3-gobject
# Hard dependency, as on Arch. On Fedora, steam comes from RPM Fusion nonfree.
Requires:       steam

%description
Maintains a system-wide /etc/xdg/autostart/steam.desktop generated from the
installed Steam desktop file, so Steam starts with -silent. Includes a GTK 4
configuration app and re-syncs whenever the steam package changes.

%prep
%autosetup

%build
# Nothing to build: shell helpers, a Python app, and data files.

%install
install -Dm755 sync-autostart %{buildroot}%{_prefix}/lib/%{name}/sync-autostart
install -Dm755 apply-config %{buildroot}%{_prefix}/lib/%{name}/apply-config
install -Dm755 steam-autostart-silent-config %{buildroot}%{_bindir}/steam-autostart-silent-config
install -Dm644 steam-autostart-silent-config.desktop \
  %{buildroot}%{_datadir}/applications/steam-autostart-silent-config.desktop
install -Dm644 io.github.matthewyjiang.steam-autostart-silent.policy \
  %{buildroot}%{_datadir}/polkit-1/actions/io.github.matthewyjiang.steam-autostart-silent.policy
install -Dm644 steam-autostart-silent-config-app.py \
  %{buildroot}%{_prefix}/lib/%{name}/steam_autostart_silent_config/app.py
install -dm755 %{buildroot}%{_sysconfdir}/%{name}

%post
# Install and upgrade: write the autostart entry from the current config.
%{_prefix}/lib/%{name}/sync-autostart >/dev/null 2>&1 || :

%postun
# Clean up only on a real erase; on upgrade the new package's post re-syncs.
if [ "$1" -eq 0 ]; then
  rm -f %{_sysconfdir}/xdg/autostart/steam.desktop
  rm -f %{_sysconfdir}/%{name}/config.conf
  rmdir %{_sysconfdir}/%{name} >/dev/null 2>&1 || :
fi

# These two triggers replace the libalpm hook (not shipped in the RPM).
%triggerin -- steam
# steam installed or upgraded (also fires when this package is installed
# while steam is present): regenerate from the new steam.desktop.
%{_prefix}/lib/%{name}/sync-autostart || :

%triggerpostun -- steam
# steam removed: sync-autostart drops the entry once steam.desktop is gone.
%{_prefix}/lib/%{name}/sync-autostart || :

%files
%{_bindir}/steam-autostart-silent-config
%{_prefix}/lib/%{name}/
%{_datadir}/applications/steam-autostart-silent-config.desktop
%{_datadir}/polkit-1/actions/io.github.matthewyjiang.steam-autostart-silent.policy
# Holds config.conf, which apply-config writes at runtime.
%dir %{_sysconfdir}/%{name}
