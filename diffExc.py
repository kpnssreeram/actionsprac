import csv
from datetime import datetime

def read_first_column(file_path):
    data = set()
    try:
        with open(file_path, 'r', newline='') as csvfile:
            csv_reader = csv.reader(csvfile)
            for row in csv_reader:
                if row:  # Check if the row is not empty
                    data.add(row[0])  # Add the first column value to the set
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
    except csv.Error as e:
        print(f"Error reading CSV file: {e}")
    return data

def main():
    # Hardcoding file names for simplicity, but you can modify to accept command-line arguments
    file1_path = 'Review.csv'
    file2_path = '6e47647b-55c6-4c59-9577-37e19fa55440.csv'

    # Read data from both files
    data1 = read_first_column(file1_path)
    data2 = read_first_column(file2_path)

    # Find symmetric difference
    unique_data = data1.symmetric_difference(data2)

    # Generate a timestamp for the output file name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"unique_entries_{timestamp}.csv"

    # Write unique entries to the output CSV file
    try:
        with open(output_file, 'w', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(["Unique Entries"])  # Write header
            for entry in sorted(unique_data):
                csv_writer.writerow([entry])
        print(f"Unique entries have been saved to {output_file}")
    except IOError as e:
        print(f"Error writing to CSV file: {e}")

if __name__ == "__main__":
    main()