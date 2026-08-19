import os
import random
import time
import mlflow
import torch

def train():
    print("Starting MLflow training dummy job...")
    mlflow_uri = os.environ.get("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db")
    mlflow.set_tracking_uri(mlflow_uri)
    mlflow.set_experiment("pet-chat-finetuning")
    
    with mlflow.start_run():
        params = {"model": "phi-3", "epochs": 5, "lr": 2e-4, "batch_size": 8}
        mlflow.log_params(params)
        
        print(f"Training model with params: {params}")
        
        for epoch in range(params["epochs"]):
            loss = max(0.1, 1.0 - (epoch * 0.15) + (random.random() * 0.1))
            print(f"Epoch {epoch+1}/{params['epochs']} - loss: {loss:.4f}")
            mlflow.log_metric("loss", loss, step=epoch)
            time.sleep(1)
            
        print("Training complete!")
        # Simulate saving model weights
        dummy_model = torch.nn.Linear(10, 10)
        mlflow.pytorch.log_model(dummy_model, name="model", serialization_format="cloudpickle")
        print("Model logged to MLflow.")

if __name__ == "__main__":
    train()
