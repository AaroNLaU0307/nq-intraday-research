# DATA QA ADDENDUM — structural closure (per Aaron 2026-07-29 spec)

QA-only. Contains structural facts exclusively — no strategy returns, no
Oracle output, no EV, no MC, no Checkpoint 0. **Real S0 remains locked**
pending Aaron's explicit approval; this addendum does not change that.

Base report: DATA_QA_REPORT.md (QA commit `4ab40c5`). Analysis conventions:
all wall-clock references America/New_York (ET); bar-start convention
(bar 15:44 covers 15:44:00-15:44:59, closes 15:45 = frozen forced exit);
exchange-closed time is never counted as missing (spec item 9): windows are
evaluated only on pandas-market-calendars CME_Equity scheduled trading days,
scheduled early-close afternoons are excluded days (not missing minutes),
and the 17:00-18:00 maintenance hour / weekends / holidays are out of scope
by construction.

## A1 Development (NQ.v.0 ohlcv-1m)

### 1. Coverage
- first bar: `2010-06-07 00:00:00+00:00` UTC = `2010-06-06 20:00:00-04:00` ET
- last bar:  `2021-12-31 21:59:00+00:00` UTC = `2021-12-31 16:59:00-05:00` ET
- purchased query window (metadata.json): 2010-06-06 -> 2022-01-01 UTC
  (exclusive); GLBX.MDP3 dataset itself begins 2010-06-06.
- files: 139 monthly (UTC month split); total bars 3,848,635;
  file-boundary overlaps: none; decode failures: none.

### 2. Per-file bar counts and hash verification
Every file's SHA-256 is verified against the official Databento
manifest.json inside `DevelopmentSignalLoader.load_real` BEFORE decode
(fail-closed); a decoded file below therefore implies hash match.

