import datetime
import time
import json
import sys
import os
import webbrowser
import logging
import inspect

from httplib2 import Http

from apiclient.discovery import build
from apiclient.errors import HttpError

from oauth2client.file import Storage
from oauth2client.client import flow_from_clientsecrets
from oauth2client.service_account import ServiceAccountCredentials

# Add parent folder to path so we can import definitions
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

import analytics.definitions as definitions

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
PARENT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, os.pardir))
WEBMASTER_CREDENTIALS_FILE_PATH = os.path.join(PARENT_DIR, "webmaster_credentials.dat")

logger = logging.getLogger(__name__)
# Suppress lack of file cache in later oauth versions
# https://github.com/google/google-api-python-client/issues/299
logging.getLogger("googleapiclient.discovery_cache").setLevel(logging.ERROR)


def acquire_new_oauth2_credentials(secrets_file):
    """
    secrets_file: A JSON file containing:
        client_id
        client_secret
        redirect_uris
        auth_uri
        token_uri
    returns:
        credentials for use with Google APIs
    """
    flow = flow_from_clientsecrets(
        secrets_file,
        scope="https://www.googleapis.com/auth/analytics.readonly",
        redirect_uri="urn:ietf:wg:oauth:2.0:oob",
    )
    auth_uri = flow.step1_get_authorize_url()
    webbrowser.open(auth_uri)
    print("Please enter the following URL in a browser " + auth_uri)
    auth_code = input("Enter the authentication code: ")
    credentials = flow.step2_exchange(auth_code)
    return credentials


def load_oauth2_credentials(secrets_file):
    """
    Looks for a credentials file first.
    If one does not exist, calls a function to acquire and save new credentials.
    """
    storage = Storage(WEBMASTER_CREDENTIALS_FILE_PATH)
    credentials = storage.get()

    if credentials is None or credentials.invalid:
        credentials = acquire_new_oauth2_credentials(secrets_file)
    storage.put(credentials)
    return credentials


class GoogleAnalyticsProfile(object):
    """A simple object to store account_id, web_property_id and view_id
    """

    _account_id = None
    _web_property_id = None
    _view_id = None

    def __init__(self, account_id, web_property_id, view_id, auth_type, auth_file):
        self._account_id = account_id
        self._web_property_id = web_property_id
        self._view_id = view_id
        self.auth_file = auth_file

        try:
            open(self.auth_file, "r")
        except IOError:
            raise Exception(
                "You need to specify the location of your GA API credentials with 'auth_file'. "
                "If that didn't make sense please see https://www.domwoodman.com/posts/how-to-get-unsampled-google-analytics-data"
            )

        if auth_type is "oauth_client":
            self.service = self._get_oauth_service()
        elif auth_type is "service":
            self.service = self._get_serviceacc_service()

    @property
    def view_id(self):
        return self._view_id

    def _get_oauth_service(self):
        # scopes = ['https://www.googleapis.com/auth/analytics.readonly']

        http_auth = Http()
        credentials = load_oauth2_credentials(self.auth_file)
        http_auth = credentials.authorize(http_auth)
        service = build("analytics", "v3", http=http_auth)

        return service

    def _get_serviceacc_service(self):
        scopes = ["https://www.googleapis.com/auth/analytics.readonly"]
        credentials_path = os.path.join(self.auth_file)
        credentials = ServiceAccountCredentials.from_json_keyfile_name(
            credentials_path, scopes
        )
        delegated_credentials = credentials.create_delegated(
            "analytics@distilled.co.uk"
        )
        http_auth = delegated_credentials.authorize(Http())
        service = build("analytics", "v3", http=http_auth, cache_discovery=False)
        return service

    def get_view_info(self):
        view_info = (
            self.service.management()
            .profiles()
            .get(
                accountId=self._account_id,
                webPropertyId=self._web_property_id,
                profileId=self._view_id,
            )
            .execute()
        )

        return view_info

    def day_finished(self, date):
        """Based on the timezone stored with the profile has the given date ended"""
        # NBED Needs work!
        return date < datetime.date.today()

    def __repr__(self):
        return "<Profile: {account_id} {web_property_id} {view_id}>".format(
            account_id=self.account_id,
            web_property_id=self.web_property_id,
            view_id=self.view_id,
        )


