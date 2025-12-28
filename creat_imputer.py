import joblib
import numpy as np
import os
from sklearn.impute import SimpleImputer

# 1. Define the folder and file name
model_dir = 'models'
model_path = os.path.join(model_dir, 'imputer.pkl')

# 2. Create the folder if it's missing
os.makedirs(model_dir, exist_ok=True)

# 3. Create a NEW imputer (Born in Python 3.13.11 / Scikit-Learn 1.6)
# This uses the modern structure that avoids the 'AttributeError'
new_imputer = SimpleImputer(strategy='mean')

# 4. Fit it with placeholder data
# We use 3 columns to match your shark features (e.g., Speed, Sinuosity, Chlorophyll)
dummy_data = np.array([[0.5, 1.2, 0.1], [0.8, 2.5, 0.4], [np.nan, 1.5, 0.2]])
new_imputer.fit(dummy_data)

# 5. Save it as the official imputer
joblib.dump(new_imputer, model_path)

print(f"✅ Success! New 3.13.11-compatible imputer saved to: {model_path}")
