import os # setting environment and multiprocessing
os.environ["OMP_NUM_THREADS"] = "1" # khóa chuẩn OpenMP, chuẩn đa luồng C/C++ trong compiler GCC/Clang trên Linux Pi5
os.environ["OPENBLAS_NUM_THREADS"] = "1"# khóa chuẩn OPENBLAS - mặc định của numpy/spicy cho nhiều bản linux
os.environ["MKL_NUM_THREADS"] = "1"# chạy trên laptop intel
import pathlib # finding datasets directory
import hashlib # using hash alrogithm
from joblib import Parallel, delayed
import librosa # active multiTask
import numpy as np
import imageio_ffmpeg
VALID_FILETYPE = {".wav", ".mp3", ".mp4", ".mp4a", ".flac", ".ogg", ".m4a"}

def preprocessings(path_string):
    folder = pathlib.Path(path_string) # always return PosixPath if Linux .Otherwise, WindowsPath
    valid_path = [i for i in folder.rglob("*") if i.is_file() and i.suffix.lower() in VALID_FILETYPE] # check whether folder.rglob() is a valid file type or not
    seen_hashes = dict()
    unique_files = dict()
    duplicate_files = dict()
    result = Parallel(n_jobs= -1, verbose=10)(delayed(get_file_hash)(single_path) for single_path in valid_path)
    for single_scan,md5 in zip(valid_path,result):
        if md5 in seen_hashes:
            duplicate_files[single_scan] = md5 # lấy đường dẫn làm key (vì key là unique, path cũng unique)
        else:
            unique_files[single_scan] = md5 
            seen_hashes[md5] = single_scan # lấy md5 làm seen để so sánh, vì khi băm, các file giống nhau có có xu bits giống nhau
    return unique_files, duplicate_files

def get_file_hash(single_path):
    with open(single_path, "rb") as file: # mở đường dẫn dưới dạng đọc
            contents = file.read() # đọc nội dung file
            hash_obj = hashlib.md5(contents) # nén một chiều (tức băm) ra từ triệu bytes sang 128 bits
            result = hash_obj.hexdigest() # đổi 128-bits nhị phân thành chuỗi văn bản dài 32 ký tự
    return result
# process raw audio and convert to 16KHz
def inspect_audio_signal(single_path):
    try:
        single_path = str(single_path)
        y, sr = librosa.load(single_path, sr=16000, mono=True)
        duration = len(y) / sr
        rms = np.sqrt(np.mean(y ** 2) + 1e-8)
        dbfs = 20.0 * np.log10(rms)
        clip_ratio = np.mean(np.abs(y) >= 0.99)
        frame_rms = librosa.feature.rms(y=y, frame_length=512, hop_length=256)[0]
        snr_db = 20.0 * np.log10((np.percentile(frame_rms, 90) + 1e-8) / (np.percentile(frame_rms, 10) + 1e-8))
    except Exception as e:
        print(f"Error: ", e)


if __name__ == "__main__":
    unique_file, duplicate_file = preprocessings("data/01_audio_cry_sample")
    draft_result = Parallel(n_jobs=-1, verbose=5)(delayed(inspect_audio_signal)(every_file) for every_file in unique_file.keys())