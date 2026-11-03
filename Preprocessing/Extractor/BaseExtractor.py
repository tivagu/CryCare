import pathlib
import librosa
from abc import ABC, abstractclassmethod
import numpy as np

class BaseExtractor(ABC):
    def __init__(self, target_sr =16000, n_fft=512, hop_length=160, n_mels=40, f_min=50.0, f_max=7600.0):
        self.sr = target_sr
        self.n_fft = n_fft
        self.hop_length = hop_length
        self.expect_sample = target_sr*2
        self.n_mels = n_mels
        self.f_min = f_min
        self.f_max = f_max
    
    def Validation_SFTF(self, y: np.ndarray):
        if len(y) < self.expect_sample:
            y = np.pad(y, (0, self.expect_sample - len(y)), mode= "constant")
        else:
            y = y[:self.expect_sample]
        
        # tinh stft cua dau vao 32000, dau ra la mot ma tran 2 chieu gom cot(time) hang(tan so)
        stft = librosa.stft(y, n_fft=self.n_fft, hop_length=self.hop_length, window="hann")
        
        power_spec = np.abs(stft)**2
        
        return y, power_spec

    @abstractclassmethod
    def extractor():
        pass
    

class MFCCExtractor(BaseExtractor):
    def __init__(self, n_mfcc = 13, **kwargs):
        super().__init__(**kwargs)
        self.n_mfcc =n_mfcc
    
    def extractor(self, y: np.ndarray):
        y_padded, power_spec = self.Validation_SFTF(y)
        mel_spectrogram = librosa.feature.melspectrogram(S=power_spec, sr=self.sr, n_mels=self.n_mels, fmin=self.f_min, fmax=self.f_max, htk=True)
        Log_Mels = 10*np.log10(np.maximum(mel_spectrogram, 1e-6))
        mfcc = librosa.feature.mfcc(S=Log_Mels, sr= self.sr, n_mfcc=self.n_mfcc)
        delta = librosa.feature.delta(mfcc)
        flatness=librosa.feature.spectral_flatness(S=np.sqrt(power_spec))
        centroid = librosa.feature.spectral_centroid(S=np.sqrt(power_spec))
        rolloff = librosa.feature.spectral_rolloff(S=np.sqrt(power_spec))
        crossing_rate = librosa.feature.zero_crossing_rate(y=y_padded, frame_length=self.n_fft, hop_length=self.hop_length)
        
        stacked = np.vstack([mfcc,delta,centroid,rolloff, flatness,crossing_rate])
        mean_feature = np.mean(stacked, axis=1)
        std_feature = np.std(stacked, axis=1)
        x_1d = np.concatenate([mean_feature, std_feature])
        
        return x_1d
    

class MelSpectrogramExtractor(BaseExtractor):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def extractor(self, y:np.ndarray):
        y_padded, power_spec = self.Validation_SFTF(y)
        mels_spectrogram = librosa.feature.melspectrogram(S=power_spec, sr= self.sr,n_mels=self.n_mels, fmin= self.f_min, fmax= self.f_max, htk=True)
        Log_Mels = 10*np.log10(np.maximum(mels_spectrogram, 1e-6))
        
        return Log_Mels[..., np.newaxis]
        
        
        
        
        