"""Kronos loading and sampling. Needs the pinned weights (downloaded once into the Hugging Face cache).

Synthetic bars are enough here: these tests check plumbing (pins, guards, seeds, equality with upstream),
not forecast quality.
"""
import numpy as np
import pandas as pd
import pytest

import config
from lib import kronos_model as K


def synthetic_bars(n=420, seed=0):
    rng = np.random.default_rng(seed)
    close = 20000 * np.exp(np.cumsum(rng.normal(0, 0.01, n)))
    open_ = np.r_[close[0], close[:-1]] * (1 + rng.normal(0, 0.002, n))
    high = np.maximum(open_, close) * (1 + rng.uniform(0.001, 0.01, n))
    low = np.minimum(open_, close) * (1 - rng.uniform(0.001, 0.01, n))
    return pd.DataFrame({"date": pd.bdate_range("2024-01-01", periods=n), "open": open_, "high": high,
                         "low": low, "close": close})


BARS = synthetic_bars()
T_DAY = BARS["date"].iloc[410]
WINDOW = K.context_window(BARS, T_DAY, 400)


@pytest.fixture(scope="module")
def predictor():
    return K.load_predictor("cpu")


def test_models_are_in_eval_mode(predictor):
    assert not predictor.model.training and not predictor.tokenizer.training


def test_upstream_sample_count_returns_one_averaged_row(predictor):
    """Spec trap 1, shown numerically: predict(sample_count=5) is the mean of the 5 paths that 5 copies give."""
    import torch

    torch.manual_seed(11)
    averaged = predictor.predict(WINDOW[K.PRICE_COLS], WINDOW["date"], pd.Series([T_DAY]), pred_len=1, T=1.0,
                                 top_k=0, top_p=0.9, sample_count=5, verbose=False)
    paths = K.sample_next_bar(predictor, WINDOW, T_DAY, 5, 1.0, 0.9, seed=11)
    assert len(averaged) == 1
    assert len(np.unique(paths, axis=0)) > 1  # the 5 paths differ...
    np.testing.assert_allclose(averaged[K.PRICE_COLS].to_numpy()[0], paths.mean(axis=0), rtol=1e-5)  # ...and get averaged


def test_copies_give_different_samples(predictor):
    s = K.sample_upstream(predictor, WINDOW, T_DAY, 32, 1.0, 0.9, seed=3)
    assert s.shape == (32, 4) and (s.std(axis=0) > 0).all()


@pytest.mark.parametrize("T, top_p", [(1.0, 0.9), (0.6, 0.99), (1.0, 1.0)])
def test_fast_sampler_equals_upstream_sample_by_sample(predictor, T, top_p):
    """D28: the shared-work sampler must give the same numbers, bit for bit, as upstream predict_batch on copies.
    top_p = 1.0 keeps every token, so the fine (s2) draw really depends on which coarse (s1) token came first;
    with top_p = 0.9 the s2 nucleus is often one token and a wrong s1 -> s2 mapping could go unnoticed."""
    fast = K.sample_next_bar(predictor, WINDOW, T_DAY, 128, T, top_p, seed=5)
    upstream = K.sample_upstream(predictor, WINDOW, T_DAY, 128, T, top_p, seed=5)
    assert len(np.unique(fast, axis=0)) > 1
    np.testing.assert_array_equal(fast, upstream)


def test_s2_logits_follow_each_rows_own_s1(predictor):
    """The s1 -> s2 mapping, checked directly: s2 depends only weakly on s1 and one s2 token often holds most
    of the probability, so whole-sampler parity on a few samples could miss a wrong mapping."""
    import torch

    x, stamp, _, _ = K._normalise(WINDOW, predictor.clip)
    with torch.no_grad():
        s1_ctx, s2_ctx = predictor.tokenizer.encode(torch.from_numpy(x[None]), half=True)
        _, hidden = predictor.model.decode_s1(s1_ctx, s2_ctx, torch.from_numpy(stamp[None]))
        s1 = torch.tensor([[5], [900], [5], [17], [900]])
        ours = K.s2_logits_per_row(predictor.model, hidden, s1)
        upstream = predictor.model.decode_s2(hidden.expand(5, -1, -1), s1)[:, -1, :]  # one row per sample
    assert (ours[0] - ours[1]).abs().max() > 1e-3  # the rows really differ, so a wrong mapping would show
    torch.testing.assert_close(ours, upstream, rtol=0, atol=1e-5)


def test_same_seed_same_samples_new_seed_new_samples(predictor):
    a = K.sample_next_bar(predictor, WINDOW, T_DAY, 200, 1.0, 0.9, seed=1)
    b = K.sample_next_bar(predictor, WINDOW, T_DAY, 200, 1.0, 0.9, seed=1)
    c = K.sample_next_bar(predictor, WINDOW, T_DAY, 200, 1.0, 0.9, seed=2)
    np.testing.assert_array_equal(a, b)
    assert not np.array_equal(a, c)


def test_context_window_is_strictly_before_t():
    assert len(WINDOW) == 400
    assert WINDOW["date"].iloc[-1] == BARS["date"].iloc[409]  # the row right before t
    assert (WINDOW["date"] < T_DAY).all()


def test_guard_fires_on_a_window_that_includes_t(predictor):
    leaky = BARS.iloc[11:411].reset_index(drop=True)  # 400 rows ending ON t
    with pytest.raises(AssertionError, match="future"):
        K.check_context(leaky, T_DAY)
    with pytest.raises(AssertionError, match="future"):
        K.sample_next_bar(predictor, leaky, T_DAY, 4, 1.0, 0.9, seed=0)


def test_not_enough_history_is_refused():
    with pytest.raises(ValueError, match="need 400"):
        K.context_window(BARS, BARS["date"].iloc[399], 400)


def test_day_seed_depends_only_on_base_index_and_day():
    s = K.day_seed(1, "NIFTY", "2025-09-01")
    assert s == K.day_seed(1, "NIFTY", pd.Timestamp("2025-09-01"))
    assert len({s, K.day_seed(2, "NIFTY", "2025-09-01"), K.day_seed(1, "BANKNIFTY", "2025-09-01"),
                K.day_seed(1, "NIFTY", "2025-09-02")}) == 4


def test_wrong_code_pin_is_refused(monkeypatch):
    monkeypatch.setattr(config, "KRONOS_COMMIT", "0" * 40)
    with pytest.raises(K.PinMismatch, match="pinned"):
        K.check_code_pin()


def test_wrong_weights_hash_is_refused(monkeypatch):
    monkeypatch.setattr(config, "KRONOS_MODEL_SHA256", "0" * 64)
    with pytest.raises(K.PinMismatch, match="weights sha256"):
        K.load_predictor("cpu")
