import pandas as pd
from numbers import Number

from covid19_pytoolbox.modeling.Rt import naive

def growth(p0,rate, zerosteps, steps):
    assert(zerosteps < steps)
    if isinstance(rate, Number):
        ratefunc = lambda s: rate
    elif callable(rate):
        ratefunc = rate
    else:
        raise Exception("rate must be either a number or a function")
    v = p0
    for s in range(steps):
        if s <= zerosteps:
            yield 0.
        else:
            r = ratefunc(s)
            v = v * (1. + r)
            yield v


def apply_perturbations(cumulatives, p0, rate, zerosteps, steps, regularizer, Rt_alpha, Rt_beta):
    perturbation = pd.Series(growth(p0, rate, zerosteps, steps))

    cum_low, cum_high = cumulatives - perturbation, cumulatives + perturbation

    new_cases_low, new_cases_high = (
        regularizer.stat_smooth_differentiate(cum_low),
        regularizer.stat_smooth_differentiate(cum_high)
    )

    Rt_low, Rt_high = (
        naive.compute_Rt(new_cases_low, alpha=Rt_alpha, beta=Rt_beta),
        naive.compute_Rt(new_cases_high, alpha=Rt_alpha, beta=Rt_beta)
    )

    return new_cases_low, new_cases_high, Rt_low, Rt_high