| file | bars | first ET date | last ET date | manifest sha256 |
|---|---|---|---|---|
| glbx-mdp3-20100606-20100630.ohlcv-1m.dbn.zst | 22,193 | 2010-06-06 | 2010-06-30 | verified |
| glbx-mdp3-20100701-20100731.ohlcv-1m.dbn.zst | 26,698 | 2010-06-30 | 2010-07-30 | verified |
| glbx-mdp3-20100801-20100831.ohlcv-1m.dbn.zst | 26,515 | 2010-08-01 | 2010-08-31 | verified |
| glbx-mdp3-20100901-20100930.ohlcv-1m.dbn.zst | 25,452 | 2010-08-31 | 2010-09-30 | verified |
| glbx-mdp3-20101001-20101031.ohlcv-1m.dbn.zst | 25,556 | 2010-09-30 | 2010-10-31 | verified |
| glbx-mdp3-20101101-20101130.ohlcv-1m.dbn.zst | 26,528 | 2010-10-31 | 2010-11-30 | verified |
| glbx-mdp3-20101201-20101231.ohlcv-1m.dbn.zst | 24,417 | 2010-11-30 | 2010-12-31 | verified |
| glbx-mdp3-20110101-20110131.ohlcv-1m.dbn.zst | 24,512 | 2011-01-02 | 2011-01-31 | verified |
| glbx-mdp3-20110201-20110228.ohlcv-1m.dbn.zst | 23,238 | 2011-01-31 | 2011-02-28 | verified |
| glbx-mdp3-20110301-20110331.ohlcv-1m.dbn.zst | 28,923 | 2011-02-28 | 2011-03-31 | verified |
| glbx-mdp3-20110401-20110430.ohlcv-1m.dbn.zst | 24,064 | 2011-03-31 | 2011-04-29 | verified |
| glbx-mdp3-20110501-20110531.ohlcv-1m.dbn.zst | 26,575 | 2011-05-01 | 2011-05-31 | verified |
| glbx-mdp3-20110601-20110630.ohlcv-1m.dbn.zst | 27,127 | 2011-05-31 | 2011-06-30 | verified |
| glbx-mdp3-20110701-20110731.ohlcv-1m.dbn.zst | 25,691 | 2011-06-30 | 2011-07-31 | verified |
| glbx-mdp3-20110801-20110831.ohlcv-1m.dbn.zst | 30,151 | 2011-07-31 | 2011-08-31 | verified |
| glbx-mdp3-20110901-20110930.ohlcv-1m.dbn.zst | 28,381 | 2011-08-31 | 2011-09-30 | verified |
| glbx-mdp3-20111001-20111031.ohlcv-1m.dbn.zst | 27,918 | 2011-10-02 | 2011-10-31 | verified |
| glbx-mdp3-20111101-20111130.ohlcv-1m.dbn.zst | 28,346 | 2011-10-31 | 2011-11-30 | verified |
| glbx-mdp3-20111201-20111231.ohlcv-1m.dbn.zst | 25,430 | 2011-11-30 | 2011-12-30 | verified |
| glbx-mdp3-20120101-20120131.ohlcv-1m.dbn.zst | 24,916 | 2012-01-03 | 2012-01-31 | verified |
| glbx-mdp3-20120201-20120229.ohlcv-1m.dbn.zst | 25,822 | 2012-01-31 | 2012-02-29 | verified |
| glbx-mdp3-20120301-20120331.ohlcv-1m.dbn.zst | 26,984 | 2012-02-29 | 2012-03-30 | verified |
| glbx-mdp3-20120401-20120430.ohlcv-1m.dbn.zst | 25,898 | 2012-04-01 | 2012-04-30 | verified |
| glbx-mdp3-20120501-20120531.ohlcv-1m.dbn.zst | 29,444 | 2012-04-30 | 2012-05-31 | verified |
| glbx-mdp3-20120601-20120630.ohlcv-1m.dbn.zst | 26,886 | 2012-05-31 | 2012-06-29 | verified |
| glbx-mdp3-20120701-20120731.ohlcv-1m.dbn.zst | 27,383 | 2012-07-01 | 2012-07-31 | verified |
| glbx-mdp3-20120801-20120831.ohlcv-1m.dbn.zst | 28,214 | 2012-07-31 | 2012-08-31 | verified |
| glbx-mdp3-20120901-20120930.ohlcv-1m.dbn.zst | 24,383 | 2012-09-02 | 2012-09-30 | verified |
| glbx-mdp3-20121001-20121031.ohlcv-1m.dbn.zst | 28,589 | 2012-09-30 | 2012-10-31 | verified |
| glbx-mdp3-20121101-20121130.ohlcv-1m.dbn.zst | 26,600 | 2012-10-31 | 2012-11-30 | verified |
| glbx-mdp3-20121201-20121231.ohlcv-1m.dbn.zst | 24,192 | 2012-12-02 | 2012-12-31 | verified |
| glbx-mdp3-20130101-20130131.ohlcv-1m.dbn.zst | 25,908 | 2013-01-02 | 2013-01-31 | verified |
| glbx-mdp3-20130201-20130228.ohlcv-1m.dbn.zst | 23,296 | 2013-01-31 | 2013-02-28 | verified |
| glbx-mdp3-20130301-20130331.ohlcv-1m.dbn.zst | 23,599 | 2013-02-28 | 2013-03-31 | verified |
| glbx-mdp3-20130401-20130430.ohlcv-1m.dbn.zst | 27,518 | 2013-03-31 | 2013-04-30 | verified |
| glbx-mdp3-20130501-20130531.ohlcv-1m.dbn.zst | 27,007 | 2013-04-30 | 2013-05-31 | verified |
| glbx-mdp3-20130601-20130630.ohlcv-1m.dbn.zst | 25,774 | 2013-06-02 | 2013-06-30 | verified |
| glbx-mdp3-20130701-20130731.ohlcv-1m.dbn.zst | 27,284 | 2013-06-30 | 2013-07-31 | verified |
| glbx-mdp3-20130801-20130831.ohlcv-1m.dbn.zst | 27,689 | 2013-07-31 | 2013-08-30 | verified |
| glbx-mdp3-20130901-20130930.ohlcv-1m.dbn.zst | 24,326 | 2013-09-02 | 2013-09-30 | verified |
| glbx-mdp3-20131001-20131031.ohlcv-1m.dbn.zst | 29,651 | 2013-09-30 | 2013-10-31 | verified |
| glbx-mdp3-20131101-20131130.ohlcv-1m.dbn.zst | 24,701 | 2013-10-31 | 2013-11-29 | verified |
| glbx-mdp3-20131201-20131231.ohlcv-1m.dbn.zst | 24,193 | 2013-12-01 | 2013-12-31 | verified |
| glbx-mdp3-20140101-20140131.ohlcv-1m.dbn.zst | 25,936 | 2014-01-02 | 2014-01-31 | verified |
| glbx-mdp3-20140201-20140228.ohlcv-1m.dbn.zst | 24,502 | 2014-02-02 | 2014-02-28 | verified |
| glbx-mdp3-20140301-20140331.ohlcv-1m.dbn.zst | 26,582 | 2014-03-02 | 2014-03-31 | verified |
| glbx-mdp3-20140401-20140430.ohlcv-1m.dbn.zst | 26,706 | 2014-03-31 | 2014-04-30 | verified |
| glbx-mdp3-20140501-20140531.ohlcv-1m.dbn.zst | 27,006 | 2014-04-30 | 2014-05-30 | verified |
| glbx-mdp3-20140601-20140630.ohlcv-1m.dbn.zst | 22,946 | 2014-06-01 | 2014-06-30 | verified |
| glbx-mdp3-20140701-20140731.ohlcv-1m.dbn.zst | 27,427 | 2014-06-30 | 2014-07-31 | verified |
| glbx-mdp3-20140801-20140831.ohlcv-1m.dbn.zst | 25,945 | 2014-07-31 | 2014-08-31 | verified |
| glbx-mdp3-20140901-20140930.ohlcv-1m.dbn.zst | 22,625 | 2014-08-31 | 2014-09-30 | verified |
| glbx-mdp3-20141001-20141031.ohlcv-1m.dbn.zst | 30,229 | 2014-09-30 | 2014-10-31 | verified |
| glbx-mdp3-20141101-20141130.ohlcv-1m.dbn.zst | 25,200 | 2014-11-02 | 2014-11-30 | verified |
| glbx-mdp3-20141201-20141231.ohlcv-1m.dbn.zst | 26,529 | 2014-11-30 | 2014-12-30 | verified |
| glbx-mdp3-20150101-20150131.ohlcv-1m.dbn.zst | 27,618 | 2015-01-01 | 2015-01-30 | verified |
| glbx-mdp3-20150201-20150228.ohlcv-1m.dbn.zst | 24,597 | 2015-02-01 | 2015-02-27 | verified |
| glbx-mdp3-20150301-20150331.ohlcv-1m.dbn.zst | 27,348 | 2015-03-01 | 2015-03-31 | verified |
| glbx-mdp3-20150401-20150430.ohlcv-1m.dbn.zst | 26,962 | 2015-03-31 | 2015-04-30 | verified |
| glbx-mdp3-20150501-20150531.ohlcv-1m.dbn.zst | 25,533 | 2015-04-30 | 2015-05-31 | verified |
| glbx-mdp3-20150601-20150630.ohlcv-1m.dbn.zst | 27,049 | 2015-05-31 | 2015-06-30 | verified |
| glbx-mdp3-20150701-20150731.ohlcv-1m.dbn.zst | 29,390 | 2015-06-30 | 2015-07-31 | verified |
| glbx-mdp3-20150801-20150831.ohlcv-1m.dbn.zst | 27,717 | 2015-08-02 | 2015-08-31 | verified |
| glbx-mdp3-20150901-20150930.ohlcv-1m.dbn.zst | 29,311 | 2015-08-31 | 2015-09-30 | verified |
| glbx-mdp3-20151001-20151031.ohlcv-1m.dbn.zst | 29,220 | 2015-09-30 | 2015-10-30 | verified |
| glbx-mdp3-20151101-20151130.ohlcv-1m.dbn.zst | 26,970 | 2015-11-01 | 2015-11-30 | verified |
| glbx-mdp3-20151201-20151231.ohlcv-1m.dbn.zst | 28,252 | 2015-11-30 | 2015-12-31 | verified |
| glbx-mdp3-20160101-20160131.ohlcv-1m.dbn.zst | 27,060 | 2016-01-03 | 2016-01-31 | verified |
| glbx-mdp3-20160201-20160229.ohlcv-1m.dbn.zst | 28,248 | 2016-01-31 | 2016-02-29 | verified |
| glbx-mdp3-20160301-20160331.ohlcv-1m.dbn.zst | 28,816 | 2016-02-29 | 2016-03-31 | verified |
| glbx-mdp3-20160401-20160430.ohlcv-1m.dbn.zst | 27,818 | 2016-03-31 | 2016-04-29 | verified |
| glbx-mdp3-20160501-20160531.ohlcv-1m.dbn.zst | 28,627 | 2016-05-01 | 2016-05-31 | verified |
| glbx-mdp3-20160601-20160630.ohlcv-1m.dbn.zst | 28,585 | 2016-05-31 | 2016-06-30 | verified |
| glbx-mdp3-20160701-20160731.ohlcv-1m.dbn.zst | 27,214 | 2016-06-30 | 2016-07-31 | verified |
| glbx-mdp3-20160801-20160831.ohlcv-1m.dbn.zst | 29,040 | 2016-07-31 | 2016-08-31 | verified |
| glbx-mdp3-20160901-20160930.ohlcv-1m.dbn.zst | 28,047 | 2016-08-31 | 2016-09-30 | verified |
| glbx-mdp3-20161001-20161031.ohlcv-1m.dbn.zst | 27,511 | 2016-10-02 | 2016-10-31 | verified |
| glbx-mdp3-20161101-20161130.ohlcv-1m.dbn.zst | 28,560 | 2016-10-31 | 2016-11-30 | verified |
| glbx-mdp3-20161201-20161231.ohlcv-1m.dbn.zst | 26,719 | 2016-11-30 | 2016-12-30 | verified |
| glbx-mdp3-20170101-20170131.ohlcv-1m.dbn.zst | 27,543 | 2017-01-02 | 2017-01-31 | verified |
| glbx-mdp3-20170201-20170228.ohlcv-1m.dbn.zst | 26,249 | 2017-01-31 | 2017-02-28 | verified |
| glbx-mdp3-20170301-20170331.ohlcv-1m.dbn.zst | 30,344 | 2017-02-28 | 2017-03-31 | verified |
| glbx-mdp3-20170401-20170430.ohlcv-1m.dbn.zst | 25,354 | 2017-04-02 | 2017-04-30 | verified |
| glbx-mdp3-20170501-20170531.ohlcv-1m.dbn.zst | 30,184 | 2017-04-30 | 2017-05-31 | verified |
| glbx-mdp3-20170601-20170630.ohlcv-1m.dbn.zst | 29,241 | 2017-05-31 | 2017-06-30 | verified |
| glbx-mdp3-20170701-20170731.ohlcv-1m.dbn.zst | 27,869 | 2017-07-02 | 2017-07-31 | verified |
| glbx-mdp3-20170801-20170831.ohlcv-1m.dbn.zst | 31,019 | 2017-07-31 | 2017-08-31 | verified |
| glbx-mdp3-20170901-20170930.ohlcv-1m.dbn.zst | 27,995 | 2017-08-31 | 2017-09-29 | verified |
| glbx-mdp3-20171001-20171031.ohlcv-1m.dbn.zst | 29,542 | 2017-10-01 | 2017-10-31 | verified |
| glbx-mdp3-20171101-20171130.ohlcv-1m.dbn.zst | 29,289 | 2017-10-31 | 2017-11-30 | verified |
| glbx-mdp3-20171201-20171231.ohlcv-1m.dbn.zst | 26,842 | 2017-11-30 | 2017-12-29 | verified |
| glbx-mdp3-20180101-20180131.ohlcv-1m.dbn.zst | 29,720 | 2018-01-01 | 2018-01-31 | verified |
| glbx-mdp3-20180201-20180228.ohlcv-1m.dbn.zst | 27,053 | 2018-01-31 | 2018-02-28 | verified |
| glbx-mdp3-20180301-20180331.ohlcv-1m.dbn.zst | 28,572 | 2018-02-28 | 2018-03-29 | verified |
| glbx-mdp3-20180401-20180430.ohlcv-1m.dbn.zst | 28,725 | 2018-04-01 | 2018-04-30 | verified |
| glbx-mdp3-20180501-20180531.ohlcv-1m.dbn.zst | 31,040 | 2018-04-30 | 2018-05-31 | verified |
| glbx-mdp3-20180601-20180630.ohlcv-1m.dbn.zst | 28,491 | 2018-05-31 | 2018-06-29 | verified |
| glbx-mdp3-20180701-20180731.ohlcv-1m.dbn.zst | 29,717 | 2018-07-01 | 2018-07-31 | verified |
| glbx-mdp3-20180801-20180831.ohlcv-1m.dbn.zst | 31,221 | 2018-07-31 | 2018-08-31 | verified |
| glbx-mdp3-20180901-20180930.ohlcv-1m.dbn.zst | 27,135 | 2018-09-02 | 2018-09-30 | verified |
| glbx-mdp3-20181001-20181031.ohlcv-1m.dbn.zst | 31,378 | 2018-09-30 | 2018-10-31 | verified |
| glbx-mdp3-20181101-20181130.ohlcv-1m.dbn.zst | 29,472 | 2018-10-31 | 2018-11-30 | verified |
| glbx-mdp3-20181201-20181231.ohlcv-1m.dbn.zst | 26,654 | 2018-12-02 | 2018-12-31 | verified |
| glbx-mdp3-20190101-20190131.ohlcv-1m.dbn.zst | 29,865 | 2019-01-01 | 2019-01-31 | verified |
| glbx-mdp3-20190201-20190228.ohlcv-1m.dbn.zst | 26,885 | 2019-01-31 | 2019-02-28 | verified |
| glbx-mdp3-20190301-20190331.ohlcv-1m.dbn.zst | 28,716 | 2019-02-28 | 2019-03-31 | verified |
| glbx-mdp3-20190401-20190430.ohlcv-1m.dbn.zst | 28,645 | 2019-03-31 | 2019-04-30 | verified |
| glbx-mdp3-20190501-20190531.ohlcv-1m.dbn.zst | 31,042 | 2019-04-30 | 2019-05-31 | verified |
| glbx-mdp3-20190601-20190630.ohlcv-1m.dbn.zst | 27,387 | 2019-06-02 | 2019-06-30 | verified |
| glbx-mdp3-20190701-20190731.ohlcv-1m.dbn.zst | 30,939 | 2019-06-30 | 2019-07-31 | verified |
| glbx-mdp3-20190801-20190831.ohlcv-1m.dbn.zst | 29,908 | 2019-07-31 | 2019-08-30 | verified |
| glbx-mdp3-20190901-20190930.ohlcv-1m.dbn.zst | 28,555 | 2019-09-01 | 2019-09-30 | verified |
| glbx-mdp3-20191001-20191031.ohlcv-1m.dbn.zst | 31,383 | 2019-09-30 | 2019-10-31 | verified |
| glbx-mdp3-20191101-20191130.ohlcv-1m.dbn.zst | 28,102 | 2019-10-31 | 2019-11-29 | verified |
| glbx-mdp3-20191201-20191231.ohlcv-1m.dbn.zst | 28,419 | 2019-12-01 | 2019-12-31 | verified |
| glbx-mdp3-20200101-20200131.ohlcv-1m.dbn.zst | 29,796 | 2020-01-01 | 2020-01-31 | verified |
| glbx-mdp3-20200201-20200229.ohlcv-1m.dbn.zst | 26,728 | 2020-02-02 | 2020-02-28 | verified |
| glbx-mdp3-20200301-20200331.ohlcv-1m.dbn.zst | 28,204 | 2020-03-01 | 2020-03-31 | verified |
| glbx-mdp3-20200401-20200430.ohlcv-1m.dbn.zst | 28,666 | 2020-03-31 | 2020-04-30 | verified |
| glbx-mdp3-20200501-20200531.ohlcv-1m.dbn.zst | 28,439 | 2020-04-30 | 2020-05-31 | verified |
| glbx-mdp3-20200601-20200630.ohlcv-1m.dbn.zst | 29,513 | 2020-05-31 | 2020-06-30 | verified |
| glbx-mdp3-20200701-20200731.ohlcv-1m.dbn.zst | 31,050 | 2020-06-30 | 2020-07-31 | verified |
| glbx-mdp3-20200801-20200831.ohlcv-1m.dbn.zst | 28,779 | 2020-08-02 | 2020-08-31 | verified |
| glbx-mdp3-20200901-20200930.ohlcv-1m.dbn.zst | 29,801 | 2020-08-31 | 2020-09-30 | verified |
| glbx-mdp3-20201001-20201031.ohlcv-1m.dbn.zst | 29,909 | 2020-09-30 | 2020-10-30 | verified |
| glbx-mdp3-20201101-20201130.ohlcv-1m.dbn.zst | 28,288 | 2020-11-01 | 2020-11-30 | verified |
| glbx-mdp3-20201201-20201231.ohlcv-1m.dbn.zst | 29,757 | 2020-11-30 | 2020-12-31 | verified |
| glbx-mdp3-20210101-20210131.ohlcv-1m.dbn.zst | 27,134 | 2021-01-03 | 2021-01-31 | verified |
| glbx-mdp3-20210201-20210228.ohlcv-1m.dbn.zst | 27,073 | 2021-01-31 | 2021-02-28 | verified |
| glbx-mdp3-20210301-20210331.ohlcv-1m.dbn.zst | 31,446 | 2021-02-28 | 2021-03-31 | verified |
| glbx-mdp3-20210401-20210430.ohlcv-1m.dbn.zst | 29,455 | 2021-03-31 | 2021-04-30 | verified |
| glbx-mdp3-20210501-20210531.ohlcv-1m.dbn.zst | 28,554 | 2021-05-02 | 2021-05-31 | verified |
| glbx-mdp3-20210601-20210630.ohlcv-1m.dbn.zst | 30,043 | 2021-05-31 | 2021-06-30 | verified |
| glbx-mdp3-20210701-20210731.ohlcv-1m.dbn.zst | 29,996 | 2021-06-30 | 2021-07-30 | verified |
| glbx-mdp3-20210801-20210831.ohlcv-1m.dbn.zst | 30,479 | 2021-08-01 | 2021-08-31 | verified |
| glbx-mdp3-20210901-20210930.ohlcv-1m.dbn.zst | 30,105 | 2021-08-31 | 2021-09-30 | verified |
| glbx-mdp3-20211001-20211031.ohlcv-1m.dbn.zst | 28,979 | 2021-09-30 | 2021-10-31 | verified |
| glbx-mdp3-20211101-20211130.ohlcv-1m.dbn.zst | 29,833 | 2021-10-31 | 2021-11-30 | verified |
| glbx-mdp3-20211201-20211231.ohlcv-1m.dbn.zst | 30,296 | 2021-11-30 | 2021-12-31 | verified |

