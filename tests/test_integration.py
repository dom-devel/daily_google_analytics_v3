import unittest
from download_ga_data import main
import local_vars


class FullRunTests(unittest.TestCase):
    def setUp(self):
        query_details = {
            "start_date": "2019-01-01",
            "end_date": "2019-01-02",
            "auth_type": "service",
            "total_results_per_day": False,
            "pagination_size": 10000,
            "query_params": {
                "metrics": "ga:sessions",
                "dimensions": "ga:landingPagePath",
                "max_results": 10000,
            },
        }

        base_dict = {**local_vars.ga_data2, **query_details}

        self.base_dict = base_dict

    def test_service_auth_full_run_return_df(self):
        self.base_dict["auth_file"] = r"credentials/credentials.json"
        df = main(self.base_dict)

        # print(df.shape)
        # print(df)

    # def test_service_auth_full_run_return_df(self):
    #     self.base_dict["auth_type"] = r"oauth_client"
    #     df = main(self.base_dict)

    # self.assertEqual(error, "You need a fully featured dictionary.")

    # def test_service_auth_full_run_return_df(self):
    #     error = main(self.base_dict)

    #     self.assertEqual(error, "You need a fully featured dictionary.")


if __name__ == "__main__":
    unittest.main()
