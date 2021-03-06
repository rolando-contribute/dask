from distutils.version import LooseVersion
import pandas as pd
import pandas.util.testing as tm
import pytest
import numpy as np

import dask.dataframe as dd
from dask.async import get_sync
from dask.utils import raises, ignoring


def eq(p, d):
    if isinstance(d, dd.DataFrame):
        tm.assert_frame_equal(p, d.compute(get=get_sync))
    else:
        tm.assert_series_equal(p, d.compute(get=get_sync))


def mad(x):
    return np.fabs(x - x.mean()).mean()

def rolling_functions_tests(p, d):
    # Old-fashioned rolling API
    eq(pd.rolling_count(p, 3), dd.rolling_count(d, 3))
    eq(pd.rolling_sum(p, 3), dd.rolling_sum(d, 3))
    eq(pd.rolling_mean(p, 3), dd.rolling_mean(d, 3))
    eq(pd.rolling_median(p, 3), dd.rolling_median(d, 3))
    eq(pd.rolling_min(p, 3), dd.rolling_min(d, 3))
    eq(pd.rolling_max(p, 3), dd.rolling_max(d, 3))
    eq(pd.rolling_std(p, 3), dd.rolling_std(d, 3))
    eq(pd.rolling_var(p, 3), dd.rolling_var(d, 3))
    eq(pd.rolling_skew(p, 3), dd.rolling_skew(d, 3))
    eq(pd.rolling_kurt(p, 3), dd.rolling_kurt(d, 3))
    eq(pd.rolling_quantile(p, 3, 0.5), dd.rolling_quantile(d, 3, 0.5))
    eq(pd.rolling_apply(p, 3, mad), dd.rolling_apply(d, 3, mad))
    with ignoring(ImportError):
        eq(pd.rolling_window(p, 3, 'boxcar'), dd.rolling_window(d, 3, 'boxcar'))
    # Test with edge-case window sizes
    eq(pd.rolling_sum(p, 0), dd.rolling_sum(d, 0))
    eq(pd.rolling_sum(p, 1), dd.rolling_sum(d, 1))
    # Test with kwargs
    eq(pd.rolling_sum(p, 3, min_periods=3), dd.rolling_sum(d, 3, min_periods=3))

def basic_rolling_tests(p, d): # Works for series or df
    # New rolling API
    eq(p.rolling(3).count(), d.rolling(3).count())
    eq(p.rolling(3).sum(), d.rolling(3).sum())
    eq(p.rolling(3).mean(), d.rolling(3).mean())
    eq(p.rolling(3).median(), d.rolling(3).median())
    eq(p.rolling(3).min(), d.rolling(3).min())
    eq(p.rolling(3).max(), d.rolling(3).max())
    eq(p.rolling(3).std(), d.rolling(3).std())
    eq(p.rolling(3).var(), d.rolling(3).var())
    eq(p.rolling(3).skew(), d.rolling(3).skew())
    eq(p.rolling(3).kurt(), d.rolling(3).kurt())
    eq(p.rolling(3).quantile(0.5), d.rolling(3).quantile(0.5))
    eq(p.rolling(3).apply(mad), d.rolling(3).apply(mad))
    with ignoring(ImportError):
        eq(p.rolling(3, win_type='boxcar').sum(),
           d.rolling(3, win_type='boxcar').sum())
    # Test with edge-case window sizes
    eq(p.rolling(0).sum(), d.rolling(0).sum())
    eq(p.rolling(1).sum(), d.rolling(1).sum())
    # Test with kwargs
    eq(p.rolling(3, min_periods=2).sum(), d.rolling(3, min_periods=2).sum())

def test_rolling_functions_series():
    ts = pd.Series(np.random.randn(25).cumsum())
    dts = dd.from_pandas(ts, 3)
    rolling_functions_tests(ts, dts)


@pytest.mark.skipif(LooseVersion(pd.__version__) <= '0.18.0',
                    reason="rolling object not supported")
def test_rolling_series():
    for ts in [
            pd.Series(np.random.randn(25).cumsum()),
            pd.Series(np.random.randint(100, size=(25,)))]:
        dts = dd.from_pandas(ts, 3)
        basic_rolling_tests(ts, dts)


def test_rolling_funtions_dataframe():
    df = pd.DataFrame({'a': np.random.randn(25).cumsum(),
                       'b': np.random.randint(100, size=(25,))})
    ddf = dd.from_pandas(df, 3)
    rolling_functions_tests(df, ddf)


@pytest.mark.skipif(LooseVersion(pd.__version__) <= '0.18.0',
                    reason="rolling object not supported")
def test_rolling_dataframe():
    df = pd.DataFrame({'a': np.random.randn(25).cumsum(),
                       'b': np.random.randint(100, size=(25,))})
    ddf = dd.from_pandas(df, 3)
    basic_rolling_tests(df, ddf)


