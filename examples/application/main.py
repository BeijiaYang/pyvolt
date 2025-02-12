import os
import uuid
import json
from typing import List
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse

# Import our state estimation logic
from state_estimator import run_state_estimation

app = FastAPI()

UPLOAD_DIR = "./uploads"
RESULTS_DIR = "./results"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

jobs = {}  # In-memory job store

def process_job(job_id: str, file_paths: List[str]) -> None:
    """
    Background task: run state estimation and store the results.
    """
    try:
        result = run_state_estimation(file_paths)
        
        # Since 'result' is already a dict with float values,
        # we can directly dump it to a file.
        result_path = os.path.join(RESULTS_DIR, f"{job_id}.json")
        with open(result_path, "w") as f:
            json.dump(result, f)
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["result"] = result_path

    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)


@app.post("/jobs")
async def create_job(background_tasks: BackgroundTasks, files: List[UploadFile] = File(...)):
    """
    Endpoint to upload CIM/RDF (XML) files and create a state estimation job.
    """
    job_id = str(uuid.uuid4())
    job_upload_dir = os.path.join(UPLOAD_DIR, job_id)
    os.makedirs(job_upload_dir, exist_ok=True)
    
    file_paths = []
    for upload in files:
        file_path = os.path.join(job_upload_dir, upload.filename)
        with open(file_path, "wb") as f:
            content = await upload.read()
            f.write(content)
        file_paths.append(file_path)
    
    jobs[job_id] = {"status": "processing", "result": None}
    background_tasks.add_task(process_job, job_id, file_paths)
    
    return {"job_id": job_id, "status": "submitted"}


@app.get("/jobs/{job_id}")
async def get_job_result(job_id: str):
    """
    Endpoint to retrieve the state estimation results for a given job ID.
    """
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job["status"] == "completed":
        try:
            with open(job["result"], "r") as f:
                result_data = json.load(f)
            return {"job_id": job_id, "status": "completed", "result": result_data}
        except Exception as e:
            raise HTTPException(status_code=500, detail="Failed to read job result")
    elif job["status"] == "failed":
        return {"job_id": job_id, "status": "failed", "error": job.get("error")}
    else:
        return {"job_id": job_id, "status": job["status"]}
