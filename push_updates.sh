#UDATE=$(date --iso-8601)
UDATE="YYYY-MM-DD"


git add data/computed/TD-covid19-ita-andamento-nazionale_Rt.csv
git add data/computed/TD-covid19-ita-andamento-nazionale_Rt.xlsx
git add images/TD_Rt_computation_MCMC_300dpi.png
git add images/TD_Rt_computation_MCMC_300dpi.jpg

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
notebooks/italy/Rt_regions.ipynb

git add "data/computed/italy/${UDATE}_italy_futbound-08-12_draws-5_MCMC_Rt_pastdays_000_000.pickle"
git add "data/computed/italy/${UDATE}_futbound_08_12_Piemonte_MCMC_Rt_pastdays_000_000.pickle"
git add "data/computed/italy/${UDATE}_TD_calc_Regions_MCMC_Rt.pickle"

git commit -m "update $UDATE"



git push