### 3. Trading days
- scheduled (CME_Equity, 2010-06-06..2021-12-31): **2989** (of which 97 scheduled early closes)
- observed days with RTH bars: **2969**
- RTH bars on non-scheduled days: 0 (none)
- scheduled days with ZERO RTH bars: 20 — classified:
  - 6 vendor-degraded (also in Databento condition.json): 2014-06-12, 2014-06-13, 2014-09-23, 2014-09-24, 2014-09-25, 2014-12-31
  - 14 known market closures the calendar model does not
    carry (3x Good Friday 2012/2015/2021; 2x Hurricane Sandy 2012-10-29/30;
    9x 2012-2014-era holidays with no RTH session under CME's then-current
    holiday schedule): 2012-04-06, 2012-10-29, 2012-10-30, 2012-11-22, 2013-01-21, 2013-02-18, 2013-05-27, 2013-07-04, 2013-09-02, 2013-11-28, 2014-01-20, 2014-02-17, 2015-04-03, 2021-04-02
  Downstream these fall under the frozen S0 SS3 exclusion rules (zero-bar
  day); QA records facts only.

### 4. Window 09:30-10:00 ET (30 bars, frozen observation window)
- complete days: **2960** of 2969
- incomplete days: **9** (missing minutes total 53)

### 5. Window 10:00-15:44 ET (345 bars, frozen PM window)
- complete days: **2873**
- excluded days (scheduled early close, afternoon not traded): **85**
- incomplete days (missing data within an open window): **11** (missing minutes total 648)

