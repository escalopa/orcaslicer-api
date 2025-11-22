#!/usr/bin/env python3
"""
Example usage of the OrcaSlicer API Python client.

This script demonstrates the complete workflow:
1. Upload a 3D model
2. Create a custom profile
3. Submit a slicing job with overrides
4. Poll for completion
5. Download results
"""

import time
import sys
from pathlib import Path

# Add src to path for local development
sys.path.insert(0, str(Path(__file__).parent))

from src.clients.python_client import OrcaSlicerClient, ApiError


def main():
    """Run example workflow."""
    # Initialize client
    client = OrcaSlicerClient(base_url="http://localhost:8000", timeout=30.0)

    print("🚀 OrcaSlicer API Example Workflow\n")

    # Step 1: Upload a model
    print("📤 Step 1: Upload model")
    model_file = "example.stl"  # Replace with your actual model file

    if not Path(model_file).exists():
        print(f"⚠️  Model file '{model_file}' not found.")
        print("   Please provide a valid .stl, .step, or .3mf file.")
        return

    try:
        model = client.upload_model(model_file)
        print(f"   ✓ Uploaded: {model['filename']}")
        print(f"   ID: {model['id']}")
        print(f"   Size: {model['size_bytes']:,} bytes\n")
    except ApiError as e:
        print(f"   ✗ Upload failed: {e.message}")
        return

    # Step 2: Create a custom profile
    print("⚙️  Step 2: Create slicing profile")
    try:
        profile = client.create_profile({
            "name": "Example_LargeRobot_PLA",
            "description": "Example profile for large manipulator with PLA",
            "source": "user",
            "vendor": "Ginger Additive",
            "machine_id": "ginger_large_manipulator",
            "process_id": "0.20mm Quality @Ginger",
            "filament_id": "Ginger PLA White",
            "settings_overrides": {
                "layer_height": 0.2,
                "infill_density": 25,
                "support_enable": True,
                "nozzle_temperature": 205,
                "bed_temperature": 60
            }
        })
        print(f"   ✓ Created: {profile['name']}")
        print(f"   ID: {profile['id']}\n")
    except ApiError as e:
        print(f"   ✗ Profile creation failed: {e.message}")
        return

    # Step 3: Create slice job with per-request overrides
    print("🔪 Step 3: Create slice job")
    try:
        job = client.create_slice_job(
            model_id=model["id"],
            profile_id=profile["id"],
            overrides={
                "layer_height": 0.16,  # Override profile's 0.2mm
                "infill_density": 40,   # Override profile's 25%
                "support_enable": False  # Override profile's True
            },
            output_options={
                "gcode": True,
                "project_3mf": True,
                "metadata_json": True
            },
            metadata={
                "job_reference": "example-job-001",
                "requested_by": "example-script"
            }
        )
        print(f"   ✓ Job created: {job['id']}")
        print(f"   Status: {job['status']}\n")
    except ApiError as e:
        print(f"   ✗ Job creation failed: {e.message}")
        return

    # Step 4: Poll for completion
    print("⏳ Step 4: Wait for slicing to complete")
    job_id = job["id"]
    max_attempts = 60  # 2 minutes with 2-second intervals
    attempt = 0

    while attempt < max_attempts:
        try:
            job = client.get_slice_job(job_id)
            status = job["status"]

            if status == "completed":
                print(f"   ✓ Slicing completed!")
                duration = (
                    job["finished_at"]
                    if job.get("finished_at")
                    else "unknown"
                )
                print(f"   Duration: {duration}\n")
                break
            elif status == "failed":
                print(f"   ✗ Slicing failed!")
                print(f"   Error: {job.get('error_message', 'Unknown error')}\n")
                return
            else:
                progress = job.get("progress_percent", 0)
                print(f"   Status: {status} ({progress}%)", end="\r")
                time.sleep(2)
                attempt += 1
        except ApiError as e:
            print(f"   ✗ Failed to get job status: {e.message}")
            return

    if job["status"] != "completed":
        print("\n   ⚠️  Job did not complete in time")
        return

    # Step 5: Download results
    print("📥 Step 5: Download results")

    # Download G-code
    try:
        gcode_file = f"{job_id}_output.gcode"
        client.download_gcode(job_id, gcode_file)
        print(f"   ✓ G-code saved: {gcode_file}")
    except ApiError as e:
        print(f"   ✗ Failed to download G-code: {e.message}")

    # Download 3MF project
    try:
        project_file = f"{job_id}_project.3mf"
        client.download_project_3mf(job_id, project_file)
        print(f"   ✓ 3MF project saved: {project_file}")
    except ApiError as e:
        print(f"   ✗ Failed to download 3MF: {e.message}")

    # Display metadata
    if job.get("output") and job["output"].get("metadata"):
        metadata = job["output"]["metadata"]
        print(f"\n📊 Print Metadata:")
        print(f"   Estimated time: {metadata.get('estimated_print_time_seconds', 0)} seconds")
        print(f"   Filament used: {metadata.get('filament_used_mm', 0):.1f} mm")
        print(f"   Filament weight: {metadata.get('filament_used_g', 0):.1f} g")
        print(f"   Layer count: {metadata.get('layer_count', 0)}")
        if metadata.get('bounding_box_mm'):
            bbox = metadata['bounding_box_mm']
            print(f"   Bounding box: {bbox['x']} x {bbox['y']} x {bbox['z']} mm")

    print("\n✅ Example workflow completed successfully!")

    # Cleanup (optional)
    print("\n🧹 Cleanup: Delete example profile")
    try:
        client.delete_profile(profile["id"])
        print(f"   ✓ Profile deleted: {profile['id']}")
    except ApiError as e:
        print(f"   ⚠️  Could not delete profile: {e.message}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        sys.exit(1)
