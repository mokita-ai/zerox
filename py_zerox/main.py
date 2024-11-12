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



def calculate_metrics_pipeline(pred_json, ground_truth_json):
    """
    Calculates various metrics for a given prediction and ground truth JSON.

    Args:
        pred_json (dict): The prediction JSON object.
        ground_truth_json (dict): The ground truth JSON object.

    Returns:
        dict: A dictionary containing the calculated ROUGE values, BLEU values, and hierarchy metrics.
    """

    updated_pred_json, _ = normalize_headings(pred_json, ground_truth_json) ##_ is a placeholder will be used in the future for table metrics
    pred_text_map, _ = extract_text(updated_pred_json)
    GT_text_map, _ = extract_text(ground_truth_json)
    matching_values = find_and_matching_values(pred_text_map, GT_text_map)
    rouge_values = calculate_rouge_metrics(matching_values)
    bleu_values = calculate_bleu_metrics(matching_values)    
    metrics = evaluate_hierarchy(ground_truth_json, updated_pred_json )



    metrics = {
        "rouge_values": rouge_values,
        "bleu_values": bleu_values,
        "hierarchy_metrics": metrics
    }

    return sanitize_json(metrics)



async def pdf_to_latx(file_location: str, page_numbers: List[int], model: str, **args) -> str:
    """
    Converts a PDF file to LaTeX format.
    Args:
        file_location (str): The location of the PDF file to be converted.
        page_numbers (List[int]): A list of page numbers to be converted.
        model (str): The liteLLM model to be used for conversion.
        **kwargs: Additional keyword arguments to be passed to the conversion function.
    Returns:
        str: The LaTeX content of the specified pages from the PDF file.
    """
    fs_examples = prepare_fs_examples_pathes()

    print(f"page_numbers: {page_numbers}")

    result = await zerox(
        file_path = file_location, 
        model = model,
        custom_system_prompt = PROMPT, 
        postprocessing_propmt = POST_PROCESSING_PROMP,
        select_pages=page_numbers, 
        fewshot_examples_paths=fs_examples,
        **args  
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

 
    if pdf_file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Please upload a PDF file!")

    if isinstance(ground_truth_tex_file, str):
        ground_truth_tex_file = None

    if ground_truth_tex_file and not ground_truth_tex_file.filename.endswith(".tex"):
        raise HTTPException(status_code=400, detail="Please upload a valid .tex file for the ground truth!")


    ## args for the both the postprocessing and the model
    model = 'azure/gpt-4o'
    args = {
        "temperature": 0,
        "top_p": 1,
        "seed": 42,
        "max_tokens" : 4096 ,
    }
  

    if ground_truth_tex_file:
        ground_truth_tex_file = await ground_truth_tex_file.read()
        ground_truth_latex = ground_truth_tex_file.decode("utf-8") ##ground_truth_latex is now an string


        if postprocess_gt:
            pp_model = litellmmodel(model = model, **args)
            ## str -> str
            ground_truth_latex = await pp_model.cleaning_postprocessing(ground_truth_latex, POST_PROCESSING_PROMP)


        try:
            ground_truth_json = tex_file_to_json(tex_data=ground_truth_latex)
        except Exception as e:
            print(e)
            raise HTTPException(status_code=400, detail="erorr in parsing the ground truth latex file to json")


    ##temp file for the pdf
    temp_dir = Path("temp") 
    temp_dir.mkdir(parents=True, exist_ok=True)
    file_location = temp_dir / f"{uuid.uuid4().hex}.pdf"

    
    with open(file_location, "wb") as f:
        content = await pdf_file.read()
        f.write(content)

    predictes_latex = await pdf_to_latx(
        file_location.as_posix(), 
        page_numbers = range(start_page, end_page + 1), 
        model = model,
        **args  
    )




    try:
        pred_json = tex_file_to_json(tex_data=predictes_latex)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=400, detail="erorr in parsing the predicted latex file to json")
    finally:
        # Ensure the file is removed
        if file_location.exists():
            os.remove(file_location)


    ## if there is no ground truth file just return the parsed json
    if not ground_truth_tex_file:
        return pred_json
    


    try:
        metrics =  calculate_metrics_pipeline(pred_json, ground_truth_json)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=f"Error calculating the metrics")

   
     
    return {"ground_truth_latex": ground_truth_latex,
            "ground_truth_json": ground_truth_json,
            "predicted_latex": predictes_latex,
            "predicted_json": pred_json,
            "metrics": metrics}

