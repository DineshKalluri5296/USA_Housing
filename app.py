import boto3
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import joblib
import os
import time
import mlflow

# Prometheus
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

# -----------------------------
# Metrics
# -----------------------------
prediction_requests = Counter(
    "prediction_requests_total",
    "Total number of prediction requests"
)

prediction_latency = Histogram(
    "prediction_latency_seconds",
    "Total prediction latency"
)

inference_time = Histogram(
    "inference_time_seconds",
    "Model inference time"
)

preprocess_time = Histogram(
    "preprocess_time_seconds",
    "Preprocessing time"
)

model_accuracy = Gauge(
    "model_accuracy",
    "Model accuracy"
)
mlflow.set_tracking_uri("http://54.208.120.4:5000")  # <-- your MLflow server
mlflow.set_experiment("USA_Housing_price_Analysis1")
# -----------------------------
# S3 Config
# -----------------------------
BUCKET_NAME = "usa-ml-app1"
MODEL_KEY = "models/latest/model.pkl"
LOCAL_MODEL_PATH = "model.pkl"

app = FastAPI(title="USA Housing Price Prediction API")

model = None

# Feature order MUST match training
FEATURES = [
    "Avg_Area_Income",
    "Avg_Area_House_Age",
    "Avg_Area_Number_of_Rooms",
    "Avg_Area_Number_of_Bedrooms",
    "Area_Population"
]

# -----------------------------
# Download Model (with retry)
# -----------------------------
def download_model():
    s3 = boto3.client("s3")

    for attempt in range(3):
        try:
            print(f"Downloading model (attempt {attempt+1})...")
            s3.download_file(BUCKET_NAME, MODEL_KEY, LOCAL_MODEL_PATH)
            print("Model downloaded successfully")
            return
        except Exception as e:
            print(f"Download failed: {e}")
            time.sleep(2)

    raise Exception("Failed to download model from S3")

# -----------------------------
# Startup Event
# -----------------------------
@app.on_event("startup")
def load_model():
    global model

    if not os.path.exists(LOCAL_MODEL_PATH):
        download_model()

    model = joblib.load(LOCAL_MODEL_PATH)

    # Warm-up (important for latency)
    model.predict([[0, 0, 0, 0, 0]])

    # Set model accuracy (replace with real value if available)
    model_accuracy.set(0.91)

    print("Model loaded and warmed up successfully")

# -----------------------------
# Input Schema (FIXED)
# -----------------------------
class HousingInput(BaseModel):
    Avg_Area_Income: float
    Avg_Area_House_Age: float
    Avg_Area_Number_of_Rooms: float
    Avg_Area_Number_of_Bedrooms: float
    Area_Population: float

# -----------------------------
# Prediction Endpoint
# -----------------------------
@app.post("/predict")
def predict(data: HousingInput):

    global model

    if model is None:
        return {"error": "Model not loaded"}

    prediction_requests.inc()
    start_total = time.time()

    try:
        # -----------------------------
        # Preprocessing
        # -----------------------------
        start_pre = time.time()

        input_data = [[getattr(data, f) for f in FEATURES]]

        preprocess_time.observe(time.time() - start_pre)

        # -----------------------------
        # Inference
        # -----------------------------
        start_inf = time.time()

        prediction = model.predict(input_data)[0]

        inference_time.observe(time.time() - start_inf)

        # -----------------------------
        # Total latency
        # -----------------------------
        total_latency = time.time() - start_total
        prediction_latency.observe(total_latency)

        return {
            "prediction": float(prediction),
            "latency": total_latency
        }

    except Exception as e:
        return {"error": str(e)}

# -----------------------------
# Metrics Endpoint
# -----------------------------
@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# -----------------------------
# Run
# -----------------------------
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
