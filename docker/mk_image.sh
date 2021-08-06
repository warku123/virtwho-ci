#!/usr/bin/env bash
#
# Create a base RHEL/Centos Docker image.
#
# This script is useful on systems with yum installed (e.g., building
# a RHEL/CentOS image).

set -e

usage() {
    cat <<EOOPTS
$(basename $0) [OPTIONS] <name>
OPTIONS:
  -p "<packages>"  The list of packages to install in the container.
                   The default is blank.
  -g "<groups>"    The groups of packages to install in the container.
                   The default is "Core".
  -y <yumconf>     The path to the yum config to install packages from. The
                   default is /etc/yum.conf for Centos/RHEL and /etc/dnf/dnf.conf for Fedora
EOOPTS
    exit 1
}

# option defaults
yum_config=/etc/yum.conf
if [ -f /etc/dnf/dnf.conf ] && command -v dnf &> /dev/null; then
	yum_config=/etc/dnf/dnf.conf
	alias yum=dnf
fi
install_groups="Core"
while getopts ":y:p:g:h" opt; do
    case $opt in
        y)
            yum_config=$OPTARG
            ;;
        h)
            usage
            ;;
        p)
            install_packages="$OPTARG"
            ;;
        g)
            install_groups="$OPTARG"
            ;;
        \?)
            echo "Invalid option: -$OPTARG"
            usage
            ;;
    esac
done
shift $((OPTIND - 1))
name=$1

if [[ -z $name ]]; then
    usage
fi

target=$(mktemp -d --tmpdir $(basename $0).XXXXXX)

set -x

mkdir -m 755 "$target"/dev
mknod -m 600 "$target"/dev/console c 5 1
mknod -m 600 "$target"/dev/initctl p
mknod -m 666 "$target"/dev/full c 1 7
mknod -m 666 "$target"/dev/null c 1 3
mknod -m 666 "$target"/dev/ptmx c 5 2
mknod -m 666 "$target"/dev/random c 1 8
mknod -m 666 "$target"/dev/tty c 5 0
mknod -m 666 "$target"/dev/tty0 c 4 0
mknod -m 666 "$target"/dev/urandom c 1 9
mknod -m 666 "$target"/dev/zero c 1 5

# amazon linux yum will fail without vars set, remove it for rhel8
#if [ -d /etc/yum/vars ]; then
#	mkdir -p -m 755 "$target"/etc/yum
#	cp -a /etc/yum/vars "$target"/etc/yum/
#fi

if [[ -n "$install_groups" ]];
then
    for i in {1..5}
    do
        yum -c "$yum_config" --installroot="$target" --releasever=/ --setopt=tsflags=nodocs \
            --setopt=group_package_types=mandatory -y groupinstall "$install_groups"
        if [ $? -eq 0 ]
        then
            echo  "Finished to install groups"
            break
        else
            sleep 30s
            echo  "Waiting 60s try again to install groups"
        fi
    done
fi

if [[ -n "$install_packages" ]];
then
    for i in {1..5}
    do
        yum -c "$yum_config" --installroot="$target" --releasever=/ --setopt=tsflags=nodocs \
            --setopt=group_package_types=mandatory -y install "$install_packages"
        if [ $? -eq 0 ]
        then
            echo  "Finished to install packages"
            break
        else
            sleep 30s
            echo  "Waiting 60s try again to install packages"
        fi
    done
fi

# install dependence packages for virt-who
for i in {1..5}
do
    yum -c "$yum_config" --installroot="$target" --releasever=/ --setopt=tsflags=nodocs --setopt=group_package_types=mandatory \
        -y install @base openssh-server openssh-clients openssl-devel net-tools wget hostname sudo subscription-manager gcc expect
    # different packages for rhel8/9 and rhel7
    if [[ $name =~ "rhel7" ]] || [[ $name =~ "rhel-7" ]] || [[ $name =~ "rhel.7" ]];
    then
        yum -c "$yum_config" --installroot="$target" --releasever=/ --setopt=tsflags=nodocs --setopt=group_package_types=mandatory \
            -y install @x11 subscription-manager-gui pexpect libvirt-python python-devel
    elif [[ $name =~ "rhel8" ]] || [[ $name =~ "rhel-8" ]] || [[ $name =~ "rhel.8" ]];
    then
        yum -c "$yum_config" --installroot="$target" --releasever=/ --setopt=tsflags=nodocs --setopt=group_package_types=mandatory \
            -y install cockpit subscription-manager-cockpit python3-pexpect python3-libvirt glibc-all-langpacks
    else
        yum -c "$yum_config" --installroot="$target" --releasever=/ --setopt=tsflags=nodocs --setopt=group_package_types=mandatory \
            -y install cockpit subscription-manager-cockpit python3-libvirt glibc-all-langpacks
    fi
    # try again if failed to install
    if [ $? -eq 0 ]
    then
        echo  "Finished to install packages"
        break
    else
        sleep 30s
        echo  "Waiting 60s try again to install packages"
    fi
done

# setup compose yum repo for virt-who host
mkdir -p -m 755 "$target"/etc/yum.repos.d/
cp "$yum_config" "$target"/etc/yum.repos.d/

yum -c "$yum_config" --installroot="$target" -y clean all

cat > "$target"/etc/sysconfig/network <<EOF
NETWORKING=yes
HOSTNAME=localhost.localdomain
EOF

# backup rhsm.conf
mkdir -p --mode=0755 "$target"/backup/
cp "$target"/etc/rhsm/rhsm.conf "$target"/backup/

# effectively: febootstrap-minimize --keep-zoneinfo --keep-rpmdb --keep-services "$target".
#  locales
#rm -rf "$target"/usr/{{lib,share}/locale,{lib,lib64}/gconv,bin/localedef,sbin/build-locale-archive}
#  docs and man pages
rm -rf "$target"/usr/share/{man,doc,info,gnome/help}
#  cracklib
rm -rf "$target"/usr/share/cracklib
#  i18n
#rm -rf "$target"/usr/share/i18n
#  yum cache
rm -rf "$target"/var/cache/yum
mkdir -p --mode=0755 "$target"/var/cache/yum
#  sln
rm -rf "$target"/sbin/sln
#  ldconfig
rm -rf "$target"/etc/ld.so.cache "$target"/var/cache/ldconfig
mkdir -p --mode=0755 "$target"/var/cache/ldconfig

version=
for file in "$target"/etc/{redhat,system}-release
do
    if [ -r "$file" ]; then
        version="$(sed 's/^[^0-9\]*\([0-9.]\+\).*$/\1/' "$file")"
        break
    fi
done

if [ -z "$version" ]; then
    echo >&2 "warning: cannot autodetect OS version, using '$name' as tag"
    version=$name
fi

tar --numeric-owner -c -C "$target" . | docker import - $name

docker images | grep "$name"
#docker run -i -t --rm $name /bin/bash -c 'echo success'

rm -rf "$target"

