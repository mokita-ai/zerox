from fastapi import FastAPI, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from pathlib import Path
import uuid
import os
import nest_asyncio
from pyzerox import zerox
from prompt import PROMPT
from latex_to_json import tex_file_to_json

# Apply nest_asyncio
nest_asyncio.apply()

# Required environment variables
required_env_vars = ["AZURE_API_KEY", "AZURE_API_BASE", "AZURE_API_VERSION"]
for var in required_env_vars:
    if not os.getenv(var):
        raise RuntimeError(f"Environment variable {var} is required but not set.")

model = "azure/gpt-4o-mini"

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

# Define Pydantic model for the response
class PageTextResponse(BaseModel):
    page_number: int
    text: Optional[str]

    @property
    def as_dict(self) -> dict:
        print(self.text)
        return tex_file_to_json(tex_data=self.text)

    def to_dict(self) -> dict:
        # Include both page data and as_dict representation in the output
        data = self.dict()
        data["as_dict"] = self.as_dict
        return data

# Asynchronous function to extract text from PDF pages
async def extract_pages_from_pdf(file_location: str, pages: List[int]) -> List[PageTextResponse]:
    result = await zerox(file_path=file_location, model=model,
                         custom_system_prompt=PROMPT, select_pages=pages)

    # Parse each page result to a Pydantic model
    pages_parsed = [
        PageTextResponse(
            page_number=page.page,
            text=page.content
        ) for page in result.pages
    ]
    return pages_parsed

# Endpoint to parse specified pages from uploaded PDF file
@app.post("/parse-pages")
async def parse_pages(
    file: UploadFile, 
    pages: List[int] = Query(...)
):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Please upload a PDF file!")

    # Generate a random filename for the PDF in a temporary directory
    temp_dir = Path("temp")  # Adjusted to local temp path
    temp_dir.mkdir(parents=True, exist_ok=True)
    file_location = temp_dir / f"{uuid.uuid4().hex}.pdf"

    # Save the uploaded file
    try:
        with open(file_location, "wb") as f:
            content = await file.read()
            f.write(content)

        # Parse the pages
        pages_data = await extract_pages_from_pdf(file_location.as_posix(), pages)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing the PDF document: {str(e)}")
    finally:
        # Ensure the file is removed
        if file_location.exists():
            os.remove(file_location)

    # Return a list of dictionaries with both the `text` and `as_dict` representations
    return [page.to_dict() for page in pages_data]
