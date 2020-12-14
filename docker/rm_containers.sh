#!/usr/bin/env bash
set -e
usage() {
cat <<EOOPTS
$(basename $0) [OPTIONS]
OPTIONS:
  -d "<created-days>"       How many days the container created
EOOPTS
exit 1
}

if [ $# -eq 0 ]
then
    usage
fi


while getopts ":d:h" opt; do
    case $opt in
        d)
            created_days=$OPTARG
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
if [ "$created_days" == "" ]; then usage; fi

# will  
docker ps -a --format "{{.ID}} {{.CreatedAt}}" | while read id cdate ctime _; do if [[ $(date +%s -d "$cdate $ctime") -lt $(date +%s -d "$created_days days ago") ]]; then docker kill $id; docker rm $id; fi; done
