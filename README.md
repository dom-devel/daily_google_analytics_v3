# Google Analytics to CSV

This command line tool allows you to query the Google Api saving the data to csv.

## Getting started

`git clone git@github.com:DistilledLtd/google_analytics_to_csv.git`

Ideally within a virtual env run the following

`pip install -r requirements.txt`


## Usage

`python download_ga_data.py settings.yml`

You can optionally pass a start_date and / or end_date (both in YYYYMMDD format). If not they both default to yesterday.

e.g. 

`python download_ga_data.py settings.yml -s 20160701`

`python download_ga_data.py settings.yml -e 20160720`

## settings.yml

Pass a path to a yml settings file. It should be of the following format

```
---
account_id: "1618063"
web_property_id: "UA-1618063-1"
view_id: "2901806"
query_params:
  metrics: "ga:entrances"
  dimensions: "ga:pagePathLevel1,ga:hostname"
  filters: "ga:medium==organic;ga:entrances>99"
  samplingLevel: "HIGHER_PRECISION"
  max_results: 10000
csv_file:
  filename: "distilled_{st}_{ed}.csv"
  directory: "/tmp"
```

NB `{st}` and `{ed}` in the csv filename will get converted to the start_date and end_date respectively.
