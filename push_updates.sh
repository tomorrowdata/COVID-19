UDATE=$(date --iso-8601)
#UDATE="YYYY-MM-DD"


git add data/computed/TD-covid19-ita-andamento-nazionale_Rt.csv
git add data/computed/TD-covid19-ita-andamento-nazionale_Rt.xlsx
git add images/TD_Rt_computation_MCMC_300dpi.png
git add images/TD_Rt_computation_MCMC_300dpi.jpg
git add notebooks/Rt_on_italian_national_data.ipynb
git add notebooks/italy/Rt_Piemonte.ipynb

git add "data/computed/italy/${UDATE}_italy_futbound-08-12_draws-5_MCMC_Rt_pastdays_000_000.pickle"
git add "data/computed/italy/${UDATE}_futbound_08_12_Piemonte_MCMC_Rt_pastdays_000_000.pickle"


git commit -m "update $UDATE"



git push