### 4+5. Incomplete-day detail and exclusion reasons (all 20 rows)

| date | window | present/expected | classification |
|---|---|---|---|
| 2010-09-10 | 1000-1544 | 344/345 | no_trade_minutes_omitted (trade-aggregated OHLCV; thin 2010-2013 era) |
| 2010-12-23 | 1000-1544 | 344/345 | no_trade_minutes_omitted (trade-aggregated OHLCV; thin 2010-2013 era) |
| 2010-12-28 | 1000-1544 | 344/345 | no_trade_minutes_omitted (trade-aggregated OHLCV; thin 2010-2013 era) |
| 2010-12-29 | 1000-1544 | 341/345 | no_trade_minutes_omitted (trade-aggregated OHLCV; thin 2010-2013 era) |
| 2010-12-30 | 1000-1544 | 343/345 | no_trade_minutes_omitted (trade-aggregated OHLCV; thin 2010-2013 era) |
| 2011-05-30 | 0930-1000 | 26/30 | holiday_session_thin_morning (scheduled early-close holiday) |
| 2011-07-04 | 0930-1000 | 29/30 | holiday_session_thin_morning (scheduled early-close holiday) |
| 2012-01-16 | 0930-1000 | 28/30 | holiday_session_thin_morning (scheduled early-close holiday) |
| 2012-03-09 | 1000-1544 | 344/345 | no_trade_minutes_omitted (trade-aggregated OHLCV; thin 2010-2013 era) |
| 2012-03-12 | 1000-1544 | 341/345 | no_trade_minutes_omitted (trade-aggregated OHLCV; thin 2010-2013 era) |
| 2013-12-13 | 1000-1544 | 344/345 | no_trade_minutes_omitted (trade-aggregated OHLCV; thin 2010-2013 era) |
| 2014-07-04 | 0930-1000 | 29/30 | holiday_session_thin_morning (scheduled early-close holiday) |
| 2014-09-01 | 0930-1000 | 28/30 | holiday_session_thin_morning (scheduled early-close holiday) |
| 2015-02-16 | 0930-1000 | 28/30 | holiday_session_thin_morning (scheduled early-close holiday) |
| 2020-02-28 | 1000-1544 | 59/345 | vendor_degraded_gap (Databento condition.json) |
| 2020-03-09 | 0930-1000 | 16/30 | market_halt_period (COVID limit/circuit-breaker era; structural, not data loss) |
| 2020-03-12 | 0930-1000 | 17/30 | market_halt_period (COVID limit/circuit-breaker era; structural, not data loss) |
| 2020-03-16 | 0930-1000 | 16/30 | market_halt_period (COVID limit/circuit-breaker era; structural, not data loss) |
| 2020-03-18 | 1000-1544 | 332/345 | market_halt_period (COVID limit/circuit-breaker era; structural, not data loss) |
| 2020-06-30 | 1000-1544 | 11/345 | vendor_degraded_gap (Databento condition.json) |