def test_rolling_functions_raises():
    df = pd.DataFrame({'a': np.random.randn(25).cumsum(),
                       'b': np.random.randint(100, size=(25,))})
    ddf = dd.from_pandas(df, 3)
    assert raises(TypeError, lambda: dd.rolling_mean(ddf, 1.5))
    assert raises(ValueError, lambda: dd.rolling_mean(ddf, -1))
    assert raises(NotImplementedError, lambda: dd.rolling_mean(ddf, 3, freq=2))
    assert raises(NotImplementedError, lambda: dd.rolling_mean(ddf, 3, how='min'))

@pytest.mark.skipif(LooseVersion(pd.__version__) <= '0.18.0',
                    reason="rolling object not supported")
def test_rolling_raises():
    df = pd.DataFrame({'a': np.random.randn(25).cumsum(),
                       'b': np.random.randint(100, size=(25,))})
    ddf = dd.from_pandas(df, 3)
    assert raises(ValueError, lambda: ddf.rolling(1.5))
    assert raises(ValueError, lambda: ddf.rolling(-1))
    assert raises(ValueError, lambda: ddf.rolling(3, min_periods=1.2))
    assert raises(ValueError, lambda: ddf.rolling(3, min_periods=-2))
    assert raises(ValueError, lambda: ddf.rolling(3, axis=10))
    assert raises(ValueError, lambda: ddf.rolling(3, axis='coulombs'))
    assert raises(NotImplementedError, lambda: ddf.rolling(100).mean().compute())


def test_rolling_functions_names():
    df = pd.DataFrame({'a': [1, 2, 3],
                       'b': [4, 5, 6]})
    a = dd.from_pandas(df, npartitions=2)
    assert sorted(dd.rolling_sum(a, 2).dask) == sorted(dd.rolling_sum(a, 2).dask)

@pytest.mark.skipif(LooseVersion(pd.__version__) <= '0.18.0',
                    reason="rolling object not supported")
def test_rolling_names():
    df = pd.DataFrame({'a': [1, 2, 3],
                       'b': [4, 5, 6]})
    a = dd.from_pandas(df, npartitions=2)
    assert sorted(a.rolling(2).sum().dask) == sorted(a.rolling(2).sum().dask)

@pytest.mark.skipif(LooseVersion(pd.__version__) <= '0.18.0',
                    reason="rolling object not supported")
def test_rolling_axis():
    df = pd.DataFrame(np.random.randn(20, 16))
    ddf = dd.from_pandas(df, npartitions=3)

    eq(df.rolling(3, axis=0).mean(), ddf.rolling(3, axis=0).mean())
    eq(df.rolling(3, axis=1).mean(), ddf.rolling(3, axis=1).mean())
    eq(df.rolling(3, min_periods=1, axis=1).mean(),
        ddf.rolling(3, min_periods=1, axis=1).mean())
    eq(df.rolling(3, axis='columns').mean(),
        ddf.rolling(3, axis='columns').mean())
    eq(df.rolling(3, axis='rows').mean(),
        ddf.rolling(3, axis='rows').mean())

    s = df[3]
    ds = ddf[3]
    eq(s.rolling(5, axis=0).std(), ds.rolling(5, axis=0).std())

def test_rolling_function_partition_size():
    df = pd.DataFrame(np.random.randn(50, 2))
    ddf = dd.from_pandas(df, npartitions=5)

    for obj, dobj in [(df, ddf), (df[0], ddf[0])]:
        eq(pd.rolling_mean(obj, 10), dd.rolling_mean(dobj, 10))
        eq(pd.rolling_mean(obj, 11), dd.rolling_mean(dobj, 11))
        raises(NotImplementedError, lambda: dd.rolling_mean(dobj, 12))

@pytest.mark.skipif(LooseVersion(pd.__version__) <= '0.18.0',
                    reason="rolling object not supported")
def test_rolling_partition_size():
    df = pd.DataFrame(np.random.randn(50, 2))
    ddf = dd.from_pandas(df, npartitions=5)

    for obj, dobj in [(df, ddf), (df[0], ddf[0])]:
        eq(obj.rolling(10).mean(), dobj.rolling(10).mean())
        eq(obj.rolling(11).mean(), dobj.rolling(11).mean())
        raises(NotImplementedError, lambda: dobj.rolling(12).mean())

@pytest.mark.skipif(LooseVersion(pd.__version__) <= '0.18.0',
                    reason="rolling object not supported")
def test_rolling_repr():
    ddf = dd.from_pandas(pd.DataFrame([10]*30), npartitions=3)
    assert repr(ddf.rolling(4)) in ['Rolling [window=4,axis=0]',
                                    'Rolling [axis=0,window=4]']
