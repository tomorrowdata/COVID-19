# Python RSVD seasonal adjustment

This python module implements time series seasonal adjustment via Regularized Singular Value Decomposition.

The code is a porting from the orignal authors' R version.

## References and credits 

**Time Series Seasonal Adjustment Using Regularized Singular Value Decomposition**

By Wei Lin, Jianhua Huang (Texas A&M University), Tucker Mcelroy (U.S. Census Bureau)

The paper can be found here: https://www.researchgate.net/publication/327256122_Time_Series_Seasonal_Adjustment_Using_Regularized_Singular_Value_Decomposition

The supplementary material, with R code and sample datasets, can be found here: https://ndownloader.figstatic.com/articles/7012643/versions/2

## Usage

```

from covid19_pytoolbox.smoothing.seasonalRSVD import RSVD

signal = [1-D numpy array representing the time series]

rsvd = RSVD.SeasonalRegularizer(signal=signal, season_period=12, max_r=12)

res = rsvd.fit()

seasonal_component = res.season_svd

```

