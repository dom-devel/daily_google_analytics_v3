# Google Analytics to DF/CSV

This is a module that allows you to download daily GA data.

What to use this for?

I've primarily used this for analysis within Jupyter Notebooks. I've found it very useful for short analyses involving GA data.

I wouldn't recommend using in production. The original version was created by [Duncan Morris](https://github.com/duncanmorris) was a nice elegant CLI script.

This is a heavily bastardised version which I cobbled together several years ago to fit my workflows, while I was learning python.

## Getting started

You can either install straight from pip:

`pip install daily-google-analytics-to-df-or-csv`

Or you can clone and run

`pipenv install`

## Usage

```
import download_ga_data

{
    "start_date": "YYYY-0-01",
    "end_date": "2019-01-02",
    "total_results_per_day": "{The maximum number of results to accept per day}",
    "query_params": {
        "metrics": "ga:sessions",
        "dimensions": "ga:landingPagePath",
    },
    "account_id": "{ga-account-id}",
    "web_property_id": "{ga-property-id}",
    "view_id": "{ga-view-id}",
    "auth_type": "service" OR "oauth_client"
    "auth_file": "{location of the google API credentials file}",
}
```
