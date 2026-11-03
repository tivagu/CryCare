"""
Step3 : Split dataset and Augmentation SNR    
"""

import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
import shutil
import pathlib
from joblib import Parallel, delayed
import numpy as np
import soundfile as sf
from sklearn.model_selection import GroupShuffleSplit


Target_SR = 16000
SEED = 42
MAX_SHIFT_SAMPLE = int(Target_SR*0.25)
MIN_AUG_SNR_DB = 5.0
MAX_AUG_SNR_DB =15.0




def time_shift_audio(y_win: np.array, rng:np.random.Generator) -> np.ndarray:
    """
    input: sound freq array (32000) and random generate
    out: y_shifted (32000) shift in random circle [-MAX_SHIFT_SAMPLE: +MAX_SHIFT_SAMPLE]
    """
    # TODO: [Sáng tạo của bạn]
    # 1. Sinh số nguyên shift ngẫu nhiên bằng rng.integers(...)
    # 2. Dịch mảng bằng np.roll(...) và trả về kết quả
    randome_rng = rng.integers(-MAX_SHIFT_SAMPLE, +MAX_SHIFT_SAMPLE)
    y_shifted = np.roll(y_win, randome_rng)
    return y_shifted



def mix_noise_at_snr(clean_y:np.ndarray, noise_y: np.ndarray, target_snr_db: float):
    """
    Đầu vào: Mảng tiếng gốc clean_y (32000,), mảng tiếng ồn noise_y (32000,), và mức target_snr_db (5.0 -> 15.0)
    Đầu ra: Mảng y_mixed (32000,) đã trộn tạp âm theo đúng công thức RMS và chống clipping (> 0.99)
    """
    # TODO: [Sáng tạo của bạn]
    # 1. Tính clean_rms và noise_rms (nhớ cộng 1e-8 trong căn)
    # 2. Tính target_noise_rms = clean_rms / (10.0 ** (target_snr_db / 20.0))
    # 3. Nhân tỉ lệ cho noise_y rồi cộng vào clean_y
    # 4. Kiểm tra đỉnh max(abs(y_mixed)): nếu > 0.99 thì nhân (0.95 / peak) để chống vỡ tiếng
    clean_rms = np.sqrt(np.mean(clean_y**2)+ 1e-8)
    noise_rms = np.sqrt(np.mean(noise_y**2)+1e-8)
    
    target_noise_rms = clean_rms/(10.0**(target_snr_db/20.0))
    
    mixed_y = (target_noise_rms/noise_rms) * noise_y + clean_y
    peak = np.max(np.abs(mixed_y))
    if(peak > 0.99):
        return mixed_y*(0.95/peak)
    return mixed_y


def split_by_parent_group(wav_files: list) -> tuple:
    """
    Đầu vào: Danh sách toàn bộ đường dẫn file cửa sổ .wav từ Step 2
    Đầu ra: Tuple gồm 3 list: (train_files, val_files, test_files)
    """
    # TODO: [Sáng tạo của bạn]
    # 1. Tạo danh sách parent_ids bằng cách tách phần tên trước "_win":
    #    parent_ids = [p.stem.split("_win")[0] for p in wav_files]
    # 2. Dùng GroupShuffleSplit lần 1 (test_size=0.30) để tách train_idx (70%) và temp_idx (30%)
    # 3. Dùng GroupShuffleSplit lần 2 (test_size=0.50) trên temp_idx để tách val_idx (15%) và test_idx (15%)
    # 4. Trả về 3 danh sách đường dẫn file tương ứng
    file_arr = np.array(wav_files)
    parents_ids = np.array([p.stem.split("_win")[0] for p in file_arr])
    indices = np.arange(len(file_arr))
    
    gss_1 = GroupShuffleSplit(train_size=0.70,test_size=0.30, random_state=SEED)
    Train_idx, tempt = next(gss_1.split(indices, groups= parents_ids))
    
    tempt_files_arr = file_arr[tempt]
    tempt_parent_arr = parents_ids[tempt]
    tempt_idx = np.arange(len(tempt_files_arr)) 
    gss_2 = GroupShuffleSplit(train_size=0.50, test_size=0.50, random_state=SEED)
    Valid_idx, Test_idx = next(gss_2.split(tempt_idx, groups=tempt_parent_arr))
    
    Train = file_arr[Train_idx].tolist()
    Valid = tempt_files_arr[Valid_idx].tolist()
    Test = tempt_files_arr[Test_idx].tolist()
    
    train_group = set(p.stem.split("_win")[0] for p in Train)
    Valid_group = set(p.stem.split("_win")[0] for p in Valid)
    Test_group = set(p.stem.split("_win")[0] for p in Test)
    
    assert len(train_group.intersection(Valid_group)) == 0
    assert len(Valid_group.intersection(Test_group)) == 0
    assert len(train_group.intersection(Test_group)) == 0
    
    return Train,Valid,Test


