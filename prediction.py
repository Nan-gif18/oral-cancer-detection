import joblib
import numpy as np

# Load trained model
model = joblib.load("oral_cancer_model.pkl")

# yes/no encoder
def encode(value):
    return 1 if value.lower() == "yes" else 0

# Symptom questions in correct order
symptoms = [
    "mouth_ulcer_not_healing",
    "red_or_white_patches",
    "mouth_pain",
    "tongue_pain",
    "difficulty_swallowing",
    "jaw_stiffness",
    "loose_teeth",
    "bleeding_in_mouth",
    "neck_lump",
    "ear_pain",
    "bad_breath",
    "sore_throat",
    "toothache",
    "gum_swelling",
    "fever",
    "weight_loss"
]

print("\n🩺 Oral Cancer Symptom Checker")
print("Please answer with 'yes' or 'no'\n")

user_inputs = []

for symptom in symptoms:
    while True:
        value = input(f"Do you have {symptom.replace('_', ' ')}? (yes/no): ").strip().lower()
        if value in ["yes", "no"]:
            user_inputs.append(encode(value))
            break
        else:
            print("❌ Invalid input. Please enter 'yes' or 'no'.")

# Convert to NumPy array
input_data = np.array([user_inputs])

# Prediction
prediction = model.predict(input_data)[0]
probability = model.predict_proba(input_data)[0][1]

# Output result
print("\n📊 RESULT")
if prediction == 1:
    print("⚠️ High Risk: Oral Cancer Detected")
else:
    print("✅ Low Risk: Oral Cancer Not Detected")

print("Confidence:", round(probability * 100, 2), "%")
