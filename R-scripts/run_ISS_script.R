setwd("/R-scripts/calcolo_Rt_Italia/")

source("calcoloRt_EpiEstim.R")

stima$R$date <- date

write.csv(stima$R, '/data/computed/ISS_Epiestim_Rt.csv')
