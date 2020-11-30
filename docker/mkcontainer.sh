#!/usr/bin/env bash
set -e
usage() {
cat <<EOOPTS
$(basename $0) [OPTIONS]
OPTIONS:
  -i "<image_name>"         The image name will be used to launch container
  -c "<container-name>"     The container name you want to create
  -o "<container-port>"     The container port you want to create
  -u "<container-user>"     The container user you want to create
  -p "<container-password>" The container password you want to create
EOOPTS
exit 1
}

if [ $# -eq 0 ]
then
    usage
fi

while getopts ":i:c:o:u:p:h" opt; do
    case $opt in
        i)
            image_name=$OPTARG
            ;;
        c)
            container_name="$OPTARG"
            ;;
        o)
            container_port="$OPTARG"
            ;;
        u)
            container_user="$OPTARG"
            ;;
        p)
            container_password="$OPTARG"
            ;;
        h)
            usage
            ;;
        \?)
            echo "Invalid option: -$OPTARG"
            usage
            ;;
        :)
            echo "No value for opiton -$OPTARG"
            usage
            ;;
    esac
done

if [ $# -eq 0 ]; then usage; fi
if [ "$image_name" == "" ]; then usage; fi
if [ "$container_name" == "" ]; then usage; fi
if [ "$container_port" == "" ]; then usage; fi
if [ "$container_user" == "" ]; then usage; fi
if [ "$container_password" == "" ]; then usage; fi
container_name=$(echo "$container_name" | tr '[:upper:]' '[:lower:]')

if [[ $container_name =~ "rhel6" ]] || [[ $container_name =~ "rhel-6" ]] || [[ $container_name =~ "rhel.6" ]]
then
    docker run --privileged -itd --hostname $container_name --name $container_name -p $container_port:22 $image_name bash
else
    docker run --privileged -itd -v /sys/fs/cgroup:/sys/fs/cgroup --hostname $container_name --name $container_name -p $container_port:22 $image_name /usr/sbin/init
fi

echo -e "${container_user}:${container_password}" | docker exec -i $container_name chpasswd
docker exec -i $container_name ifconfig
docker exec -i $container_name hostname $container_name
if [[ $container_name =~ "rhel9" ]] || [[ $container_name =~ "rhel-9" ]] || [[ $container_name =~ "rhel.9" ]]
then
    docker exec -i $container_name sed -i 's/#*PermitRootLogin prohibit-password/PermitRootLogin yes/g' /etc/ssh/sshd_config
    docker exec -i $container_name sed -i 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' /etc/pam.d/sshd
else
    docker exec -i $container_name sed -i 's/UsePAM yes/UsePAM no/g' /etc/ssh/sshd_config
fi
docker exec -i $container_name sed -i 's/#UseDNS yes/UseDNS no/g' /etc/ssh/sshd_config
docker exec -i $container_name sed -i 's/GSSAPIAuthentication yes/GSSAPIAuthentication no/g' /etc/ssh/sshd_config
docker exec -i $container_name sed -i 's/#X11UseLocalhost yes/X11UseLocalhost no/g' /etc/ssh/sshd_config
echo -e "" | docker exec -i $container_name ssh-keygen -t dsa -f /etc/ssh/ssh_host_dsa_key > /dev/null 2>&1
echo -e "" | docker exec -i $container_name ssh-keygen -t rsa -f /etc/ssh/ssh_host_rsa_key > /dev/null 2>&1
docker exec -i $container_name /usr/sbin/sshd
