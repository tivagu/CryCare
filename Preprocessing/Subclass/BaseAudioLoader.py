from abc import ABC, abstractmethod
import pathlib
import hashlib
import librosa
import soundfile as sf
import numpy as np

class BaseAudioLoader(ABC):
    Target = 16000
    
    def load_normalize(self, file_Path: pathlib.Path) -> np.ndarray:
        y = self.decode_to_mono_16k(file_Path)
        
        y = y - np.mean(y)
        
        y = librosa.util.normalize(y) * 0.95
        
        return y.astype(np.float32) 
    @abstractmethod
    def decode_to_mono_16k(self, path: pathlib.Path) -> np.ndarray:
        pass
    

class FileLoader(BaseAudioLoader):
    def decode_to_mono_16k(self, path: pathlib.Path):
        y, sr = sf.read(str(path), dtype="float32", always_2d=True)
        y_mono = np.mean(y, axis=1)
        if sr!= self.Target:
            y_mono = librosa.resample(y_mono, orig_sr=sr, target_sr=self.Target)
        return y_mono
    

class CotainerLoader(BaseAudioLoader):
    def decode_to_mono_16k(self, path: pathlib.Path):
        y_mono, _ = librosa.load(str(path), sr=self.Target, mono=True)
        return y_mono
    
        
