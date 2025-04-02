import json
import subprocess
import threading
from select_files import is_zip_wanted, find_all_zips
from create_data import walk_and_create
from concurrent.futures import ThreadPoolExecutor, as_completed


latex_pdf_root = "/data1/nzw/latex_pdf/"
target_json_file = "/home/ninziwei/lyj/nougat/gen_dataset/data.json"
required_size = 10000  # The number of files to generate
generated_size = 0
# 添加锁以保护全局变量
size_lock = threading.Lock()
# 添加一个事件标志来指示是否已完成工作
done_event = threading.Event()


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
    
    # 如果已完成，直接返回
    if done_event.is_set():
        return False
        
    try:
        if walk_and_create(zip_file):
            # 使用锁保护对共享变量的修改
            with size_lock:
                generated_size += 1
                current_size = generated_size  # 在锁内获取当前值
                
                with open("success.txt", "a") as f:
                    f.write(zip_file + "\n")
                
                print(f"create data: {current_size}/{required_size}")
                
                # 检查是否达到目标
                if current_size >= required_size:
                    done_event.set()  # 设置事件标志
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
        
        # 减少工作线程数量
        with ThreadPoolExecutor(max_workers=10) as executor:
            for i in range(0, len(zip_files), batch_size):
                subprocess.run("rm *.log", shell=True)

                if generated_size >= required_size or done_event.is_set():
                    break

                batch = zip_files[i : i + batch_size]
                
                # 使用as_completed而不是map来更好地控制任务
                futures = [executor.submit(process_zip_file, zip_file) for zip_file in batch]
                
                for future in as_completed(futures):
                    try:
                        if future.result():
                            # 如果任何任务返回True，表示已达到目标
                            break
                    except Exception as e:
                        print(f"任务执行出错: {e}")
                    
                    # 检查是否已达到目标
                    if done_event.is_set():
                        break
                
                # 如果已达到目标，跳出循环
                if done_event.is_set():
                    print("已达到目标数量，终止处理")
                    break

                print(
                    f"Processed batch {i//batch_size + 1}, total generated: {generated_size}/{required_size}"
                )

    print("create data done!")


if __name__ == "__main__":
    main()
