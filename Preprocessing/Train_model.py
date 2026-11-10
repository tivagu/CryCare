import pathlib
import sys
import os
os.environ["OMP_NUM_THREADS"] = "1" #OMP
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
from joblib import Parallel, delayed
import json
import numpy as np
from sklearn.metrics import(
    log_loss,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix
)
import matplotlib.pyplot as plt
from Model.BaseLineModel import LogisticModel, BaseLineModel
def load_data(feature_dir: str|pathlib.Path, feature_type: str = "1d"):
    feat_path = pathlib.Path(feature_dir)
    X_train = np.load(feat_path/f"X_train_{feature_type}.npy")
    Y_train =  np.load(feat_path/f"y_train.npy")
    X_valid =  np.load(feat_path/f"X_valid_{feature_type}.npy")
    Y_valid =  np.load(feat_path/f"y_valid.npy")
    X_test =  np.load(feat_path/f"X_test_{feature_type}.npy")
    Y_test =  np.load(feat_path/f"y_test.npy")
    return (X_train, Y_train), (X_valid, Y_valid), (X_test, Y_test)

def train_evaluate(model: BaseLineModel, feature_dir: pathlib.Path|str):
    (X_train, Y_train), (X_valid, Y_valid), (X_test, Y_test)=load_data(feature_dir=feature_dir)
    
    model.fit_model(X_train, Y_train, X_valid, Y_valid)
    train_proba = model.predict_proba(X_train)
    valid_proba = model.predict_proba(X_valid)
    BCE_train = log_loss(Y_train, train_proba)
    BCE_valid = log_loss(Y_valid, valid_proba)
    BCE_gap = abs(BCE_train - BCE_valid)
    Y_predict = model.predict(X_test) 
    return {
        "Train_Loss": BCE_train,
        "Valid_Loss": BCE_valid,
        "Loss_Gap": BCE_gap,
        "Accuracy": accuracy_score(Y_test, Y_predict),
        "Precision": precision_score(y_pred=Y_predict, y_true=Y_test),
        "Recall": recall_score(y_true=Y_test, y_pred=Y_predict),
        "F1": f1_score(y_true=Y_test, y_pred=Y_predict),
        "confusion_matrix": confusion_matrix(y_true=Y_test, y_pred=Y_predict).tolist()
    }
    
def Evaluate_Model( feature_dir: pathlib.Path):
    feat_dir = pathlib.Path(feature_dir)
    Log_Model = LogisticModel()
    metrics = train_evaluate(Log_Model, feat_dir)
    print(metrics)
    

if __name__ == "__main__":
    try:
        FEATURE_FOLDER = r"D:\2026-2027\CryCare\Implementation\output\Feature"
        Evaluate_Model(FEATURE_FOLDER)
    except Exception as e:
        print(f"Error: {e}")
    
    
    
    
    