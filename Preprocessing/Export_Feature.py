"""
Step 4: Feature Extraction with Abstract Base Class for ESP32 Audio Pipeline
"""

import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

import pathlib
import json
from abc import ABC, abstractmethod
from joblib import Parallel, delayed
import numpy as np
import soundfile as sf
import librosa
from Preprocessing.Extractor.BaseExtractor import MelSpectrogramExtractor, MFCCExtractor


# ==============================================================================
# TẦNG 2: HÀM WORKER CHO JOBLIB (XỬ LÝ 1 FILE)
# ==============================================================================

# Khởi tạo sẵn 2 đối tượng trích xuất để tái sử dụng
EXTRACTOR_1D = MFCCExtractor()
EXTRACTOR_2D = MelSpectrogramExtractor()

def process_single_file_features(wav_path: pathlib.Path, split_name: str, label: int):
    """
    Đầu vào: Đường dẫn 1 file .wav, tên tập ("train", "valid", "test"), và nhãn (1: khóc, 0: ồn)
    Đầu ra: Dict chứa dữ liệu đặc trưng đã trích xuất của file đó
    """
    try:
        y, sr = sf.read(str(wav_path), dtype="float32")
        
        # Gọi phương thức extract đa hình
        feat_1d = EXTRACTOR_1D.extractor(y)
        feat_2d = EXTRACTOR_2D.extractor(y)

        return {
            "split": split_name,
            "y": label,
            "x_1d": feat_1d,
            "x_2d": feat_2d,
        }
    except Exception as e:
        print(f"Lỗi khi xử lý {wav_path.name}: {e}")
        return None


# ==============================================================================
# TẦNG 3: HÀM ĐIỀU PHỐI CHÍNH (MAIN)
# ==============================================================================

def main(step3_output_dir: str, features_output_dir: str):
    in_dir = pathlib.Path(step3_output_dir)
    out_dir = pathlib.Path(features_output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Thu thập danh sách các task từ 3 thư mục: train, valid, test
    tasks = []
    for split_name in ["train", "valid", "test"]:
        split_folder = in_dir / split_name
        if not split_folder.exists():
            continue
        for wav_path in sorted(list(split_folder.rglob("*.wav"))):
            # Nhãn 1 nếu tên file hoặc thư mục chứa chữ "cry", ngược lại nhãn 0
            label = 1 if wav_path.name.startswith("Cry_") else 0
            tasks.append((wav_path, split_name, label))

    print(f"Bắt đầu trích xuất đặc trưng cho {len(tasks)} file...")

    # 2. Chạy đa tiến trình Parallel
    extracted_data = Parallel(n_jobs=-1, verbose=5)(
        delayed(process_single_file_features)(p, s, l) for p, s, l in tasks
    )
    # Lọc bỏ các phần tử lỗi None
    extracted_data = [item for item in extracted_data if item is not None]

    # 3. Phân tách và đóng gói mảng theo từng tập: train, valid, test
    # TODO: [Sáng tạo của bạn]
    Train = [i for i in extracted_data if i["split"] == "train"]
    Valid = [i for i in extracted_data if i["split"] == "valid"]
    Test = [i for i in extracted_data if i["split"] == "test"]
    
    # - Gom X_1d_train, X_2d_train, y_train từ các phần tử có r["split"] == "train"
    # - Gom tương tự cho valid và tes
    X_1d_train =np.stack([i["x_1d"] for  i in Train])
    X_2d_train = np.stack([i["x_2d"] for i in Train])
    y_train = np.array([i["y"] for i in Train], dtype=np.int64)
    
    X_1d_valid =np.stack([i["x_1d"] for  i in Valid])
    X_2d_valid = np.stack([i["x_2d"] for i in Valid])
    y_valid = np.array([i["y"] for i in Valid], dtype=np.int64)
        
    X_1d_test =np.stack([i["x_1d"] for  i in Test])
    X_2d_test = np.stack([i["x_2d"] for i in Test])
    y_test = np.array([i["y"] for i in Test], dtype=np.int64)
    
    # 4. CHUẨN HÓA Z-SCORE: Chỉ tính mean và std từ X_2d_train!
    #    mel_mean = float(np.mean(X_2d_train))
    #    mel_std  = float(np.std(X_2d_train) + 1e-8)
    #    Áp dụng công thức (X - mel_mean) / mel_std cho cả train, valid, test!
    mel_mean = float(np.mean(X_2d_train))
    mel_std = float(np.mean(X_2d_train + 1e-8))
    X_2d_train_norm = (X_2d_train - mel_mean)/mel_std
    X_2d_valid_norm = (X_2d_valid - mel_mean)/mel_std
    X_2d_test_norm = (X_2d_test-mel_mean)/mel_std
    # 5. Lưu các mảng nhị phân .npy bằng np.save(...)
    #    np.save(out_dir / "X_train_2d.npy", X_train_2d_norm)
    #    np.save(out_dir / "y_train.npy", y_train)
    #    ...
    np.save(out_dir / "X_train_1d.npy", X_1d_train)
    np.save(out_dir / "X_train_2d.npy", X_2d_train_norm)
    np.save(out_dir / "y_train.npy", y_train)
    
    np.save(out_dir / "X_valid_1d.npy", X_1d_valid)
    np.save(out_dir / "X_valid_2d.npy", X_2d_valid_norm)
    np.save(out_dir / "y_valid.npy", y_valid)
        
    
    np.save(out_dir / "X_test_1d.npy", X_1d_test)
    np.save(out_dir / "X_test_2d.npy", X_2d_test_norm)
    np.save(out_dir / "y_test.npy", y_test)

    # 6. Lưu file cấu hình DSP để sau này nạp vào firmware C++ trên ESP32
    #    dsp_config = {
    #        "target_sr": 16000,
    #        "n_fft": 512,
    #        "hop_length": 160,
    #        "n_mels": 40,
    #        "mel_mean": round(mel_mean, 4),
    #        "mel_std": round(mel_std, 4),
    #        "input_1d_dim": 60,
    #        "input_2d_shape": [40, 201, 1]
    #    }
    #    with open(out_dir / "esp32_dsp_config.json", "w", encoding="utf-8") as f:
    #        json.dump(dsp_config, f, indent=2)
    dsp_config = {
           "target_sr": 16000,
           "n_fft": 512,
            "hop_length": 160,
            "n_mels": 40,
            "mel_mean": round(mel_mean, 4),
            "mel_std": round(mel_std, 4),
            "input_1d_dim": 60,
            "input_2d_shape": [40, 201, 1]
        }
    with open(out_dir / "esp32_dsp_config.json", "w", encoding="utf-8") as f:
            json.dump(dsp_config, f, indent=2)
    print(f"Hoàn thành Step 4! Đã lưu đặc trưng vào: {out_dir}")


if __name__ == "__main__":
    INPUT_STEP3 = r"D:\2026-2027\CryCare\Implementation\output\out_Step3"
    OUTPUT_STEP4 = r"D:\2026-2027\CryCare\Implementation\output\Output_step4"
    main(INPUT_STEP3, OUTPUT_STEP4)