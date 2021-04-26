#UDATE=$(date --iso-8601)
UDATE="2021-04-23"


git add data/computed/TD-covid19-ita-andamento-nazionale_Rt.csv
git add data/computed/TD-covid19-ita-andamento-nazionale_Rt.xlsx
git add images/TD_Rt_computation_MCMC_300dpi.png
git add images/TD_Rt_computation_MCMC_300dpi.jpg

git add images/italy/TD_Rt_Regions_All_computation_MCMC_150dpi.jpg
git add images/italy/TD_Rt_Regions_All_computation_MCMC_150dpi.png



git add	images/italy/TD_Rt_Campania_computation_MCMC_150dpi.jpg
git add	images/italy/TD_Rt_Campania_computation_MCMC_150dpi.png
git add	images/italy/TD_Rt_Lombardia_computation_MCMC_150dpi.jpg
git add	images/italy/TD_Rt_Lombardia_computation_MCMC_150dpi.png
git add	images/italy/TD_Rt_Piemonte_computation_MCMC_150dpi.jpg
git add	images/italy/TD_Rt_Piemonte_computation_MCMC_150dpi.png
git add	images/italy/TD_Rt_Toscana_computation_MCMC_150dpi.jpg
git add	images/italy/TD_Rt_Toscana_computation_MCMC_150dpi.png

git add notebooks/Rt_on_italian_national_data.ipynb
git add notebooks/italy/Rt_Piemonte.ipynb
git add notebooks/italy/Rt_regions.ipynb

git add notebooks/italy/Rt-all-regions.ipynb
git add notebooks/italy/Rt_Sicilia.ipynb
git add notebooks/italy/Rt_Valle_d_Aosta.ipynb



git add "data/computed/italy/${UDATE}_futbound_08_12_National_MCMC_Rt_pastdays_000_000.pickle"
git add "data/computed/italy/${UDATE}_futbound_08_12_Piemonte_MCMC_Rt_pastdays_000_000.pickle"
git add "data/computed/italy/${UDATE}_TD_calc_Regions_MCMC_Rt.pickle"
git add "data/computed/italy/${UDATE}_TD_calc_Regions_all_MCMC_Rt.pickle"
git add "data/computed/italy/${UDATE}_TD_calc_Regions_all_MCMC_Rt.csv"

git commit -m "update $UDATE"

git push