# ==========================================
# TẦNG 3: HÀM XỬ LÝ 1 FILE TRONG TỪNG TẬP (WORKER CHO JOBLIB)
# Nhiệm vụ: Copy file gốc vào thư mục split ("train"/"val"/"test").
#           Nếu split == "train", tạo thêm bản ghi đã Augment!
# ==========================================
def process_split_file(file_path: pathlib.Path, split_name: str, output_base_dir: pathlib.Path, seed: int):
    """
    Đầu vào: 1 đường dẫn file_path, tên tập ("train", "val", hoặc "test"), thư mục đích, và seed
    Đầu ra: Dict trạng thái xử lý của file đó
    """
    try:
        # Tạo thư mục con: output_base_dir / split_name (VD: out_Step3/train)
        split_dir = output_base_dir / split_name
        split_dir.mkdir(parents=True, exist_ok=True)

        # 1. Luôn lưu/copy cửa sổ gốc vào thư mục split_dir
        # TODO: Đọc y, sr bằng sf.read() và lưu bản gốc (hoặc dùng shutil.copy2)
        origin_file = split_dir/ file_path.name
        shutil.copy2(file_path, origin_file)
        # 2. CHỈ KHI split_name == "train": Thực hiện Augmentation và lưu thêm file mới
        if split_name == "train" and file_path.name.startswith("Cry_"):
            y, sr = sf.read(file_path, dtype="float32")
            # TODO: [Sáng tạo của bạn]
            # - Khởi tạo rng = np.random.default_rng(seed)
            rng = np.random.default_rng(seed=seed)
            # - Gọi time_shift_audio(y, rng)
            shifted_y = time_shift_audio(y, rng)
            # - Tạo mảng tiếng ồn ngẫu nhiên: noise = rng.standard_normal(len(y))
            noise = rng.standard_normal(len(y))
            # - Chọn mức SNR ngẫu nhiên từ 5.0 đến 15.0 bằng rng.uniform(MIN_AUG_SNR_DB, MAX_AUG_SNR_DB)
            random_snr =rng.uniform(MIN_AUG_SNR_DB, MAX_AUG_SNR_DB)
            # - Gọi mix_noise_at_snr(...)
            mixed_noise = mix_noise_at_snr(shifted_y, noise, random_snr)
            # - Lưu file mới với tên: f"{file_path.stem}_aug.wav" bằng sf.write(..., subtype="PCM_16")
            output_file = split_dir/f"{file_path.stem}_aug.wav"
            sf.write(str(output_file), mixed_noise,Target_SR, subtype="PCM_16")
        return {"file": file_path.name, "split": split_name, "status": "ok"}
    except Exception as e:
        return {"file": file_path.name, "split": split_name, "status": f"error: {e}"}
    

def main(input: pathlib.Path, output: pathlib.Path):
    indir = pathlib.Path(input)
    outdir = pathlib.Path(output)
    wav_files = sorted(list(indir.rglob("*.wav")))
    outdir.mkdir(parents=True, exist_ok=True)
    train_files, valid_files, test_files = split_by_parent_group(wav_files)
    group = {"train":train_files,
             "valid": valid_files,
             "test": test_files}
    Parallel(n_jobs=-1)(delayed(process_split_file)(p, split_name,outdir, 42+idx)for split_name, file_list in group.items() for idx, p in enumerate(file_list))



if __name__ == "__main__":
    input = r"D:\2026-2027\CryCare\Implementation\output\out_test2"
    output = r"D:\2026-2027\CryCare\Implementation\output\out_Step3"
    main(input, output)
    
    
    
    
    