Notes: the two vendor gaps (2020-02-28: 286 min; 2020-06-30: 334 min) are
the only large in-window holes and both are vendor-documented degraded
dates; 2020-03 rows are COVID circuit-breaker/halt minutes (no trades ->
no bars in trade-aggregated OHLCV); remaining rows are 1-4 thin no-trade
minutes in the 2010-2013 low-volume era. The frozen >10%-missing exclusion
rule governs day eligibility downstream; QA does not decide.

### 6. ADR14 lookback completeness (availability only — no values computed)
- frozen definition (prereg): mean RTH range of the prior 14 COMPLETE RTH
  days, excluding the current day; complete RTH day = scheduled full day
  with all 390 bars 09:30-15:59.
- complete RTH days in sample: **2870**
- candidate D-days (both frozen windows complete): **2870**
- warm-up days lacking a full 14-day lookback: **14** (2010-06-07 .. 2010-06-24)
- first day with full lookback: **2010-06-25**
- handling: warm-up days are structurally ineligible for ADR14-normalized
  features/labels and are excluded by the frozen normalization definition;
  ADR14 numeric values were NOT computed at QA stage.

### 7. Explicit anomaly counts (all 139 files, 3,848,635 bars)
- duplicate (ET date, minute) slots: **0**
- NaN price rows: **0**; inf price rows: **0**;
  non-positive price rows: **0**
