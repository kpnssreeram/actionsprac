import csv
import sys
from datetime import datetime

def extract_unique_queues(file_path):
    unique_queues = set()
    
    try:
        with open(file_path, 'r', newline='') as csvfile:
            csv_reader = csv.reader(csvfile)
            for row in csv_reader:
                if row:  # Check if the row is not empty
                    unique_queues.add(row[0])  # Add the first column value to the set
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
    except csv.Error as e:
        print(f"Error reading CSV file: {e}")
    except IndexError:
        print("Error: The CSV file appears to be empty or malformed.")
    
    return unique_queues

def main():
    if len(sys.argv) < 2:
        print("Usage: python script.py <csv_file1> <csv_file2> ...")
        return

    all_unique_queues = set()

    for file_path in sys.argv[1:]:
        file_queues = extract_unique_queues(file_path)
        all_unique_queues.update(file_queues)

    # Generate a timestamp for the output file name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"unique_queues_{timestamp}.csv"

    # Write unique queue names to the output CSV file
    try:
        with open(output_file, 'w', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(["Queue Name"])  # Write header
            for queue in sorted(all_unique_queues):
                csv_writer.writerow([queue])
        print(f"Unique queue names have been saved to {output_file}")
    except IOError as e:
        print(f"Error writing to CSV file: {e}")

if __name__ == "__main__":
    main()