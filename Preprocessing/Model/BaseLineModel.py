from abc import ABC, abstractmethod
import pathlib
import json
import numpy as np
import joblib
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    log_loss,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix
)
 
 
class BaseLineModel(ABC):
    def __init__(self, Feature_type):
        self.Feature_type = Feature_type
        self.Model = None
    
    @abstractmethod
    def fit_model(self, X_train: np.ndarray , Y_train: np.ndarray, X_valid: np.ndarray = None, Y_valid: np.ndarray = None):
        pass
    
    @abstractmethod
    def predict_proba(self, X_train: np.ndarray) -> np.ndarray:
        pass
    
    @abstractmethod
    def save(self, path: pathlib.Path):
        pass
    
    @abstractmethod
    def predict(self, X_train: np.ndarray) -> np.ndarray:
        pass

        

class LogisticModel(BaseLineModel):
    def __init__(self, C: float = 0.5, max_iter: int = 1000):
        super().__init__(Feature_type="1D")
        self.Model = Pipeline([("scaler", StandardScaler()), ("clf", LogisticRegression(C=C, class_weight= "balanced" ,max_iter= max_iter, random_state=42  ))])
        
    def fit_model(self, X_train, Y_train, X_valid, Y_valid):
        self.Model.fit(X_train, Y_train)
    
    def predict_proba(self, X_train):
        return self.Model.predict_proba(X_train)
    
    def predict(self, X_train: np.ndarray):
        return self.Model.predict(X_train)
    
    def save(self, path: pathlib.Path):
        path_dir = pathlib.Path(path)
        path_dir.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.Model, str(path_dir/f"_LogisticModel.joblib"))
    
    
        


    
    
        
        
    
        
        