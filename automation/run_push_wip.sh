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


if [ ! -f $regions_file_source ]; then
    echo "Regions file missing"
    echo "Location should be $regions_file_source"
    echo "Retry later"
    exit 1
fi

if [ ! -f $national_file_source ]; then
    echo "National file missing"
    echo "Location should be $national_file_source"
    echo "Retry later"    
    exit 1
fi

sudo chown $UID:$UID $regions_file_source

mv $regions_file_source $regions_file_target
mv $national_file_source $national_file_target

BRANCH_DATE=$(echo $PLACEHOLDER_DATE | sed -s "s#-##g")
echo $BRANCH_DATE
git checkout -b WIP_$BRANCH_DATE || exit 1

git add $regions_file_target || exit 1
git add $national_file_target || exit 1

git commit -m "calculations $PLACEHOLDER_DATE" || exit 1

git push --set-upstream origin WIP_$BRANCH_DATE
