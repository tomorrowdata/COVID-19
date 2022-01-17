#! /bin/bash

source .env

if [[ -z "${PLACEHOLDER_DATE}" ]]; then
    echo "Please set the PLACEHOLDER_DATE env variable!"
    exit 1
fi

PASTDAYS="000"

cd .. || exit 1

source_dir="data/computed/WIP"
target_dir="data/computed/italy"

regions_file="${PLACEHOLDER_DATE}_TD_calc_Regions_all_MCMC_Rt.pickle"
national_file="${PLACEHOLDER_DATE}_futbound_08_12_National_MCMC_Rt_pastdays_${PASTDAYS}_${PASTDAYS}.pickle"

regions_file_source="${source_dir}/${regions_file}"
national_file_source="${source_dir}/${national_file}"

regions_file_target="${target_dir}/${regions_file}"
national_file_target="${target_dir}/${national_file}"


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




BRANCH_DATE=$(echo $PLACEHOLDER_DATE | sed -s "s#-##g")
echo $BRANCH_DATE
git checkout -b TTT_WIP_$BRANCH_DATE || exit 1

git add $regions_file_target || exit 1
git add $national_file_target || exit 1

git commit -m "calculations $PLACEHOLDER_DATE" || exit 1

git push --set-upstream origin WIP_$BRANCH_DATE
