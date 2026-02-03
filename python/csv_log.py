import csv
from datetime import datetime

class CSVLogger:
    def __init__(self, col_names, csv_file='log.csv'):
        self.csv_file = csv_file
        col_names.insert(0, "Timestamp")
        # Create the CSV file and write the header if it doesn't exist
        with open(self.csv_file, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(col_names)

    def write(self, data):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        with open(self.csv_file, mode='a', newline='') as file:
            writer = csv.writer(file)
            row = [timestamp] + data
            writer.writerow(row)

# Example usage
if __name__ == "__main__":
    logger = CSVLogger()
    logger.write('Device1', '123', 'Sample data')
    logger.write('Device2', '456', 'More sample data')