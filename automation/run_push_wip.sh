#! /bin/bash

# to run a continuous process that automatically check for the processing to be finished:
# GOON=1 ; while [ ! $GOON -eq 0 ] ; do echo $(date) ; ./run_push_wip.sh ; GOON=$? ; sleep 5 ; done

source .env

if [[ -z "${PLACEHOLDER_DATE}" ]]; then
    echo "Please set the PLACEHOLDER_DATE env variable!"
    exit 1
fi

PASTDAYS="000"

cd .. || exit 1

source_dir="data/computed/WIP"
target_dir="data/computed/italy"

regions_file="${PLACEHOLDER_DATE}_TD_calc_Regions_all_MCMC_Rt.parquet"
national_file="${PLACEHOLDER_DATE}_futbound_08_12_National_MCMC_Rt_pastdays_${PASTDAYS}_${PASTDAYS}.pickle"

regions_file_source="${source_dir}/${regions_file}"
national_file_source="${source_dir}/${national_file}"

regions_file_target="${target_dir}/${regions_file}"
national_file_target="${target_dir}/${national_file}"

# check that the automation process is completed
rtautomation=$(docker ps --filter "name=RTAutomation" -q)

if [ ! -z $rtautomation ]; then
    echo "$(date): processing is not completed yet. running calculations:"
    docker ps --filter "ancestor=covid-run-apps" --format "{{.Names}}"
    echo "retry later"
    exit 1
else
    echo "$(date): processing is completed. goon with moving and pushing results"
fi

# check if regions file exists and process it
if [ ! -f $regions_file_source  ]; then
    if [ ! -f $regions_file_target ]; then
        echo "None of the two Regions file are present. Locations should be:"
        echo "$regions_file_source"
        echo "or"
        echo "$regions_file_target"
        echo "Retry later"
        exit 1
    fi
else
    if [ ! -f $regions_file_target ]; then
        GOOD_SUDO=true
        sudo chown $UID:$UID $regions_file_source || GOOD_SUDO=false
        if $GOOD_SUDO ; then
            mv $regions_file_source $regions_file_target
            echo "proccessed ${regions_file_source} to ${regions_file_target}"
        else
            echo "you must type your sudo password when asked for"
            exit 1
        fi
    fi
fi

#check if national file exists and process it
if [ ! -f $national_file_source ]; then
    if [ ! -f $national_file_target ]; then
        echo "None of the two national files are present. Locations should be:"
        echo "$national_file_source"
        echo "or"
        echo "$national_file_target"
        echo "Retry later"    
        exit 1
    fi
else
    if [ ! -f $national_file_target ]; then
        mv $national_file_source $national_file_target
        echo "moved ${national_file_source} to ${national_file_target}"
    fi
fi

$GOOD_SUDO || exit 1

BRANCH_DATE=$(echo $PLACEHOLDER_DATE | sed -s "s#-##g")

WIP_BRANCH="WIP_${BRANCH_DATE}"
echo $WIP_BRANCH

git checkout -b $WIP_BRANCH
if [ ! $? -eq 0 ]; then
    git checkout $WIP_BRANCH
fi

git add $regions_file_target || exit 1
git add $national_file_target || exit 1

git commit -m "calculations $PLACEHOLDER_DATE" || exit 1

git push --set-upstream origin $WIP_BRANCH

echo ""
echo " OK. Everything pushed to ${WIP_BRANCH}"
