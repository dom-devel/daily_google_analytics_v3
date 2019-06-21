from distutils.core import setup

setup(
    name="daily-google-analytics-to-df-or-csv",
    packages=["daily-google-analytics-to-df-or-csv"],
    version="0.1",
    license="MIT",
    description="A library for downloading daily GA data to a pandas dataframe or CSV using v3 of the API.",
    author="Dominic Woodman",
    author_email="domwoodman@gmail.com",
    url="https://github.com/dom-devel/daily_google_analytics_to_df_or_csv",
    include_package_data=True,
    download_url="https://github.com/user/reponame/archive/v_01.tar.gz",
    keywords=["google analytics", "pandas"],
    install_requires=["pandas", "httplib2", "google-api-python-client", "oauth2client"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
    ],
)
