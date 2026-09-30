# Outbound enquiry — ETF Global (ETFG)

```
STATUS  = READY_NOT_SENT
PREPARED = 2026-09-20
```

**NOT SENT.** Copy the message below as-is. Do not add context about the research
question, the mechanism, or any internal naming.

## Contact route

```
Contact form at etfg.com · phone +1 (212) 223-3834 (New York HQ).
CONTACT_TYPE = WEB_FORM (phone as fallback).
A department-specific address is not publicly confirmed; the published
email format is [first-initial][last]@etfg.com.
```

## Subject

```
Historical point-in-time ETF fund-size data enquiry
```

## Message

---

Hello,

I am conducting academic / research work on historical point-in-time ETF
fund-size data, and I am evaluating which sources can establish not only what a fund's
size was on a historical date, but **what value was actually available, and when**.

The funds I need are five US-listed ProShares Nasdaq-100 ETFs — **QLD, QID, PSQ, TQQQ,
SQQQ** — over approximately **2010-06-06 to 2021-12-31**.

1. Do you provide daily historical Total Net Assets / AUM, or daily NAV plus
   contemporaneous **unadjusted** shares outstanding, for these five ETFs back to their
   respective inception dates?
2. Are the historical records **original vintage**, or retrospectively revised / restated?
3. Do you retain the historical timestamp at which each daily value was received, loaded,
   published, or first made available to users?
4. Is that timestamp **date only**, or date plus intraday time plus timezone?
5. Can historical data be queried **"as known at timestamp X"**, or through immutable
   historical snapshots / vintages?
6. Could you provide a small verification sample for **2016-03-31, 2016-04-01, 2016-04-04
   and 2016-04-05** for the five ETFs, including: value date; fund-size value (or NAV plus
   unadjusted shares outstanding); first receipt / load / publication timestamp; timezone;
   and a revision or vintage identifier if one exists?
7. Are delisted ETFs preserved historically?
8. Which stable identifiers are included — CUSIP, ISIN, SEDOL, SEC Series ID, an internal
   permanent ID?
9. What is the earliest historical coverage date?
10. What delivery formats exist — API, bulk files, terminal export, cloud dataset, SFTP?
11. What academic or research licence options exist?
12. What pricing applies for only the historical dataset described above?

Four questions specific to your documented schema:

13. Your fund-flow records carry both `effective_date` and `processed_date`, the latter
    documented as the date ETF Global received and processed the data. For a **historical**
    row, is the stored `processed_date` the date you **originally** received that value, or
    is it updated if the value is later corrected or reloaded?
14. Is an **intraday** processing or receipt timestamp held internally, even if the
    published field is date-only?
15. When a value is corrected, is the **previous record version retained**, or replaced?
16. The redistributed history begins **2017-04-03**. Does coverage before that date exist
    in another product or archive — and if so, do those earlier records carry a genuine
    `processed_date`, or were they constructed retrospectively?

Thank you for your help.

Best regards,
[name]
[affiliation, if any]

---
