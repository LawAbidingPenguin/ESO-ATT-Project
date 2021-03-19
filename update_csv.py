from csv_data import get_csv


if __name__ == '__main__':

    with open('test_file.csv', 'w') as f:
        f.write(get_csv())