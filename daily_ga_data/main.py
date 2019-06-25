import datetime
import pandas as pd
import logging
import argparse

from analytics.google import GoogleAnalytics

# from analytics.google import GoogleAnalytics

# Silence the file cache unavailable error - https://github.com/google/google-api-python-client/issues/299
logging.getLogger("googleapiclient.discovery").setLevel(logging.CRITICAL)
logger = logging.getLogger(__name__)

QUERY_REQUIRES = [
    "account_id",
    "web_property_id",
    "view_id",
    "query_params",
    "start_date",
    "end_date",
    "total_results_per_day",
]

QUERY_PARAMS_REQUIRED = {"metrics", "dimensions"}


def convert_to_date(datestring):
    try:
        return datetime.datetime.strptime(datestring, "%Y%-m-%d").date()
    except ValueError:
        raise argparse.ArgumentTypeError("Incorrect date format, should be YYYY-MM-DD")


def get_arguments():
    """ Take input arguments. Allows for easy conversion to Gooey.
    """
    parser = argparse.ArgumentParser(description="Download GA data to a CSV file")
    parser.add_argument(
        "account_id", help="The account id of the Google Analytics account."
    )
    parser.add_argument(
        "web_property_id", help="The property id of the Google Analytics account."
    )
    parser.add_argument("view_id", help="The view id of the Google Analytics account.")
    parser.add_argument(
        "credentials", help="The file path to credentials.", default="credentials.json"
    )
    parser.add_argument(
        "total_results_per_day", help="The maximum number of results returned from GA."
    )
    parser.add_argument(
        "start_date",
        "-s",
        dest="start_date",
        type=convert_to_date,
        default=datetime.date.today() - datetime.timedelta(days=1),
        help="Earliest date (YYYY-MM-DD) to pull data from GA.",
    )
    parser.add_argument(
        "end_date",
        "-e",
        dest="end_date",
        type=convert_to_date,
        default=datetime.date.today() - datetime.timedelta(days=1),
        help="Latest date (YYYY-MM-DD) to pull data from GA.",
    )

    # Add in query information
    subparser = parser.add_subparsers()
    query_params = subparser.add_parser("add")

    query_params.add_argument(
        "dimensions", help="A list of comma separated dimensions."
    )
    query_params.add_argument("metrics", help="A list of comma separated metrics.")
    query_params.add_argument(
        "--sort",
        "st",
        help=(
            "A comma separated list of metrics and dimensions"
            "indicating the sorting order."
        ),
    )
    query_params.add_argument(
        "--filters",
        "ft",
        help=("A Google analytics valid filter string (see v3 reference guide)."),
    )
    query_params.add_argument(
        "--segments",
        "sg",
        help=("A Google analytics valid segments string (see v3 reference guide)."),
    )

    args = parser.parse_args()
    settings = {}

    # convert argparse to dict
    for arg in vars(args):
        if arg not in settings:
            settings[arg] = getattr(args, arg)

    return settings


def validate_google_query_dict(params):
    """ Validates the shape of the dictionary given and calls out any issues.
    """
    valid = True
    for key in QUERY_REQUIRES:
        if key not in params:
            print("The general params needs to include {}".format(key))
            valid = False
    try:
        for key in QUERY_PARAMS_REQUIRED:
            if key not in params["query_params"]:
                print("The google specific params needs to include {}".format(key))
                valid = False
    except Exception as e:
        pass

    return valid


def convert_to_date(datestring):
    """ Attempts to convert a date string into a python datetime object.
    """
    try:
        return datetime.datetime.strptime(datestring, "%Y-%m-%d").date()
    except ValueError:
        raise TypeError("Incorrect date format, should be YYYY-MM-DD")
    except TypeError:
        raise TypeError(
            "This error will appear if you haven't set your date as string (i.e. put \
            it in quotes)."
        )


def download_v3(google_analytics_query_params):
    """ Returns either a CSV or dataframe containing GA data day by day
    to minimize the chance of sampling.

    Requires a dictionary containing:
    account_id: The account id of the Google Analytics account.
    web_property_id: The property id of the Google Analytics account.
    view_id: The view id of the Google Analytics account.
    max_results: The maximum number of results returned from GA.
    start_date: Earliest date (YYYY-MM-DD) to pull data from GA.
    end_date: Latest date (YYYY-MM-DD) to pull data from GA.
    auth_type: The type of authentication key: 'oauth_client' or 'service'.
    auth_file: Location of the authentication file.
    query_params: In here needs to be GA query parameters
                  https://developers.google.com/analytics/devguides/reporting/core/v3/reference
        metrics: Required
        dimensions: Required

        Filters & Sorts have been tested, everything else should work in theory
        but hasn't been extensively tested.
    """
    if validate_google_query_dict(google_analytics_query_params) is False:
        return "You need a fully featured dictionary."

    settings = google_analytics_query_params

    if "to_csv" not in settings:
        settings["to_csv"] = False

    if "auth_type" not in settings:
        settings["auth_type"] = "oauth_client"

    if "auth_file" not in settings:
        settings["auth_file"] = "credentials.json"

    if "allow_sampled" not in settings:
        settings["allow_sampled"] = False

    if "total_results_per_day" not in settings:
        settings["total_results_per_day"] = False

    if "pagination_size" not in settings:
        settings["pagination_size"] = 10000

    settings["start_date"] = convert_to_date(settings["start_date"])
    settings["end_date"] = convert_to_date(settings["end_date"])
    delta = settings["end_date"] - settings["start_date"]

    if delta.days < 0:
        return "Your end date must be after the start date."

    ga = GoogleAnalytics(
        settings["account_id"],
        settings["web_property_id"],
        settings["view_id"],
        settings["auth_type"],
        settings["auth_file"],
        settings["total_results_per_day"],
        settings["allow_sampled"],
    )

    df_list = []

    for i in range(delta.days + 1):
        date_to_query = settings["start_date"] + datetime.timedelta(days=i)

        logger.info("Querying {dt}".format(dt=date_to_query))

        query_params = settings.get("query_params", {})
        query_params["start_date"] = date_to_query
        query_params["end_date"] = date_to_query
        query_params["start_index"] = 1

        prepared_query_params = ga.prepare_query(**query_params)
        data = ga.query(prepared_query_params, settings["pagination_size"])

        df = pd.DataFrame(data["data"], columns=data["columns"], dtype="int")
        df["date"] = date_to_query
        df_list.append(df)

    joined_df = pd.concat(df_list, axis=0, ignore_index=True)

    if settings["to_csv"]:
        joined_df.to_csv("", encoding="utf-8")
    else:
        return joined_df


if __name__ == "__main__":
    get_arguments()
    download_v3()
