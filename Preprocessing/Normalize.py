import os
os.environ["OMP_NUM_THREADS"] = "1" #OMP
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
import hashlib
import soundfile as sf
from joblib import Parallel, delayed
import pathlib
from Subclass.BaseAudioLoader import CotainerLoader, FileLoader
Valid = {".wav", ".mp3", ".mp4", ".flac", ".ogg", ".m4a"}
Compressed = {".wav", ".flac", ".ogg"}
Target_SR = 16000
targer_hash = 65536
def hash_file(input_file: pathlib.Path ):
    hash_obj = hashlib.md5()
    with open(input_file, "rb") as f:
        while chunk:= f.read(targer_hash):
            hash_obj.update(chunk)
    return hash_obj.hexdigest()

def load_single_audio(input: pathlib.Path, output_dir: pathlib.Path, md5: str, prefix: str):
    try:
        if input.suffix.lower() in Compressed:
            loader = FileLoader()
            y = loader.load_normalize(input)
        else:
            cotainer = CotainerLoader()
            y = cotainer.load_normalize(input)
        out_file = output_dir/f"{prefix}_{md5}.wav"
        sf.write(str(out_file), y, Target_SR, subtype="PCM_16")
        return {"path": str(input), "status": "ok", "duration": len(y)/ Target_SR}
    except Exception as e:
        return {"path": str(input), "status": e, "duration": 0.0}


def main(input_folder: str, output_dir: str, prefix: str):
    folder = pathlib.Path(input_folder)
    out_folder = pathlib.Path(output_dir)
    out_folder.mkdir(parents=True, exist_ok=True)
    valid_files = sorted([p for p in folder.rglob("*") if p.is_file() and p.suffix.lower() in Valid])
    hashes = Parallel(n_jobs=-1, verbose=5)( delayed(hash_file)(p) for p in valid_files)
    
    unique_map = {}
    for p, h in zip(valid_files, hashes):
        if h not in unique_map:
            unique_map[h] = p
    result = Parallel(n_jobs=-1)(delayed(load_single_audio)(p,out_folder,h, prefix) for h,p in unique_map.items())
    return result

if __name__ == "__main__":
    try:
        input_cry = r"D:\2026-2027\CryCare\Implementation\Dataset\Cry"
        input_non_cry = r"D:\2026-2027\CryCare\Implementation\Dataset\Non-Cry"
        output = r"D:\2026-2027\CryCare\Implementation\output\out_test"
        main(input_cry, output, "Cry")
        main(input_non_cry, output, "Non_Cry")
    except Exception as e:
        print(f"error: {e}")
    
    
    
    
    
    
    
    
    
    
