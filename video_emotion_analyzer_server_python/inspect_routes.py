from main import app
import json

print("Routes:")
for route in app.routes:
    print(f"Path: {route.path}, Name: {route.name}, Methods: {route.methods}")
