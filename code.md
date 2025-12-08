# CODE

```bash
MODEL_ID=$(curl -X POST http://localhost:8000/models \
  -F "file=@models/bracket.stl" | jq -r '.id')

PROFILE_ID=$(curl -X POST http://localhost:8000/profiles \
  -H "Content-Type: application/json" \
  -d '{
    "name": "LargeRobot_PLA_0.2mm",
    "description": "Profile for large manipulator",
    "source": "user",
    "vendor": "Ginger Additive",
    "machine_id": "ginger_large_manipulator",
    "process_id": "0.20mm Quality @Ginger",
    "filament_id": "Ginger PLA White",
    "settings_overrides": {
      "layer_height": 0.2,
      "infill_density": 25,
      "support_enable": true,
      "layer_gcode": "G92 E0"
    }
  }' | jq -r '.id')

curl -X POST http://localhost:8000/slice-jobs \
  -H "Content-Type: application/json" \
  -d "{
    \"model_id\": \"$MODEL_ID\",
    \"profile_id\": \"$PROFILE_ID\",
    \"overrides\": {
      \"layer_height\": 0.16,
      \"infill_density\": 40
    },
    \"output_options\": {
      \"gcode\": true,
      \"project_3mf\": true,
      \"metadata_json\": true
    }
  }"
```
