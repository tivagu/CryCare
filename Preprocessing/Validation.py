"""
cut silince and filter white noise in audio
"""

import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
import pathlib
from joblib import Parallel, delayed
import numpy as np
import soundfile as sf
import librosa
import sys
TARGET_SR = 16000
TARGET_WINDOW_DURATION_SEC = 2.0
WINDOW_SAMPLE = int(TARGET_SR*TARGET_WINDOW_DURATION_SEC)
HOP_SAMPLE = int(TARGET_SR*1.0)

MIN_DBFS = -45.0
MAX_CLIP_RATIO = 0.05
MIN_SNR_DB = 3.0
MAX_SPECTRAL_FLATNESS = 0.35
MIN_CRY_BAND_RATIA = 0.30

Valid = {".wav", ".mp3", ".mp4", ".flac", ".ogg", ".m4a"}

# TẦNG 1: HÀM TÍNH TOÁN CHỈ SỐ CỦA 1 CỬA SỔ
# Nhiệm vụ: Chỉ làm toán, không quyết định pass/fail

def calculate_window_metrics(y_win: np.ndarray, sr: int = TARGET_SR) -> dict:
    """
    Đầu vào: Mảng numpy 1D đúng 32000 mẫu
    Đầu ra: Dictionary chứa 5 chỉ số:
            {"dbfs": ..., "clip_ratio": ..., "snr_db": ..., 
             "flatness": ..., "cry_band_ratio": ...}
    """
    # TODO: [Sáng tạo của bạn]
    # 1. Tính RMS và đổi ra dBFS
    # 2. Tính tỉ lệ mẫu chạm ngưỡng |y| >= 0.99 (clip_ratio)
    # 3. Tính dải động khung p90 vs p10 (snr_db) qua librosa.feature.rms
    # 4. Tính độ phẳng phổ qua librosa.feature.spectral_flatness
    # 5. Tính FFT qua np.fft.rfft và tỉ lệ năng lượng 300 - 3500 Hz
    
    #rms: reality average energy perfromace of 2 sec windwo 
    #dbfs: convert energy to Logarit Decibel, the smaller of sound, the greater negative number 
    rms = np.sqrt(np.mean(y_win**2)+1e-8)
    dbfs = 20*np.log10(rms)
    
    #check how many window reach digital ground <=> micro near baby mouth or over gain 
    over_sr = np.abs(y_win) >= 0.99
    ratio =np.mean(over_sr)
    
    #snr_db: Calculate energy of each window, P90 mean energy when baby cry, P10 mean energy when baby stop to take breath, the contrast ratio 
    frame_rms = librosa.feature.rms(y=y_win, frame_length=512, hop_length=256)
    P90 = np.percentile(frame_rms, 90)
    P10 = np.percentile(frame_rms, 10)
    snr_db = 20*np.log10((P90+1e-8)/(P10+1e-8))
    
    
    #Spectral flat: filtered white noise
    flatness = np.mean(librosa.feature.spectral_flatness(y=y_win, n_fft=512, hop_length=256)[0])
    
    
    #FFT
    rfft = np.fft.rfft(y_win)
    freq = np.fft.rfftfreq(n=len(y_win), d = 1.0/sr)
    band_mask = (freq >= 300.0) & (freq <3500.0)
    power_spec = np.abs(rfft) ** 2
    cry_ratio = np.sum(power_spec[band_mask]) / (np.sum(power_spec) + 1e-8)
    return {"dbfs": dbfs, "clip_ratio": ratio, "snr_db": snr_db, "flatness": flatness, "cry_ratio": cry_ratio}

    
    
    

