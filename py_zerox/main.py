from fastapi import FastAPI, UploadFile, HTTPException, Query, File
from fastapi.middleware.cors import CORSMiddleware
from pyzerox.models import litellmmodel
from pydantic import BaseModel
from typing import List, Optional, Union
from pathlib import Path
import uuid
import os
import json
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
from utils.textblock_extractor import extract_text
from utils.textblock_extractor import find_and_matching_values
from utils.common import prepare_fs_examples_pathes
load_dotenv()


# Apply nest_asyncio
nest_asyncio.apply()

# Required environment variables
required_env_vars = ["AZURE_API_KEY", "AZURE_API_BASE", "AZURE_API_VERSION"]
for var in required_env_vars:
    if not os.getenv(var):
        raise RuntimeError(f"Environment variable {var} is required but not set.")




# Initialize FastAPI app
app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)

# Define root endpoint
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
        **kwargs  # Unpack the dictionary as keyword arguments
    )
    
   
    return result.pages[0].content

# Endpoint to parse specified pages from uploaded PDF file
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
        "seed": 42
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


        # Convert the string to a dictionary
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

  

    # Get the list of dictionaries with headings and concatenated text
    pred_text_map = extract_text(updated_pred_json)
    GT_text_map = extract_text(ground_truth_json)

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
                
     
    return {'ground_truth_latex': ground_truth_string, 'ground_truth_json': ground_truth_json, 'predicted_latex': pred_latex_code, "predicted_json": pred_json, "metrics": metrics}


# class MetricsEvaluationRequest(BaseModel):
#     prompt: str


# @app.post("/metrics-evaluation")
# async def metrics_evaluation(request: MetricsEvaluationRequest):
#     prompt = request.prompt
#     metric_data_files = Path("metric_data_examples")

#     for file_location in metric_data_files.iterdir():
#         if file_location.suffix == ".pdf":
#             result  = await zerox(file_path=str(file_location), model=model, output_dir="./output_test",
#                                           custom_system_prompt=prompt )

#             predicted_latex = ""
#             for page in result.pages:
#                 predicted_latex += page.content + '\n'
                        

#             GT_latex_file = file_location.with_suffix(".tex")
#             with open(GT_latex_file) as f:
#                 GT_latex = f.read()
                

#             predicted_json = tex_file_to_json(tex_data = predicted_latex)
#             GT_json = tex_file_to_json(tex_data= GT_latex)


#             # ##save GT_json
#             GT_json_file = file_location.with_suffix(".GT.json")
#             with open(GT_json_file, 'w') as json_file:
#                 json.dump(GT_json, json_file, indent=4)

#             ##save predicted_json
#             predicted_json_file = file_location.with_suffix(".predicted.json")
#             with open(predicted_json_file, 'w') as json_file:
#                 json.dump(predicted_json, json_file, indent=4)


#             updated_pred_json, _ = normalize_headings(predicted_json, GT_json, "logs.txt")

#             ##save updated_pred_json
#             updated_pred_json_file = file_location.with_suffix(".updated_pred.json")
#             with open(updated_pred_json_file, 'w') as json_file:
#                 json.dump(updated_pred_json, json_file, indent=4)


#             # Get the list of dictionaries with headings and concatenated text
#             pred_text_map = extract_text(updated_pred_json)
#             GT_text_map = extract_text(GT_json)

#             matching_values = find_and_matching_values(pred_text_map, GT_text_map)


#             rouge_values = calculate_rouge_metrics(matching_values)
#             bleu_values = calculate_bleu_metrics(matching_values)



#             try:
#                 metrics = evaluate_hierarchy(GT_json, updated_pred_json )
#             except Exception as e:
#                 print(f"Error during evaluation: {e}")



#             response = {
#                 "rouge_values": rouge_values,
#                 "bleu_values": bleu_values,
#                 "hierarchy_metrics": metrics
#             }
#             return response


