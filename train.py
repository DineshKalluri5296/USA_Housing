import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.linear_model import Lasso
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

import mlflow
import mlflow.sklearn
from mlflow.tracking import MlflowClient
import joblib

# MLflow setup
mlflow.set_tracking_uri("http://107.22.130.253:5000")
mlflow.set_experiment("USA_Housing_price_Analysis12")

# Load data
df = pd.read_csv("USA_Housing.csv")
df = df.dropna()
df = df.drop(["Address"], axis=1)

X = df.drop(["Price"], axis=1)
y = df["Price"]

# Split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Start MLflow run
with mlflow.start_run():

    # Model
    model = LinearRegression()
    #model=DecisionTreeRegressor()
    #model=Lasso()
    #model=Ridge()
    model.fit(X_train, y_train)

    # Predictions
    pred = model.predict(X_test)

    # Metrics
    r2 = r2_score(y_test, pred)
    mae = mean_absolute_error(y_test, pred)
    mse = mean_squared_error(y_test, pred)

    print("r2_score:", r2)
    print("MAE:", mae)
    print("MSE:", mse)

    # Log parameters
    mlflow.log_param("model_type", "LinearRegression")

    # Log metrics
    mlflow.log_metric("r2_score", r2)
    mlflow.log_metric("mae", mae)
    mlflow.log_metric("mse", mse)

    # Log model
    mlflow.sklearn.log_model(
        sk_model=model,
        artifact_path="model",
        registered_model_name="USA_Housing_price"
    )

    # Save locally
    joblib.dump(model, "model.pkl")

# -----------------------------
# Update Model Description
# -----------------------------
client = MlflowClient()

latest_version = client.search_model_versions(
    "name='USA_Housing_price'"
)[-1].version

client.update_model_version(
    name="USA_Housing_price",
    version=latest_version,
    description="LinearRegression model trained on USA Housing dataset"
    # description="RandomForestRegressor model trained on USA_Housing dataset"
    # description="DecisionTreeRegressor model trained on USA_Housing dataset"
    # description="LassoRegressor model trained on USA_Housing dataset"
    # description="RigidRegressor model trained on USA_Housing dataset"
)

print(f"Model Version {latest_version} updated successfully!")