# ==========================================
# TẦNG 2: HÀM QUYẾT ĐỊNH CHẤT LƯỢNG (VALIDATION)
# Nhiệm vụ: Nhận metrics -> trả về True (giữ) hoặc False (loại)
# ==========================================
def validate_window(metrics: dict, is_cry_label: bool) -> bool:
    """
    Đầu vào: Dict chỉ số từ Tầng 1 và cờ đánh dấu nhãn (True nếu là tiếng bé khóc)
    Đầu ra: bool (True: đạt chuẩn, False: loại)
    """
    # TODO: [Sáng tạo của bạn]
    # - Cả 2 nhãn đều phải thỏa mãn: không quá bé (MIN_DBFS) và không vỡ tiếng (MAX_CLIP_RATIO)
    # - Nếu is_cry_label == True: kiểm tra thêm snr_db, flatness, cry_band_ratio
    # - Nếu is_cry_label == False (tiếng ồn): có thể nới lỏng flatness/cry_band_ratio để giữ tiếng ồn làm tập âm
    if metrics["dbfs"] < MIN_DBFS or metrics["clip_ratio"] > MAX_CLIP_RATIO:
        return False
    
    if is_cry_label:
        if metrics["snr_db"] < MIN_SNR_DB or metrics["flatness"] > MAX_SPECTRAL_FLATNESS or metrics ["cry_ratio"] < MIN_CRY_BAND_RATIA:
            return False
    return True


# ==========================================
# TẦNG 3: HÀM XỬ LÝ 1 FILE (WORKER CHO JOBLIB)
# Nhiệm vụ: Cắt khoảng lặng -> Cắt cửa sổ -> Lọc -> Lưu đĩa
# ==========================================
def process_single_file(file_path: pathlib.Path, output_dir: pathlib.Path):
    """
    Đầu vào: Đường dẫn 1 file WAV 16kHz từ Step 1
    Đầu ra: List các dict kết quả của từng cửa sổ con được sinh ra từ file này
    """
    try:
        # 1. Đọc file WAV 16kHz bằng soundfile
        # y, sr = sf.read(...)

        # 2. Tách và ghép các đoạn có âm thanh (loại bỏ khoảng lặng dài)
        # intervals = librosa.effects.split(y, top_db=28, ...)
        # y_active = ghép các đoạn intervals lại (nếu rỗng thì giữ nguyên y)

        # 3. Vòng lặp trượt cửa sổ (Sliding Window)
        # for start in range(0, len(y_active) - WINDOW_SAMPLES + 1, HOP_SAMPLES):
        #     y_win = y_active[start : start + WINDOW_SAMPLES]
        #     metrics = calculate_window_metrics(y_win)
        #     
        #     if validate_window(metrics, is_cry_label=...):
        #         Lưu file y_win xuống output_dir với tên format: f"{file_path.stem}_win{index}.wav"
        #         sf.write(...)
        y, sr = sf.read(file_path, dtype="float32")
        out_folder = output_dir
        
        intervals = librosa.effects.split(y=y, top_db=28, frame_length=512, hop_length=256)
        if len(intervals)<=0:
            y_active = y
        else:
            y_active = np.concatenate([y[start:end] for start, end in intervals])
        
        is_cry = file_path.name.startswith("cry_")
        for start in range(0, len(y_active) - WINDOW_SAMPLE + 1 , HOP_SAMPLE):
            y_win = y_active[start: start+WINDOW_SAMPLE]
            metrics = calculate_window_metrics(y_win)
            
            if validate_window(metrics, is_cry_label=is_cry):
                output_file_path = out_folder/f"{file_path.stem}_win{start:06d}{str(file_path.suffix.lower())}"
                sf.write(str(output_file_path), y_win, TARGET_SR, subtype="PCM_16")
    except Exception as e:
        # Bắt lỗi nếu file hỏng
        print(f"Error: {e}")


# ==========================================
# TẦNG 4: HÀM ĐIỀU PHỐI CHÍNH (MAIN)
# Nhiệm vụ: Quét thư mục Step 1 -> Bật Parallel
# ==========================================
def main(standardized_input_dir: str, windows_output_dir: str):
    input = pathlib.Path(standardized_input_dir)
    output = pathlib.Path(windows_output_dir)
    output.mkdir(parents=True, exist_ok=True)
    wav_files = sorted(list(p for p in input.rglob("*.wav")))
    for file_path in wav_files:
        process_single_file(file_path, output)


if __name__ == "__main__":
    try:
        input = r"D:\2026-2027\CryCare\Implementation\output\out_test"
        output = r"D:\2026-2027\CryCare\Implementation\output\out_test2"
        main(input, output)
    except Exception as e:
        print(f"error: {e}")