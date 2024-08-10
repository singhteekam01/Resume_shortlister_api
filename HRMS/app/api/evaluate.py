from fastapi import APIRouter,Form, HTTPException
from typing import List, Optional
import os
from ..utils.controller import evaluate_resumes
import regex as re
import pandas as pd
from fastapi.responses import FileResponse
import os
from pathlib import Path

evaluate_router = APIRouter()



RESUME_DIR = "resume"


@evaluate_router.post("/evaluate")
async def evaluate(top_k: Optional[int] = Form(...), skillset: Optional[str] = Form(...)):
    if top_k is None or skillset is None:
        raise HTTPException(status_code=400, detail="Both 'top_k' and 'skillset' are required.")
    
    skillset_list = []  
    top_resumes = []  

    try:
        num_top_resumes = int(top_k)
        if num_top_resumes <= 0:
            raise ValueError("Number of top resumes must be a positive integer.")
        skillset_list = skillset.split(',')  
    except (ValueError, TypeError) as e:
        raise HTTPException(status_code=400, detail=str(e))

    top_resumes = evaluate_resumes(RESUME_DIR, skillset_list,top_k)

    # df = pd.DataFrame(top_resumes)

    return {
        "skillset": skillset_list,
        "top_resumes": top_resumes
    }


@evaluate_router.get("/download")
async def download_resume(filename: str):
    resume_dir = Path("resume") 
    
    file_path = os.path.join(resume_dir,filename)

    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=file_path,
        media_type='application/octet-stream',
        filename=filename
    )