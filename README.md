# Google Analytics to DF/CSV

This is a module that allows you to download daily GA data.

What to use this for?

I've primarily used this for analysis within Jupyter Notebooks. I've found it very useful for short analyses involving GA data.

I wouldn't recommend using in production. The original version was created by [Duncan Morris](https://github.com/duncanmorris) was a nice elegant CLI script.

This is a heavily bastardised version which I cobbled together several years ago to fit my workflows, while I was learning python.

It's a big hot mess, but it is quite useful for ad-hoc analysis.

## Getting started

You can either install straight from pip:

`pip install daily-google-analytics-to-df-or-csv`

Or you can clone and run

`pipenv install`

## Usage

```
import daily_ga_data

// These are the minimum required fields

daily_ga_data.download_v3({
    "start_date": "YYYY-MM-DD",
    "end_date": "YYYY-MM-DD",
    "query_params": {
        "metrics": "{valid-ga-metric}",
        "dimensions": "{valid-ga-dimension}",
    },
    "account_id": "{ga-account-id}",
    "web_property_id": "{ga-property-id}",
    "view_id": "{ga-view-id}",
    "auth_type": "service" OR "oauth_client"
    "auth_file": "{location of the google API credentials file}",
})

// Here is an example minimum viable query for you to get started with

daily_ga_data.download_v3({
    "account_id": "XXXXXX",
    "web_property_id": "UA-XXXXXXX-X",
    "view_id": "XXXXXXX",
    "start_date": "2019-01-01",
    "end_date": "2019-01-02",
    "auth_type": "service",
    "auth_file": "{location-of-credentials}",
    "query_params": {
        "metrics": "ga:sessions",
        "dimensions": "ga:landingPagePath",
    },
})
```
