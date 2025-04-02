import json
import subprocess

from select_files import is_zip_wanted, find_all_zips
from create_data import walk_and_create
from concurrent.futures import ThreadPoolExecutor, as_completed


latex_pdf_root = "/data1/nzw/latex_pdf/"
target_json_file = "/home/ninziwei/lyj/nougat/gen_dataset/data.json"
required_size = 10000  # The number of files to generate
generated_size = 0


def write_json(zip_files, size=10):
    zips = []
    for zip_file in zip_files:
        try:
            if is_zip_wanted(zip_file):
                zips.append(zip_file)
                print(f"select files: {len(zips)}/{size}")
                if len(zips) >= size:
                    break
        except Exception as e:
            print(f"select files failed: {e}")
            continue

    data = {"zip_files": zips}
    with open(target_json_file, "w") as f:
        json.dump(data, f)


def process_zip_file(zip_file):
    global generated_size
    try:
        if walk_and_create(zip_file):
            generated_size += 1
            with open("success.txt", "a") as f:
                f.write(zip_file + "\n")

            print(f"create data: {generated_size}/{required_size}")
            if generated_size >= required_size:
                return True

    except Exception as e:
        print(f"create data failed: {e}")
    return False


def main():
    # select zip files and write to json
    # zip_files = find_all_zips(latex_pdf_root)
    # write_json(zip_files, size=15000)
    # print("select files done!")

    # process zip files
    with open(target_json_file, "r") as f:
        data = json.load(f)
        zip_files = data["zip_files"]

        batch_size = 100

        with ThreadPoolExecutor(max_workers=20) as executor:
            for i in range(0, len(zip_files), batch_size):
                subprocess.run("rm *.log", shell=True)

                if generated_size >= required_size:
                    break

                batch = zip_files[i : i + batch_size]

                results = executor.map(process_zip_file, batch)

                try:
                    if any(results):
                        break
                except Exception as e:
                    print(f"Error processing batch: {e}")

                print(
                    f"Processed batch {i//batch_size + 1}, total generated: {generated_size}/{required_size}"
                )

    print("create data done!")


if __name__ == "__main__":
    main()