class GoogleAnalytics(object):
    num_failed_requests = 0

    def __init__(
        self,
        account_id,
        web_property_id,
        view_id,
        auth_type,
        auth_file,
        limit,
        allow_sampled,
    ):

        self.ga_profile = GoogleAnalyticsProfile(
            account_id, web_property_id, view_id, auth_type, auth_file
        )
        self.limit = limit
        self.allow_sampled = allow_sampled

        if auth_type is "oauth_client":
            self.service = self.ga_profile._get_oauth_service()
        elif auth_type is "service":
            self.service = self.ga_profile._get_serviceacc_service()

    def _retry_request(self, reason, prepared_query_params, retry_count):
        """ This method re-runs the last request if it fails for any reason
        """
        retry_count += 1
        logger.warning(
            "\tWARNING: {r}. Backing off. There have been {i} failed requests.".format(
                r=reason, i=GoogleAnalytics.num_failed_requests
            )
        )

        sleep_for = 3 * retry_count
        logger.warning("\t\tSleeping for {s}".format(i=sleep_for))
        time.sleep(sleep_for)

        return self._query(prepared_query_params, retry_count=retry_count)

    def prepare_query(self, **kwargs):
        """ This function prepares the query params to be run.
        """
        query_params = {
            "ids": "ga:" + self.ga_profile.view_id,
            "start_date": datetime.date.today() - datetime.timedelta(days=1),
            "end_date": datetime.date.today() - datetime.timedelta(days=1),
            "samplingLevel": "HIGHER_PRECISION",
            "quotaUser": "quota{vid}".format(vid=self.ga_profile.view_id),
        }

        for key, value in kwargs.items():
            if value:
                if key in definitions.MAP_API_TO_REF:
                    query_params[definitions.MAP_API_TO_REF[key]] = value
                else:
                    query_params[key] = value

        query_params["start_date"] = query_params["start_date"].strftime("%Y-%m-%d")
        query_params["end_date"] = query_params["end_date"].strftime("%Y-%m-%d")

        return query_params

    def query(self, prepared_query_params, pagination_size, retry_count=0):
        """Query GA api for session data.

            This is expecting a fully featured query dictionary
            provided (see README for format). If one isn't then a default
            query for landingPagePath, date and sessions will be run.

            This will paginate through the API and return the number of results
            provided in max_results_at_end, rounded to the nearest 10k.

            Returns: A results dictionary with 'data' containing the data in a 
            list of dictionaries and columns returning the column headers.
        """
        results_dict = {}
        data_array = []
        if "start_index" not in prepared_query_params:
            prepared_query_params["start_index"] = 0

        if retry_count > 4:
            logger.error(
                "This query has failed more than 4 times and so has been skipped."
            )
            return results_dict

        # Max results is essentially the pagination size.
        prepared_query_params["max_results"] = pagination_size

        # Paginate through results until no more results can be found
        # or limit is reached
        has_more = True
        while has_more:
            try:
                results = (
                    self.service.data().ga().get(**prepared_query_params).execute()
                )

            except HttpError as error:
                details = json.loads(error.content.decode("utf-8"))

                code = details["error"]["code"]
                message = details["error"]["message"]

                if code == 403 and message == "User Rate Limit Exceeded":
                    self._retry_request(
                        "rate limiting", prepared_query_params, retry_count
                    )
                elif (
                    code == 403
                    and message
                    == "User does not have sufficient permissions for this profile."
                ):
                    full_account = [
                        self.ga_profile._account_id,
                        self.ga_profile._web_property_id,
                        self.ga_profile.view_id,
                    ]
                    permissions_error = "You don't have permissions to access {0}".format(
                        ".".join(full_account)
                    )
                    logger.error(permissions_error)
                    return None
                elif code == 400:
                    error_msg = "The GA request created from the configuration is bad: {0}: {1}".format(
                        code, message
                    )
                    logger.error(error_msg)
                    return None
                else:
                    logger.error(
                        "These are the query params {}".format(self.query_params)
                    )
                    logger.error("FATAL: {c}: {m}".format(c=code, m=message))
                    sys.exit(1)
            except BrokenPipeError as error:
                self._retry_request("broken pipe", prepared_query_params, retry_count)

            result_count = (
                prepared_query_params["start_index"]
                + prepared_query_params["max_results"]
            )
            logger.info(
                "Getting {start_index} to {end_index} of {total_results} results.".format(
                    total_results=results.get("totalResults"),
                    start_index=prepared_query_params["start_index"],
                    end_index=result_count,
                )
            )

            if results["containsSampledData"] and not self.allow_sampled:
                logger.error("FATAL: Query was sampled, and allow_sampled was False")
                sys.exit(1)

            if not self.limit:
                self.limit = 1000000000000

            if result_count < self.limit:
                if results.get("nextLink"):
                    prepared_query_params["start_index"] = (
                        prepared_query_params["start_index"]
                        + prepared_query_params["max_results"]
                    )
                else:
                    has_more = False
            else:
                has_more = False

            if "columns" not in results_dict:
                results_dict["columns"] = [
                    c.get("name") for c in results.get("columnHeaders")
                ]
            data_array.extend(results.get("rows", []))

        results_dict["data"] = data_array

        return results_dict
