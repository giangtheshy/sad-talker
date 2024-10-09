import os
import subprocess
import sys
from typing import List

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from uuid import uuid4

app = FastAPI()

# Define the base directory for uploads
BASE_UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")

# Ensure the base upload directory exists
os.makedirs(BASE_UPLOAD_DIR, exist_ok=True)


class VideoResponse(BaseModel):
    videos: List[str]


@app.post("/upload/", response_model=VideoResponse)
async def upload_images(
    case_id: str = Form(...),
    files: List[UploadFile] = File(...)
):
    """
    Endpoint to upload images, process them, and return video paths.
    
    - **case_id**: Identifier for the case.
    - **files**: List of image files.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")

    # Define the directory for this case_id
    case_dir = os.path.join(BASE_UPLOAD_DIR, case_id)
    os.makedirs(case_dir, exist_ok=True)

    saved_file_paths = []

    # Save each uploaded file
    for upload_file in files:
        # Secure the filename
        filename = os.path.basename(upload_file.filename)
        if not filename:
            raise HTTPException(status_code=400, detail="Invalid file name.")

        file_path = os.path.join(case_dir, filename)

        # Write the file to the server
        try:
            with open(file_path, "wb") as buffer:
                content = await upload_file.read()
                buffer.write(content)
            saved_file_paths.append(file_path)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save file {filename}: {e}")

    video_paths = []

    # Process each saved image to generate a video
    for image_path in saved_file_paths:
        image_name = os.path.splitext(os.path.basename(image_path))[0]
        video_filename = f"{image_name}.mp4"
        video_path = os.path.join(case_dir, video_filename)

        # Construct the command
        command = [
            sys.executable,
            "inference.py",
            "--source_image", image_path,             # Đường dẫn đến avatar ảnh
            "--result_dir", video_path,              # Thư mục để lưu kết quả video
            "--enhancer", "gfpgan",                  # Sử dụng GFPGAN để cải thiện khuôn mặt
            "--background_enhancer", "realesrgan",   # Sử dụng Real-ESRGAN để cải thiện nền video
            # "--still", "False",                      # Cho phép chuyển động đầu
            "--input_yaw", "180",                    # Góc quay đầu ngang 180 độ
            "--input_pitch", "180",                  # Góc gật đầu/ngửa đầu 180 độ
            "--input_roll", "0",                     # Góc nghiêng đầu 0 độ
            "--expression_scale", "1.5",             # Tăng cường biểu cảm khuôn mặt
            "--preprocess", "full"                   # Sử dụng ảnh đầy đủ để tạo video
        ]

        try:
            # Execute the subprocess command
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True  # This will raise CalledProcessError if the command fails
            )
            # Optionally, you can log the stdout and stderr
            print(f"Command output for {image_name}: {result.stdout}")
            print(f"Command errors for {image_name}: {result.stderr}")
            
            # Kiểm tra nếu video_path tồn tại
            if os.path.exists(video_path):
                if os.path.isdir(video_path):
                    # Nếu video_path là thư mục, tìm tất cả các file .mp4 bên trong
                    mp4_files = [
                        os.path.join(video_path, file)
                        for file in os.listdir(video_path)
                        if file.lower().endswith('.mp4')
                    ]
                    if not mp4_files:
                        raise HTTPException(status_code=500, detail=f"No .mp4 files found in {video_path}.")
                    video_paths.extend(mp4_files)
                elif os.path.isfile(video_path) and video_path.lower().endswith('.mp4'):
                    # Nếu video_path là tệp tin .mp4, thêm trực tiếp
                    video_paths.append(video_path)
            else:
                raise HTTPException(status_code=500, detail=f"Video not created for {image_name}.")
        except subprocess.CalledProcessError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error processing {image_name}: {e.stderr}"
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")

    # Convert absolute paths to relative paths or URLs if needed
    # For simplicity, returning absolute paths
    return VideoResponse(videos=video_paths)


# Optional: Endpoint to list all cases (for testing purposes)
@app.get("/cases/")
def list_cases():
    cases = os.listdir(BASE_UPLOAD_DIR)
    return {"cases": cases}
