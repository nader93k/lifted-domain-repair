import sys

def sort_lines(input_path, output_path):
    try:
        # Read the input file
        with open(input_path, 'r') as file:
            lines = file.readlines()

        # Strip newline characters and sort lines
        lines = [line.strip() for line in lines]
        lines.sort()

        # Prepare the sorted lines with two empty lines between each
        output_lines = []
        for line in lines:
            output_lines.append(line)
            output_lines.append('\n')
            output_lines.append('\n')

        # Write the output file
        with open(output_path, 'w') as file:
            file.writelines(output_lines)

        print(f"File sorted and written to {output_path} successfully.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script.py <input_path> <output_path>")
    else:
        input_path = sys.argv[1]
        output_path = sys.argv[2]
        sort_lines(input_path, output_path)
