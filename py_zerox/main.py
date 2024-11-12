from fastapi import FastAPI, UploadFile, HTTPException, Query, File
from fastapi.middleware.cors import CORSMiddleware
from pyzerox.models import litellmmodel
from pydantic import BaseModel
from typing import List, Optional, Union
from pathlib import Path
import uuid
import os
import json
import math
import aioshutil
import nest_asyncio
from evaluation_metrics.text_similarity import calculate_rouge_metrics
from evaluation_metrics.text_similarity import calculate_bleu_metrics
from pyzerox import zerox
from prompt import PROMPT, POST_PROCESSING_PROMP
from utils.latex_to_json import tex_file_to_json
from evaluation_metrics.DAR import evaluate_hierarchy
from utils.heading_normalizer import  normalize_headings
from dotenv import load_dotenv
from utils.block_extractor import extract_text
from utils.block_extractor import find_and_matching_values
from utils.common import prepare_fs_examples_pathes, sanitize_json
load_dotenv()


nest_asyncio.apply()

required_env_vars = ["AZURE_API_KEY", "AZURE_API_BASE", "AZURE_API_VERSION"]

for var in required_env_vars:
    if not os.getenv(var):
        raise RuntimeError(f"Environment variable {var} is required but not set.")







app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)

@app.get("/")
def app_root():
    return {"message": "Hello world"}




# Asynchronous function to parse text from PDF pages
async def pdf_to_latx(
    file_location: str, 
    pages: List[int],
    model: str, 
    **kwargs  # Expect unpacked keyword arguments
) -> str:
    
    fs_examples = prepare_fs_examples_pathes()


    result = await zerox(
        file_path=file_location, 
        model= "azure/" + model,
        custom_system_prompt = PROMPT, 
        postprocessing_propmt = POST_PROCESSING_PROMP,
        maintain_format=True,
        select_pages=pages, 
        fewshot_examples_paths=fs_examples,
        **kwargs  
    )
    
   
    return result.pages[0].content

    
@app.post("/parse-pages")
async def parse_pages(
    pdf_file: UploadFile, 
    ground_truth_tex_file: Union[UploadFile, str] = File(None),
    start_page: int = Query(...),
    end_page: int = Query(...),
    postprocess_gt: Optional[bool] = Query(False)
):
    # Check if the PDF file is actually a PDF
    if pdf_file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Please upload a PDF file!")

    model = 'gpt-4o'

    args = {
        "temperature": 0,
        "top_p": 1,
        "seed": 42,
        "max_tokens" : 4096 ,
    }

    if isinstance(ground_truth_tex_file, str):
        ground_truth_tex_file = None



    if ground_truth_tex_file :
        if not ground_truth_tex_file.filename.endswith(".tex"):
            raise HTTPException(status_code=400, detail="Please upload a valid .tex file for the ground truth!")


        
        # Read the JSON file content into the variable
        ground_truth_bytes = await ground_truth_tex_file.read()
        ground_truth_string = ground_truth_bytes.decode("utf-8")

        if postprocess_gt:
            pp_model = litellmmodel(model='azure/' + model,**args)
            ground_truth_string = await pp_model.cleaning_postprocessing(ground_truth_string , POST_PROCESSING_PROMP )


        try:
            ground_truth_json = tex_file_to_json(tex_data=ground_truth_string)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="erorr in parsing the ground truth file to json")



    # Generate a random filename for the PDF in a temporary directory
    temp_dir = Path("temp")  # Adjusted to local temp path
    temp_dir.mkdir(parents=True, exist_ok=True)
    file_location = temp_dir / f"{uuid.uuid4().hex}.pdf"

    

    pages = range(start_page, end_page + 1)

    try:
        with open(file_location, "wb") as f:
            content = await pdf_file.read()
            f.write(content)

        pred_latex_code = await pdf_to_latx(
            file_location.as_posix(), 
            pages, 
            model,
            **args  
        )


        pred_json = tex_file_to_json(tex_data=pred_latex_code)

    except Exception as e:
        # Capture the error and return the message in the response
        raise HTTPException(status_code=500, detail=f"Error parsing the PDF document: {str(e)}")
    
    finally:
        # Ensure the file is removed
        if file_location.exists():
            os.remove(file_location)

    if not ground_truth_tex_file:
        return pred_json
    




    updated_pred_json, _ = normalize_headings(pred_json, ground_truth_json)

  


    pred_text_map, _ = extract_text(updated_pred_json)
   


    GT_text_map, _ = extract_text(ground_truth_json)

   

    matching_values = find_and_matching_values(pred_text_map, GT_text_map)
    
    rouge_values = calculate_rouge_metrics(matching_values)
    bleu_values = calculate_bleu_metrics(matching_values)



    try:
        metrics = evaluate_hierarchy(ground_truth_json, updated_pred_json )
    except Exception as e:
        print(f"Error during evaluation: {e}")



    metrics = {
        "rouge_values": rouge_values,
        "bleu_values": bleu_values,
        "hierarchy_metrics": metrics
    }

    metrics =  sanitize_json(metrics)
     
     
    return {'ground_truth_latex': ground_truth_string, 'ground_truth_json': ground_truth_json, 'predicted_latex': pred_latex_code, "predicted_json": pred_json, "metrics": metrics}

