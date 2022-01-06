import sys

sys.path.append("../")

import json
import logging
import os
import pickle
import re

import numpy as np
import pymc3 as pm

from covid19_pytoolbox.italy.data import DPC, ISS
from covid19_pytoolbox.modeling.datarevision.seasonal import (
    draw_expanded_series,
    smooth_and_drop,
)
from covid19_pytoolbox.modeling.Rt.bayesian import MCMC_sample
from covid19_pytoolbox import settings
from covid19_pytoolbox.utils import cast_or_none, padnan

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

SANITIZE_PATTERN = re.compile("[\.,'@;$&\"%?\- ]+")

def process_MCMC_sampling(df, column, trace, pastdays, interval=0.95, start=0):
    interval_frac = int(interval * 100)
    sampling_mean = np.mean(trace["r_t"], axis=0)

    df[f"{column}_Rt_MCMC_pastdays_{pastdays:03d}"] = padnan(
        sampling_mean, (start, pastdays)
    )

    # credible interval
    sampling_hdi = pm.stats.hpd(trace["r_t"], hdi_prob=interval)
    df[f"{column}_Rt_MCMC_HDI_{interval_frac}_min_pastdays_{pastdays:03d}"] = padnan(
        sampling_hdi[:, 0], (start, pastdays)
    )
    df[f"{column}_Rt_MCMC_HDI_{interval_frac}_max_pastdays_{pastdays:03d}"] = padnan(
        sampling_hdi[:, 1], (start, pastdays)
    )


def compute_past_series(
    df,
    new_cases_col,
    startday,
    pastdays_start,
    pastdays_end,
    draws,
    alpha,
    beta,
    trend_alpha,
    lower_ratio,
    upper_ratio,
    pickleprefix,
    mctune=1000,
    mcdraws=500,
    mccores=8,
    mctargetaccept=0.95,
    rt_col_prefix="smooth_deseas",
    use_rel_res=True,
    new_cases_local_col=None,
    debug_mode=False,
):

    for pastdays in range(pastdays_start, pastdays_end - 1, -1):
        logger.info(f"\npastdays: {pastdays}")

        if pastdays == 0:
            sl = np.s_[startday:]
        else:
            sl = np.s_[startday:-pastdays]

        new_cases = df[new_cases_col].to_numpy()[sl]

        new_cases_expanded = draw_expanded_series(
            new_cases,
            draws=draws,
            season_period=7,
            trend_alpha=trend_alpha,
            difference_degree=2,
            alpha=alpha,
            beta=beta,
            lower_ratio=lower_ratio,
            upper_ratio=upper_ratio,
            truncate=False,
        )

        logger.info("pre smooth_and_drop")
        logger.info(f"new_cases_expanded.shape: {new_cases_expanded.shape}")

        new_cases_smoothed, rel_eps, padding_left = smooth_and_drop(
            new_cases_expanded, season_period=7, trend_alpha=100.0, difference_degree=2
        )

        logger.info("post smooth_and_drop")
        logger.info(f"new_cases_smoothed.shape: {new_cases_smoothed.shape}")
        logger.info(f"rel_eps.shape: {rel_eps.shape}")
        logger.info(f"padding_left: {padding_left}")

        # local management
        if new_cases_local_col:
            new_cases_local = df[new_cases_local_col].to_numpy()[sl]

            new_cases_local_expanded = draw_expanded_series(
                new_cases_local,
                draws=draws,
                season_period=7,
                trend_alpha=trend_alpha,
                difference_degree=2,
                alpha=alpha,
                beta=beta,
                lower_ratio=lower_ratio,
                upper_ratio=upper_ratio,
                truncate=False,
            )

            new_cases_local_smoothed, rel_eps_local, padding_left_local = smooth_and_drop(
                new_cases_local_expanded, season_period=7, trend_alpha=100.0, difference_degree=2
            )
        else:
            new_cases_local_smoothed = [None] * draws

        simulations = []
        for new_cases_s, rel_eps_s, new_cases_local_s in zip(new_cases_smoothed, rel_eps, new_cases_local_smoothed):
            logger.info(
                f"new_cases_s cut left: {new_cases_s[~np.isnan(new_cases_s)].shape}"
            )
            logger.info(f"rel_eps_s cut left: {rel_eps_s[~np.isnan(rel_eps_s)].shape}")

            try:
                model_, trace_ = MCMC_sample(
                    onset=new_cases_s[~np.isnan(new_cases_s)],
                    alpha=alpha,
                    beta=beta,
                    rel_eps=rel_eps_s[~np.isnan(rel_eps_s)] if use_rel_res else None,
                    onset_local=new_cases_local_s[~np.isnan(new_cases_local_s)],
                    start=0,
                    window=None,
                    chains=mccores,
                    tune=mctune,
                    draws=mcdraws,
                    cores=mccores,
                    target_accept=mctargetaccept,
                    dry=False,
                    progressbar=False,
                )
                simulations.append(trace_)
            except Exception as ex:
                logger.info(ex)
                logger.info(f"skipping pastdays {pastdays:03d}")
                raise ex

        # prepare target dir path and verify if exists
        TARGET_RESULT_DIR = os.path.join(settings.BASE_DATA_PATH, "computed/WIP/")
        if not os.path.exists(TARGET_RESULT_DIR):
            os.makedirs(TARGET_RESULT_DIR, exist_ok=True)

        with open(
            os.path.join(
                TARGET_RESULT_DIR,
                f"{pickleprefix}_MCMC_simulations_pastdays_{pastdays_start:03d}_{pastdays_end:03d}.pickle",
            ),
            "wb",
        ) as handle:
            pickle.dump(simulations, handle)

        
        if debug_mode:
            # use all sampled Rt, including diverging ones
            sampled_Rt = np.vstack([t["r_t"] for t in simulations])
        else:
            sampled_Rt = np.vstack([t["r_t"][~t.diverging, :] for t in simulations])

        combined_trace = {"r_t": sampled_Rt}

        process_MCMC_sampling(
            df,
            f"{new_cases_col}_{rt_col_prefix}",
            combined_trace,
            pastdays,
            interval=0.95,
            start=padding_left + 1 + startday,
        )

        df.to_pickle(
            os.path.join(
                TARGET_RESULT_DIR,
                f"{pickleprefix}_MCMC_Rt_pastdays_{pastdays_start:03d}_{pastdays_end:03d}.pickle",
            )
        )


