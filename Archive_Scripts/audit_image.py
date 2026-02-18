from roboflow import Roboflow

# --- CONFIGURATION ---
ROBOFLOW_API_KEY = "t2jq94gHItiL5ZSLhwMG" 
PROJECT_NAME = "camelo-detection-v1" 
VERSION = 1

# The specific image you are worried about
# (Check your folder for the exact name, I am guessing based on your CSV)
IMAGE_PATH = "sp_scan_images/sp_-23.543167_-46.629333_2025-10.jpg" 

rf = Roboflow(api_key=ROBOFLOW_API_KEY)
project = rf.workspace().project(PROJECT_NAME)
model = project.version(VERSION).model

# 1. Predict with the LOW confidence (what you used before)
print("Saving low confidence version...")
model.predict(IMAGE_PATH, confidence=15, overlap=30).save("audit_low_conf.jpg")

# 2. Predict with HIGH confidence (what we probably want)
print("Saving high confidence version...")
model.predict(IMAGE_PATH, confidence=40, overlap=30).save("audit_high_conf.jpg")

print("Done! Open 'audit_low_conf.jpg' and 'audit_high_conf.jpg' to compare.")