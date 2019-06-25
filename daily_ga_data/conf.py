import argparse
import datetime
import yaml


def convert_to_date(datestring):
    try:
        return datetime.datetime.strptime(datestring, '%Y-%m-%d').date()
    except ValueError:
        raise argparse.ArgumentTypeError("Incorrect date format, should be YYYY-MM-DD")


def main(yaml_Location):
    parser = argparse.ArgumentParser(description='Download GA data to a CSV file')
    # parser.add_argument('settings',
    #                     help="Settings file containing required meta info")

    parser.add_argument('--startdate', '-s',
                        dest='start_date',
                        type=convert_to_date,
                        default=datetime.date.today() - datetime.timedelta(days=1),
                        help="Earliest date (YYYY-MM-DD) to pull data from GA.")
    parser.add_argument('--enddate', '-e',
                        dest='end_date',
                        type=convert_to_date,
                        default=datetime.date.today() - datetime.timedelta(days=1),
                        help="Latest date (YYYY-MM-DD) to pull data from GA.")
    parser.add_argument('--aggregation', '-agg',
                        dest='aggregation',
                        type=bool,
                        default=False,
                        help="Do you want to aggregate the days based on a single dimension (to get unsampled aggregation)?")
    parser.add_argument('--filename', '-fn',
                        dest='filename',
                        type=str,
                        default='distilled_{st}_{ed}.csv',
                        help="The filename of the file being created")
    parser.add_argument('--directory', '-dir',
                        dest='directory',
                        type=str,
                        default='.',
                        help="The directory to save the file to.")
    parser.add_argument('--limit', '-lim',
                        dest='limit',
                        type=int,
                        default='200',
                        help="The number of results to return (will be rounded to 200).")

    args = parser.parse_args()

    with open(yaml_Location) as yaml_file:
        settings = yaml.load(yaml_file)

    for arg in vars(args):
        if arg not in settings:
            settings[arg] = getattr(args, arg)

    return settings

if __name__ == '__main__':
    main()