def main(
    pickleprefix,
    data_col_name,
    pastdays_start,
    pastdays_end,
    futuredraws,
    tot_chain_len,
    lower_ratio,
    upper_ratio,
    mc_targetaccept,
    mc_tune,
    mc_draws,
    mc_cores=4,
    region=None,
    alpha=1.87,
    beta=0.28,
    trend_alpha=100.0,
    use_relative_residuals=True,
    new_cases_local_col=None,
    debug_mode=False,
):
    """
    Start processing seasonalnoisedMCMC

    Args:
        pickleprefix (str): prefix for the generated pickle file.
        data_col_name (str): dataframe column to use for processing.
        pastdays_start (int): starting pastday range interval.
        pastdays_end (int): ending pastday range interval.
        futuredraws (int): how many future scenarios to generate.
        tot_chain_len (int): last n days to use for the processing. If None consider the entire series length.
        lower_ratio (float): lower value for the future_range.
        upper_ratio (float): upper value for the future_range.
        mc_targetaccept (float): MCMC acceptance ratio for the target distribution.
        mc_tune (int): MCMC number of iteration to tune.
        mc_draws (int): MCMC number of samples to draw.
        mc_cores (int, optional): MCMC number of chains to use (same as number of cores). Defaults to 4.
        region (str, optional): if specified, load regional data instead of national one. Defaults to None.
        alpha (float, optional): parameter for the gamma distribution of 'w'. Defaults to 1.87.
        beta (float, optional): parameter for the gamma distribution of 'w'. Defaults to 0.28.
        trend_alpha (float, optional): Tikhonov regularization alpha parameter. Defaults to 100.0.
        use_relative_residuals (bool, optional): Use relative residuals in MCMC simulations. Defaults to True
        imported_vs_locals_col_name (str, optional): column name of imported vs local ratio to correct local cases in MCMC simulations. Applies only if region is None (Italy). Defaults to None.
        debug_mode (bool, optional): if true, do not remove divergent Rt samples (use for debug only). Default to False.
    """

    logger.info(f"pastdays_start: {pastdays_start} - pastdays_end: {pastdays_end}")

    if region:
        raw_data = DPC.load_daily_cases_from_github_region(region)
        region_cleaned = SANITIZE_PATTERN.sub("_", region).replace(" ", "_")
        pickleprefix = f"{pickleprefix}_{region_cleaned}"
    else:
        raw_data = DPC.load_daily_cases_from_github()
        if new_cases_local_col:
            local_imported = ISS.read_weekly_cases_from_local(raw_data.data.max())
            ISS.preprocess_cases(local_imported)
            raw_data = DPC.merge_ISS_weekly_cases(raw_data, local_imported)
            DPC.compute_cases_corrected_by_imported(raw_data)
            
        pickleprefix = f"{pickleprefix}_National"

    startday = 0
    if tot_chain_len:
        startday = len(raw_data[data_col_name]) - tot_chain_len

    compute_past_series(
        raw_data,
        data_col_name,
        pickleprefix=pickleprefix,
        startday=startday,
        pastdays_start=pastdays_start,
        pastdays_end=pastdays_end,
        draws=futuredraws,
        alpha=alpha,
        beta=beta,
        trend_alpha=trend_alpha,
        lower_ratio=lower_ratio,
        upper_ratio=upper_ratio,
        mctune=mc_tune,
        mcdraws=mc_draws,
        mccores=mc_cores,
        mctargetaccept=mc_targetaccept,
        use_rel_res=use_relative_residuals,
        new_cases_local_col=new_cases_local_col,
        debug_mode=debug_mode,
    )


