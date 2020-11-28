# COVID-19

- real-time estimation of the `Rt` index
- analysis of COVID-19 data

# Results

Results of the `Rt` computation are updated daily at 6PM, after [Protezione Civile](https://github.com/pcm-dpc/COVID-19) makes them available

The following data are updated:

- the full jupyther notebook `notebooks/Rt_on_italian_national_data.ipynb`
- the **csv** file with `nuovi_positivi` and $Rt$ values `data/comupted/TD-covid19-ita-andamento-nazionale_rt.csv`
- the **excel** file with `nuovi_positivi` and $Rt$ values `data/comupted/TD-covid19-ita-andamento-nazionale_rt.xlsx`
- the chart with the $Rt$ trend in `images/`

# Run with docker

- install docker
- install docker-compose
- run `docker-compose up -d`
- open browser and navigate to `http://127.0.0.1:8888`
- look at the the yaml

# Datasets
The sources and owners of the Datasets  are cited in the notebooks.
The static source files are in `data/sources`.




