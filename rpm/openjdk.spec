%global jdkver 17
# Produced with: echo "git:$(git show --no-patch --format=%H | cut -c1-12)"
%global jdkrev git:0a6252780a86
%global bootjdkver 16
# Replace with "fastdebug" if jvm debugging is required
%global debuglevel release

# Filter out flags from the optflags macro that cause problems with the OpenJDK build
# We filter out -O flags so that the optimization of HotSpot is not lowered from O3 to O2
# We filter out -Wall which will otherwise cause HotSpot to produce hundreds of thousands of warnings (100+mb logs)
# We replace it with -Wno-cpp to avoid FORTIFY_SOURCE warnings
# We filter out -fexceptions as the HotSpot build explicitly does -fno-exceptions and it's otherwise the default for C++
%global jdkcflags %(echo %optflags | sed -e 's|-Wall|-Wno-cpp|' | sed -r -e 's|-O[0-9]*||')
%global jdkcxxflags %(echo %jdkcflags | sed -e 's|-fexceptions||')

# It is not possible to use __requires_exclude_from here, as automatic requires
# for these libraries will not be generated at all (e.g. there will be no
# dependency on libz.so.1).
%global _jdklibs libattach[.]so.*|libawt[.]so.*|libawt_headless[.]so.*|libdt_socket[.]so.*|libextnet[.]so.*|libfontmanager[.]so.*|libinstrument[.]so.*|libj2gss[.]so.*|libj2pcsc[.]so.*|libj2pkcs11[.]so.*|libjaas[.]so.*|libjava[.]so.*|libjavajpeg[.]so.*|libjdwp[.]so.*|libjimage[.]so.*|libjli[.]so.*|libjsig[.]so.*|libjvm[.]so.*|liblcms[.]so.*|libmanagement_agent[.]so.*|libmanagement_ext[.]so.*|libmanagement[.]so.*|libmlib_image[.]so.*|libnet[.]so.*|libnio[.]so.*|libprefs[.]so.*|librmi[.]so.*|libsaproc[.]so.*|libsctp[.]so.*|libsyslookup[.]so.*|libsystemconf[.]so.*|libverify[.]so.*|libzip[.]so.*
%global __provides_exclude ^(%{_jdklibs})$
%global __requires_exclude ^(%{_jdklibs})$

Name: java-%{jdkver}-openjdk
Summary: OpenJDK %{jdkver} Runtime Environment
Version: %{jdkver}.0.5
Release: 1

# HotSpot code is licensed under GPLv2
# JDK library code is licensed under GPLv2 with the Classpath exception
# The Apache license is used in code taken from Apache projects (primarily xalan & xerces)
# DOM levels 2 & 3 and the XML digital signature schemas are licensed under the W3C Software License
# The JSR166 concurrency code is in the public domain
# The BSD and MIT licenses are used for a number of third-party libraries (see ADDITIONAL_LICENSE_INFO)
# The OpenJDK source tree includes:
# - JPEG library (IJG), zlib & libpng (zlib), giflib (MIT), harfbuzz (ISC),
# - freetype (FTL), jline (BSD) and LCMS (MIT)
# - jquery (MIT), jdk.crypto.cryptoki PKCS 11 wrapper (RSA)
# - public_suffix_list.dat from publicsuffix.org (MPLv2.0)
# The test code includes copies of NSS under the Mozilla Public License v2.0
# The PCSClite headers are under a BSD with advertising license
# The elliptic curve cryptography (ECC) source code is licensed under the LGPLv2.1 or any later version
License: ASL 1.1 and ASL 2.0 and BSD and BSD with advertising and GPL+ and GPLv2 and GPLv2 with exceptions and IJG and LGPLv2+ and MIT and MPLv2.0 and Public Domain and W3C and zlib and ISC and FTL and RSA

URL: http://openjdk.java.net/
Source0: %{name}-%{version}.tar.zst
Patch1: 0001-Build-without-ALSA-and-CUPS.patch
Patch2: 0002-Align-stack-to-16-bytes-boundary-on-x86.patch
BuildRequires: autoconf
BuildRequires: bash
BuildRequires: zip
BuildRequires: java-%{bootjdkver}-openjdk-devel
BuildRequires: pkgconfig(zlib)
BuildRequires: pkgconfig(x11)
BuildRequires: pkgconfig(xrender)

%description
%{summary}.

%package headless
Summary: OpenJDK %{jdkver} Headless Runtime Environment
Provides: java-headless = %{version}-%{release}
Provides: java-%{jdkver}-headless = %{version}-%{release}

%description headless
The OpenJDK %{jdkver} runtime environment without audio and video support.

