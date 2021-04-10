#! /bin/bash

source .env

BRANCH_DATE=$(echo $PLACEHOLDER_DATE | sed -s "s#-##g")
echo $BRANCH_DATE
git checkout -b WIP_$BRANCH_DATE || exit 1

cd .. || exit 1

git add data/computed/TD-covid19-ita-andamento-nazionale_Rt.csv || exit 1
git add data/computed/TD-covid19-ita-andamento-nazionale_Rt.xlsx || exit 1
git add images/TD_Rt_computation_MCMC_300dpi.png || exit 1
git add images/TD_Rt_computation_MCMC_300dpi.jpg || exit 1

git add	images/italy/TD_Rt_Campania_computation_MCMC_150dpi.jpg || exit 1
git add	images/italy/TD_Rt_Campania_computation_MCMC_150dpi.png || exit 1
git add	images/italy/TD_Rt_Lombardia_computation_MCMC_150dpi.jpg || exit 1
git add	images/italy/TD_Rt_Lombardia_computation_MCMC_150dpi.png || exit 1
git add	images/italy/TD_Rt_Piemonte_computation_MCMC_150dpi.jpg || exit 1
git add	images/italy/TD_Rt_Piemonte_computation_MCMC_150dpi.png || exit 1
git add	images/italy/TD_Rt_Toscana_computation_MCMC_150dpi.jpg || exit 1
git add	images/italy/TD_Rt_Toscana_computation_MCMC_150dpi.png || exit 1

git add notebooks/Rt_on_italian_national_data.ipynb || exit 1
git add notebooks/italy/Rt_Piemonte.ipynb || exit 1
git add notebooks/italy/Rt_regions.ipynb || exit 1

git add "data/computed/italy/${PLACEHOLDER_DATE}_futbound_08_12_National_MCMC_Rt_pastdays_000_000.pickle" || exit 1
git add "data/computed/italy/${PLACEHOLDER_DATE}_futbound_08_12_Piemonte_MCMC_Rt_pastdays_000_000.pickle" || exit 1
git add "data/computed/italy/${PLACEHOLDER_DATE}_TD_calc_Regions_MCMC_Rt.pickle" || exit 1

git commit -m "update $PLACEHOLDER_DATE" || exit 1

git push --set-upstream origin WIP_$BRANCH_DATE