if __name__ == "__main__":
    pickleprefix = cast_or_none(os.environ.get("PICKLEPREFIX", None), str)
    data_col_name = cast_or_none(os.environ.get("DATA_COL_NAME", None), str)
    pastdays_start = cast_or_none(os.environ.get("PASTDAYS_START", 0), int)
    pastdays_end = cast_or_none(os.environ.get("PASTDAYS_END", 0), int)
    futuredraws = cast_or_none(os.environ.get("FUTUREDRAWS", 10), int)
    tot_chain_len = cast_or_none(os.environ.get("TOT_CHAIN_LEN", None), int)
    lower_ratio = cast_or_none(os.environ.get("LOWER_RATIO", 0.8), float)
    upper_ratio = cast_or_none(os.environ.get("UPPER_RATIO", 1.2), float)
    mc_targetaccept = cast_or_none(os.environ.get("MC_TARGETACCEPT", 0.95), float)
    mc_tune = cast_or_none(os.environ.get("MC_TUNE", 500), int)
    mc_draws = cast_or_none(os.environ.get("MC_DRAWS", 500), int)
    mc_cores = cast_or_none(os.environ.get("MC_CORES", 4), int)
    region = cast_or_none(os.environ.get("REGION", None), str)
    use_rel_res = cast_or_none(os.environ.get("USE_RELATIVE_RESIDUALS", True), bool)
    new_cases_local_col_name = cast_or_none(os.environ.get("NEW_CASES_LOCAL_COL_NAME", None), str)
    debug_mode = cast_or_none(os.environ.get("DEBUG_MODE", False), bool)

    assert pickleprefix is not None, "pickleprefix should be defined"
    assert data_col_name is not None, "data_col_name should be defined"

    params = {
        "PICKLEPREFIX": pickleprefix,
        "DATA_COL_NAME": data_col_name,
        "PASTDAYS_START": pastdays_start,
        "PASTDAYS_END": pastdays_end,
        "FUTUREDRAWS": futuredraws,
        "TOT_CHAIN_LEN": tot_chain_len,
        "LOWER_RATIO": lower_ratio,
        "UPPER_RATIO": upper_ratio,
        "MC_TARGETACCEPT": mc_targetaccept,
        "MC_TUNE": mc_tune,
        "MC_DRAWS": mc_draws,
        "MC_CORES": mc_cores,
        "REGION": region,
        "USE_RELATIVE_RESIDUALS": use_rel_res,
        "NEW_CASES_LOCAL_COL": new_cases_local_col_name,
        "DEBUG_MODE": debug_mode,
    }

    logger.info(f"Run configuration:\n{json.dumps(params, indent=2)}")
    main(**{k.lower(): v for k, v in params.items()})
