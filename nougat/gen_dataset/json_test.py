import json


# write json file
def write_json_file(file_path, data):
    with open(file_path, "w") as f:
        json.dump(data, f)


# read json file
def read_json_file(file_path):
    with open(file_path, "r") as f:
        return json.load(f)


def main():
    # write json file
    write_json_file("data.json", {"name": "John", "age": 30, "city": "New York"})

    # read json file
    data = read_json_file("data.json")
    print(data)


if __name__ == "__main__":
    main()