- OHLC consistency violations (H<L, H<max(O,C), L>min(O,C)): **0**
- zero/negative volume rows: **0** (in RTH: **0**)
- missing minutes inside frozen windows on scheduled open time: **701** (53 + 648; itemized above)
- loader qa_bars events across all files: none (0 duplicate_minute,
  0 bad_price, 0 zero_volume).

### 8. DST / holidays / half-days / rolls
- DST: 23 transitions in coverage.
  US transitions occur 02:00 local Sunday while Globex equity is closed
  (Friday-close..Sunday-18:00 gap); dates listed are the first post-switch
  midnights (Mondays), all of which show full RTH sessions. UTC->ET
  conversion via zoneinfo America/New_York (DST-safe); no duplicate or
  phantom RTH minutes observed on any transition-adjacent day (global
  duplicate count 0).
- holidays: zero-bar scheduled days itemized in section 3; scheduled
  early-close days observed with RTH bars: 85 of 97 scheduled; the other 12 are
  early-close-scheduled days among the 20 zero-bar closures above.
  Early-close afternoons are excluded days, never missing minutes.
- rolls: **47** instrument transitions (quarterly cadence,
  2010-06..2021-12 => ~46-47 expected). All transitions occur exactly at
  00:00 UTC (Databento v.0 continuous remaps daily by prior-day volume);
  instrument_ids are unmapped integers (map_symbols=false; symbology file
  not included in the batch package) — the transition COUNT and dates are
  the structural facts; per the frozen spec, F5 gap is recorded NA on
  is_roll_transition days downstream.
- Databento condition.json: {"available": 3604, "degraded": 20}; degraded dates: 20, of which 6 are zero-bar
  days and 2 (2020-02-28, 2020-06-30) are the large in-window gaps; the
  remaining degraded dates decoded with complete frozen windows.

### 9. Closed-time handling
Confirmed by construction: window statistics are computed only over
scheduled trading days from the frozen calendar source; weekends, holidays,
the 17:00-18:00 maintenance hour, overnight hours, and scheduled early-close
afternoons never enter any missing-minute count.

## A2 Execution-Cost Calibration (MNQ.v.0 bbo-1s)

### 1. Per-month raw rows, timestamps, date coverage
Files are split by RECEIPT month (UTC); the `ts` column is ts_event = last
book-update time, which lawfully lags into the prior calendar day across
closed periods (e.g. the January file opens with the frozen book state
stamped 2024-12-31 21:59:59 UTC = 16:59:59 ET NYE close) and is undefined
(NaT) on session-start snapshot rows.

| file | rows | first ts_event UTC | last ts_event UTC | ET dates |
|---|---|---|---|---|
| glbx-mdp3-20250101-20250131.bbo-1s.dbn.zst | 1,700,017 | 2024-12-31T21:59:59.058162963+00:00 | 2025-01-31T21:59:59.415826043+00:00 | 2024-12-31..2025-01-31 (28d) |
| glbx-mdp3-20250201-20250228.bbo-1s.dbn.zst | 1,567,255 | 2025-02-02T23:00:00.194919337+00:00 | 2025-02-28T21:59:59.697830711+00:00 | 2025-02-02..2025-02-28 (24d) |
| glbx-mdp3-20250301-20250331.bbo-1s.dbn.zst | 1,680,120 | 2025-03-02T23:00:00.996808999+00:00 | 2025-03-31T23:59:58.892135113+00:00 | 2025-03-02..2025-03-31 (26d) |