%package devel
Summary: OpenJDK %{jdkver} Development Environment
Provides: java-devel = %{version}-%{release}
Provides: java-%{jdkver}-devel = %{version}-%{release}
Requires: %{name}-headless = %{version}-%{release}

%description devel
The OpenJDK %{jdkver} development tools.

%prep
%autosetup -p1 -n %{name}-%{version}/upstream

%build
echo %{jdkrev} > .src-rev

bash configure \
    --openjdk-target=%{_target_platform} \
    --program-prefix=%{?_program_prefix} \
    --prefix=%{_prefix} \
    --exec-prefix=%{_exec_prefix} \
    --bindir=%{_bindir} \
    --sbindir=%{_sbindir} \
    --sysconfdir=%{_sysconfdir} \
    --datadir=%{_datadir} \
    --includedir=%{_includedir} \
    --libdir=%{_libdir} \
    --libexecdir=%{_libexecdir} \
    --localstatedir=%{_localstatedir} \
    --sharedstatedir=%{_sharedstatedir} \
    --mandir=%{_mandir} \
    --infodir=%{_infodir} \
    --disable-javac-server \
    --disable-warnings-as-errors \
    --disable-full-docs \
    --enable-headless-only \
    --with-debug-level=%{debuglevel} \
    --with-extra-ldflags="-Wl,--enable-new-dtags" \
    --with-extra-cflags="%{jdkcflags}" \
    --with-extra-cxxflags="%{jdkcxxflags}" \
    --with-native-debug-symbols=internal \
    --with-boot-jdk=%{_jvmdir}/java-%{bootjdkver}-openjdk

[ -z "$RPM_BUILD_NCPUS" ] && RPM_BUILD_NCPUS="`/usr/bin/getconf _NPROCESSORS_ONLN`"
make CONF=%{debuglevel} JOBS=$RPM_BUILD_NCPUS images

%install
STRIP_KEEP_SYMTAB=libjvm*

IMAGEDIR="build/linux-x86-server-%{debuglevel}/images/jdk"
JDKNAME="java-%{jdkver}-openjdk"
DESTDIR="%{buildroot}%{_jvmdir}/${JDKNAME}"

# Install only required directories
for dir in bin include legal lib conf; do
    install -d "${DESTDIR}/${dir}"
    rm -rf "${DESTDIR}/${dir}"
    cp -r "${IMAGEDIR}/${dir}" "${DESTDIR}/${dir}"
done

# Build screws up permissions on binaries
# https://bugs.openjdk.java.net/browse/JDK-8173610
find "${DESTDIR}" -iname '*.so' -exec chmod +x {} \;
find "${DESTDIR}/bin" -exec chmod +x {} \;

install -D -m 0644 "${IMAGEDIR}/release" "${DESTDIR}/release"

%files headless
%{_jvmdir}/%{name}/bin/java
%{_jvmdir}/%{name}/bin/keytool
%{_jvmdir}/%{name}/bin/rmiregistry
%{_jvmdir}/%{name}/conf
%{_jvmdir}/%{name}/legal
%{_jvmdir}/%{name}/lib
%{_jvmdir}/%{name}/release

%files devel
%{_jvmdir}/%{name}/bin/jar
%{_jvmdir}/%{name}/bin/jarsigner
%{_jvmdir}/%{name}/bin/javac
%{_jvmdir}/%{name}/bin/javadoc
%{_jvmdir}/%{name}/bin/javap
%{_jvmdir}/%{name}/bin/jcmd
%{_jvmdir}/%{name}/bin/jconsole
%{_jvmdir}/%{name}/bin/jdb
%{_jvmdir}/%{name}/bin/jdeprscan
%{_jvmdir}/%{name}/bin/jdeps
%{_jvmdir}/%{name}/bin/jfr
%{_jvmdir}/%{name}/bin/jhsdb
%{_jvmdir}/%{name}/bin/jimage
%{_jvmdir}/%{name}/bin/jinfo
%{_jvmdir}/%{name}/bin/jlink
%{_jvmdir}/%{name}/bin/jmap
%{_jvmdir}/%{name}/bin/jmod
%{_jvmdir}/%{name}/bin/jpackage
%{_jvmdir}/%{name}/bin/jps
%{_jvmdir}/%{name}/bin/jrunscript
%{_jvmdir}/%{name}/bin/jshell
%{_jvmdir}/%{name}/bin/jstack
%{_jvmdir}/%{name}/bin/jstat
%{_jvmdir}/%{name}/bin/jstatd
%{_jvmdir}/%{name}/bin/serialver
%{_jvmdir}/%{name}/include
