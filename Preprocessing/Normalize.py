import os
os.environ["OMP_NUM_THREADS"] = "1" #OMP
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
import hashlib
import soundfile as sf
from joblib import Parallel, delayed
import pathlib
from Subclass.BaseAudioLoader import CotainerLoader, FileLoader
import pandas as pd
Valid = {".wav", ".mp3", ".mp4", ".flac", ".ogg", ".m4a"}
Compressed = {".wav", ".flac", ".ogg"}
Target_SR = 16000
targer_hash = 65536

#UID file: This step is to filtered homogenous file = using hash_obj which is convert audio data 
def hash_file(input_file: pathlib.Path ):
    hash_obj = hashlib.md5()
    with open(input_file, "rb") as f:
        while chunk:= f.read(targer_hash):
            hash_obj.update(chunk)
    return hash_obj.hexdigest()

def load_single_audio(input: pathlib.Path, output_dir: pathlib.Path, md5: str, prefix: str):
    try:
        label = 1 if prefix == "Cry" else 0
        out_file = output_dir/f"{prefix}_{md5}_{label}.wav"
        if input.suffix.lower() in Compressed:
            loader = FileLoader()
            y = loader.load_normalize(input)
        else:
            cotainer = CotainerLoader()
            y = cotainer.load_normalize(input)
        sf.write(str(out_file), y, Target_SR, subtype="PCM_16")
        return {"path": out_file.name,"type": prefix, "status": "ok", "duration": len(y)/ Target_SR, "label": label}
    except Exception as e:
        return {"path": input.name, "type": prefix, "status": str(e), "duration": 0.0, "label": label}


def Normalization(input_folder: str, prefix: str):
    output_dir = r"D:\2026-2027\CryCare\Implementation\output\Normalize"
    folder = pathlib.Path(input_folder)
    out_folder = pathlib.Path(output_dir)
    out_folder.mkdir(parents=True, exist_ok=True)
    valid_files = sorted([p for p in folder.rglob("*") if p.is_file() and p.suffix.lower() in Valid])
    hashes = Parallel(n_jobs=-1, verbose=5)( delayed(hash_file)(p) for p in valid_files)
    
    unique_map = {}
    for p, h in zip(valid_files, hashes):
        if h not in unique_map:
            unique_map[h] = p
    res = Parallel(n_jobs=-1, verbose=5)(delayed(load_single_audio)(p,out_folder,h, prefix) for h,p in unique_map.items())
    df = pd.DataFrame(res)[['path', 'type', 'duration', 'label', 'status']]
    csv_path = out_folder/f"{prefix}.csv"
    df.to_csv(csv_path, index=True, index_label="index")
    

if __name__ == "__main__":
    try:
        input_cry = r"D:\2026-2027\CryCare\Implementation\Dataset\Cry"
        input_non_cry = r"D:\2026-2027\CryCare\Implementation\Dataset\Non-Cry"
        output = r"D:\2026-2027\CryCare\Implementation\output\out_test"
        Normalization(input_cry, "Cry")
        Normalization(input_non_cry, "Non")
    except Exception as e:
        print(f"error: {e}")
        
        
    
    
    
    
    
    
    
    
    
    
