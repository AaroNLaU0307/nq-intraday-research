# SYMBOLOGY VERIFICATION (D5, Option A — official resolve)

- window: 2010-06-06 -> 2022-01-01 (excl), NQ.v.0, GLBX.MDP3;
  metadata endpoint, USD 0.00; raw responses + SHA-256 in raw/
- API fact: continuous->raw_symbol unsupported on GLBX.MDP3
  (HTTP 422); approved chain executed as two supported hops:
  continuous->instrument_id, then instrument_id->raw_symbol.
- mapping intervals: 48 (= 47 transitions + 1) — OK
- all intervals date-granular: True
- intra-RTH-session switch count: 0 (required: 0)
- quarterly contract cadence (NQ + H/M/U/Z): True
- 47/47 transition cross-check vs qa_addendum_a1.json: ALL MATCH

| boundary UTC | old id | new id | old ends | new starts | ok |
|---|---|---|---|---|---|
| 2010-06-14 | 6641 | 26715 | True | True | True |
| 2010-09-13 | 26715 | 3088 | True | True | True |
| 2010-12-13 | 3088 | 93735 | True | True | True |
| 2011-03-14 | 93735 | 30668 | True | True | True |
| 2011-06-13 | 30668 | 56972 | True | True | True |
| 2011-09-12 | 56972 | 12038 | True | True | True |
| 2011-12-12 | 12038 | 8870 | True | True | True |
| 2012-03-13 | 8870 | 20924 | True | True | True |
| 2012-06-11 | 20924 | 57494 | True | True | True |
| 2012-09-17 | 57494 | 10016 | True | True | True |
| 2012-12-17 | 10016 | 36931 | True | True | True |
| 2013-03-12 | 36931 | 11518 | True | True | True |
| 2013-06-17 | 11518 | 17591 | True | True | True |
| 2013-09-16 | 17591 | 28499 | True | True | True |
| 2013-12-16 | 28499 | 382251 | True | True | True |
| 2014-03-17 | 382251 | 8223 | True | True | True |
| 2014-06-16 | 8223 | 83745 | True | True | True |
| 2014-09-15 | 83745 | 28097 | True | True | True |
| 2014-12-15 | 28097 | 50207 | True | True | True |
| 2015-03-16 | 50207 | 58385 | True | True | True |
| 2015-06-15 | 58385 | 2913 | True | True | True |
| 2015-09-14 | 2913 | 12809 | True | True | True |
| 2015-12-14 | 12809 | 49734 | True | True | True |
| 2016-03-14 | 49734 | 765 | True | True | True |
| 2016-06-13 | 765 | 2563 | True | True | True |
| 2016-09-12 | 2563 | 2887 | True | True | True |
| 2016-12-13 | 2887 | 35888 | True | True | True |
| 2017-03-13 | 35888 | 6398 | True | True | True |
| 2017-06-12 | 6398 | 26054 | True | True | True |
| 2017-09-11 | 26054 | 15466 | True | True | True |
| 2017-12-11 | 15466 | 16210 | True | True | True |
| 2018-03-12 | 16210 | 23520 | True | True | True |
| 2018-06-11 | 23520 | 47511 | True | True | True |
| 2018-09-17 | 47511 | 16041 | True | True | True |
| 2018-12-17 | 16041 | 15657 | True | True | True |
| 2019-03-11 | 15657 | 9166 | True | True | True |
| 2019-06-19 | 9166 | 36742 | True | True | True |
| 2019-09-16 | 36742 | 15907 | True | True | True |
| 2019-12-16 | 15907 | 10204 | True | True | True |
| 2020-03-18 | 10204 | 16908 | True | True | True |
| 2020-06-17 | 16908 | 14028 | True | True | True |
| 2020-09-16 | 14028 | 16337 | True | True | True |
| 2020-12-16 | 16337 | 4378 | True | True | True |
| 2021-03-17 | 4378 | 2786 | True | True | True |
| 2021-06-16 | 2786 | 828 | True | True | True |
| 2021-09-15 | 828 | 2770 | True | True | True |
| 2021-12-13 | 2770 | 3541 | True | True | True |

Contract sequence: NQM0, NQU0, NQZ0, NQH1, NQM1, NQU1, NQZ1, NQH2, NQM2, NQU2, NQZ2, NQH3, NQM3, NQU3, NQZ3, NQH4, NQM4, NQU4, NQZ4, NQH5, NQM5, NQU5, NQZ5, NQH6, NQM6, NQU6, NQZ6, NQH7, NQM7, NQU7, NQZ7, NQH8, NQM8, NQU8, NQZ8, NQH9, NQM9, NQU9, NQZ9, NQH0, NQM0, NQU0, NQZ0, NQH1, NQM1, NQU1, NQZ1, NQH2

Scope (frozen by D5 approval): mapping is for VERIFICATION and
DISCLOSURE of F11/F5 roll identification only; it must never
change Primary results. Key was read from env only and never
persisted.