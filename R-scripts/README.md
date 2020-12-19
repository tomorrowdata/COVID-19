# Wrapper to run ISS R script

All the scripts contained in this directory can be run within the R docker-compose `repiestim` service started from the root of the repo.

`calcolo_Rt_Italia` directoy is from the original zip file from ISS
- the zip file is downloadable here: https://www.epicentro.iss.it/coronavirus/open-data/calcolo_rt_italia.zip
- the ISS page states that the zip file is updated weekly, but in fact it is not, as of Dec 19th the last update is of Dec 2nd
- so, no need to import the zip file on the fly, it is simply cloned once within this repo

`run_ISS_script.R` is the wrapper script:
- it runs the ISS script 
- it produces a `ISS_Epiestim_Rt.csv` file in the `data/computed` directory
- the `csv` file is then loaded with pandas for further elaborations
- to run the wrapper script execute the following command, once the `repiestim` service is running:
  - `docker-compose exec -u 1000 repiestim Rscript run_ISS_script.R`
