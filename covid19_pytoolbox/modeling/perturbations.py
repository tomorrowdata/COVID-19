import pandas as pd
from numbers import Number


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


def compute_perturbed_cumulative(cumulatives, p0, rate, zerosteps, steps):
    perturbation = pd.Series(growth(p0, rate, zerosteps, steps))

    return cumulatives + perturbation