- total rows: **4,947,392**; per-file manifest SHA-256 verified
  before decode (fail-closed), as in A1.
- Databento condition.json (A2): {"available": 77}; non-available dates: none.

### 2. crossed_or_invalid_spread per month

| file | crossed (ask<bid) | denominator | fraction |
|---|---|---|---|
| glbx-mdp3-20250101-20250131.bbo-1s.dbn.zst | 337 | 1,700,017 | 0.0198% |
| glbx-mdp3-20250201-20250228.bbo-1s.dbn.zst | 440 | 1,567,255 | 0.0281% |
| glbx-mdp3-20250301-20250331.bbo-1s.dbn.zst | 314 | 1,680,120 | 0.0187% |

- max single-file fraction: **0.0281%** — two orders of magnitude below the 1% fail-closed threshold.
- totals: crossed 1091; NaN spread 0;
  locked (ask==bid) 40.

### 3. Definitions
- crossed = `ask_px < bid_px` (spread < 0). Excluded with QA event.
- `ask == bid` (locked book, spread 0): KEPT as valid 0-spread observations
  (40 rows of 4,947,392; ~1 per 124k rows — no material
  effect on per-minute medians/percentiles).
- NaN spread rows: 0 in all three files.
- NaT ts_event rows (undefined-timestamp sentinel): 299 total, of which 84
  carry a valid spread — see section 4.

### 4. Exclusion before aggregation (and one bookkeeping fix)
Confirmed: the invalid mask (spread<0 | NaN spread | NaT ts_event) is
applied BEFORE the per-minute groupby; only valid rows enter the spread
table (cost_calibration_loader._spread_table; regression-tested).
Found during this addendum: 84 valid-spread rows with NaT ts_event were
previously dropped SILENTLY by the minute groupby (NaN group key). This
violated the frozen every-cleaning-decision-is-a-QA-event rule and was
patched in this commit: they are now excluded explicitly with a
`nat_timestamp_excluded` QA event (per month: 9 / 13 / 62). The exclusion
set is unchanged, therefore the aggregation is numerically identical:
spread_cost_table.csv is byte-identical before/after the patch
(sha256 `b6d6984ff7c364f9...`, unchanged; full hash in section 7).

