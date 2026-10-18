import os
os.environ["OMP_NUM_THREADS"] = "1" # khóa chuẩn OpenMP, chuẩn đa luồng C/C++ trong compiler GCC/Clang trên Linux Pi5
os.environ["OPENBLAS_NUM_THREADS"] = "1"# khóa chuẩn OPENBLAS - mặc định của numpy/spicy cho nhiều bản linux
os.environ["MKL_NUM_THREADS"] = "1"# chạy trên laptop intel
import pathlib # finding datasets directory
import hashlib


def preprocessings(path_string):
    folder = pathlib.Path(path_string) # return PosixPath if Linux OS otherwise, WindowsPath
    draft_scan = folder.rglob("*.wav") # * WildCard "wav" into characters - Generator type
    seen_hashes = dict()
    unique_files = []
    duplicate_files = []
    for single_scan in draft_scan:
        result = get_file_hash(single_path=single_scan)
        if result in seen_hashes.get():
            duplicate_files.append(result)
        else:
            unique_files.append(result)
    return unique_files, duplicate_files

    
def get_file_hash(single_path):
    with open(single_path, "rb") as file: # mở đường dẫn dưới dạng đọc
        contents = file.read() # đọc nội dung file
        hash_obj = hashlib.md5(contents) # giải nén thành file nhị phân, gồm 128 bits mã nhị phân
        result = hash_obj.hexdigest() # đổi 128-bits nhị phân thành chuỗi văn bản dài 32 ký tự
        return result
    