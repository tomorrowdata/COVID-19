# COVID-19

- real-time estimation of the `Rt` index
- analysis of COVID-19 data

# Results

Results of the `Rt` computation are updated daily at 6PM, after [Protezione Civile](https://github.com/pcm-dpc/COVID-19) makes them available

The following data are updated:

- the full jupyther notebook `notebooks/Rt_on_italian_national_data.ipynb`
- the **csv** file with `nuovi_positivi` and $Rt$ values `data/comupted/TD-covid19-ita-andamento-nazionale_rt.csv`
- the **excel** file with `nuovi_positivi` and $Rt$ values `data/comupted/TD-covid19-ita-andamento-nazionale_rt.xlsx`
- the chart with the $Rt$ trend in `images/TD_Rt_computation_MCMC_300dpi.png`

**Please note:** file names are kept fixed (no dates in the names) so that they can be easily imported daily by third party applications. Refer to the commit date to check if the file has been updated.

## Columns in the tables:

- `data`: the date, ISO format
- `nuovi_positivi`: raw value provided by Protezione Civile
- `nuovi_positivi_Tikhonov`: `nuovi_positivi` cleaned from noise, by Tikhonof regularization
- `Rt`: the Rt value computed with Markiv chain Monte Carlo, on the `nuovi_positivi_Tikhonov`
- `Rt_interv_cred_min`: min absolute value of cerdibility interval for the Rt value
- `Rt_interv_cred_max`: max absolute value of cerdibility interval for the Rt value

# Third party Datasets

The sources and owners of the Datasets  are cited in the notebooks.
The static source files are in `data/sources`.

## ISS weekly updates of the Rt value
Rt values weekly published by ISS are updated manually in the following file: `data/sources/Rt_from_ISS.csv`. The important dates in this file are in the column `computation_time_range_descr` which reports the period apopted by ISS for the computation of the Rt index.

That file is then processed to compute the reference data, which is set in the middle of the computation period.
The processed file is available at: `data/computed/Rt_from_ISS_processed.xlsx` (or `.csv`)
The processed file can be used to produce charts of the ISS Rt value.

# Run with docker

- install docker
- install docker-compose
- run `docker-compose up -d`
- open browser and navigate to `http://127.0.0.1:8888`
- look at the the yaml