### 5. Seeded crossed-row forensics (seed 20260729, k=5 per month)
Sampled crossed rows with +/-2 neighbor context (bounded summaries via the
loader's private diagnostic; raw BBO frames never left the loader module):
- NOT a bid/ask field swap: only 0.0221% of rows are crossed; a swapped
  file would be ~100% crossed. Sampled neighbors show normal positive
  spreads adjacent to crossings.
- NOT price scaling: mid-price vs neighbor mid ratios 0.9974-1.0000; all
  prices are on the 0.25 tick grid at plausible NQ levels.
- NOT schema mapping: windows decode coherently; e.g. a February crossing
  of -80.0 points at 16:59:59.88 ET normalizes to +1.75 points on the very
  next row at the 18:00:00.97 ET reopen.
- Phase census of all 1,091 crossed rows (by ts_event ET wall-clock):
  - 20250101-20250131: {"other_open": 178, "rth_0930_1600": 104, "nat_ts": 55}, RTH magnitude {"n": 104, "ticks_median": 38.0, "ticks_p95": 507.35, "ticks_max": 532.0}
  - 20250201-20250228: {"other_open": 203, "rth_0930_1600": 152, "nat_ts": 85}, RTH magnitude {"n": 152, "ticks_median": 31.5, "ticks_p95": 232.0, "ticks_max": 376.0}
  - 20250301-20250331: {"other_open": 226, "nat_ts": 75, "rth_0930_1600": 13}, RTH magnitude {"n": 13, "ticks_median": 260.0, "ticks_p95": 435.6, "ticks_max": 555.0}
  Boundary/NaT clusters (session close 16:59:59, Sunday pre-open, early-
  close boundary 12:59:59 on 2025-01-20 MLK) show large persistent
  crossings that resolve exactly at reopen — book states disseminated
  while matching is halted, when resting orders may lawfully cross.
  In-RTH crossings (269 seconds of ~1.45M RTH seconds, 0.019%) also show
  large magnitudes (median 31-260 ticks) concentrated in volatile
  sessions, CONSISTENT WITH momentary matching pauses (CME Stop/Velocity
  Logic) — this attribution is a Level-3 inference not verifiable from
  bbo-1s alone and is recorded as hypothesis, not fact. All crossed rows
  are excluded from the spread table regardless of phase.

### 6. Per-slot sample counts (from spread_cost_table.csv, 3 months summed)
- 1380 covered slots: n_obs min 3,072 / median 3,606 / max 3,797; zero-sample covered slots: 0
- 390 RTH slots (09:30-16:00): n_obs min 3,598 / median 3,710 / max 3,732; zero-sample RTH slots: 0
- absent slots: 60 = exactly the 17:00-17:59 ET maintenance hour (exchange closed — correct absence, not missing data).

### 7. spread_cost_table.csv
- schema: ['minute_of_day_et', 'spread_median_points', 'spread_p90_points', 'spread_p95_points', 'n_obs']
- rows: 1380
- sha256: `b6d6984ff7c364f9a57514d7583685956f6b080ec02027ee8401f38f6d9509bf`

## Evidence chain

- QA commit: `4ab40c5` (base report, attestation, flag, loader QA-eventization);
  this addendum and the NaT bookkeeping patch land in the follow-up commit.
- physical_copy_attestation.json sha256 (recomputed now): `51ce415c6e2c06eb363d8061b9543c13d1b9ff11dfecbd9ec2312e3c66212813`
  — matches the value recorded inside SECOND_COPY_ATTESTED.flag. Content:
  20304<->20304 files, 10207 official manifest entries, all_raw_sha256_match=True, verified_at 2026-07-28T16:04:43.183375+00:00, all mismatch lists empty.
- primary A1 manifest.json sha256: `d8d1edc7b549b441d691dda74331806c957a19946e746bd795978e01d73c3ae8`
- primary A2 manifest.json sha256: `02014289a54658ad03a4e495ac8bb76d362418702e5e4e00671190baa38c9a97`
  - backup A1 manifest.json: E: drive NOT mounted at addendum time (removable disk). Backup equality rests on the attestation's three-way per-file match at verification time; re-verification requires remounting the drive.
  - backup A2 manifest.json: E: drive NOT mounted at addendum time (removable disk). Backup equality rests on the attestation's three-way per-file match at verification time; re-verification requires remounting the drive.
- loader/code lineage: 25cb93b (skeleton) -> 931bcbc (orchestrator) ->
  a0e0136 (pre-attestation tooling) -> a88b5ba (real-data loaders) ->
  bbe67bb (verify v2) -> 4ab40c5 (QA eventization) -> this commit
  (NaT event patch + QA-addendum diagnostics).
- G9 evidence resolution: commit `f932714` (MC1.1-G9 addendum, Case A);
  gate1/G9_RESOLVED.flag content:
  > G9 resolved 2026-07-28 via MC1.1-G9 Evidence Resolution Addendum.
  > Evidence: cme_fee_schedule_2026-07-27.xls sha256 7c4ff19c6f732ca176b71c86c273bff8c481615656ad539d29d44dc2915bf90b
  > See gate1/G9_EVIDENCE_RESOLUTION.md
- ops/SECOND_COPY_ATTESTED.flag (created in 4ab40c5) content:
  > second_physical_copy_verified: true
  > attested: 2026-07-29 per Aaron-approved sequence (copy confirmed by Aaron,
  > three-way verification all_raw_sha256_match=true, 20304<->20304 files,
  > 10207 official manifest entries matched)
  > attestation: ops/physical_copy_attestation.json sha256 51ce415c6e2c06eb363d8061b9543c13d1b9ff11dfecbd9ec2312e3c66212813
- QA thresholds and versions:
  - crossed/invalid/NaT exclusion threshold: >1% of a file fails closed;
    below threshold rows are excluded WITH QA events (never silently).
  - qa_bars taxonomy: duplicate_minute / bad_price / zero_volume /
    missing_minute / pre_launch_row / schema_gap; MNQ launch boundary
    2019-05-06; Development window [2010-06-06, 2025-07-01) fail-closed.
  - frozen day-exclusion rules (S0 SS3, incl. >10%-missing) are applied
    downstream at S0 time, not at QA time.
  - toolchain: Python 3.13.14, databento 0.81.0, pandas 2.3.3, pandas-market-calendars 5.4.0; calendar CME_Equity; tz zoneinfo America/New_York.
- flags state at render time: gate1/G9_RESOLVED.flag PRESENT (f932714,
  2026-07-28); ops/SECOND_COPY_ATTESTED.flag PRESENT (4ab40c5, 2026-07-29);
  guards.assert_real_run_allowed() passes mechanically, but real S0 remains
  ADMINISTRATIVELY LOCKED pending Aaron's explicit approval of the QA
  report and this addendum.

## Mechanical re-checks (run at render time)

### pytest full suite: PASS
```
174 passed in 0.57s
```
### seal_check.py (mc-freeze 6-item): PASS
```
1. all four files decode (manifest parses as JSON): OK
2. unapproved placeholders: NONE
3. evidence refs: 34 used, unresolved: NONE
4. manifest vs registry hashes: 33 pages, mismatches: NONE
5. hash chain (immutable + FREEZE_LOG latest): ALL MATCH
6. status: spec NOT DRAFT / params NOT draft
SEAL_CHECK: PASS (ready for freeze approval)
```
### verify_freeze_hashes.py (s0-freeze): PASS
```
hashes found in FREEZE_LOG: 3
PROJECT_CHARTER.md: blob-vs-LOG=OK  blob-vs-worktree=OK
  5176320fb54a30e5e5dcc7f1ee96b828e7d38f727a573e8bd152ca3ff4299327
STUDY_0_PREREGISTRATION.md: blob-vs-LOG=OK  blob-vs-worktree=OK
  6cca20b7b1ce496d582ef5b4677333ba1b74bc577020ab29df00ff0c0d1af132
purchase_plan.yaml: blob-vs-LOG=OK  blob-vs-worktree=OK
  02edbc2cb8481089ecf7b30156fd86eb3cf524112e3f97d253f94acc60c39e6c
ALL_VERIFIED
```
### guards.verify_frozen_hashes(): PASS
```
7 canonical frozen hashes OK
```
### pyyaml structure assertion: PASS
```
platform_params.yaml structural parse OK, 10 top-level keys
```

-- end of addendum; awaiting Aaron's review. Real S0 stays locked. --