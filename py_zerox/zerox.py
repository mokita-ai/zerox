from pyzerox import zerox
import os
import asyncio
from dotenv import load_dotenv
from prompt import PROMPT

# Load environment variables from .env file
load_dotenv()

### Model Setup (Use only Vision Models) Refer: https://docs.litellm.ai/docs/providers ###

## placeholder for additional model kwargs which might be required for some models
kwargs = {}

## system prompt to use for the vision model
# custom_system_prompt = "Convert the following PDF page to LaTeX. \
#     Return only the LaTeX with no explanation text. \
#     Do not exclude any content from the page. \
#     Use section and subsection for headings and preserve the structure and format."

###################### Example for Azure OpenAI ######################


model = "azure/gpt-4o-mini" ## "azure/<your_deployment_name>" -> format <provider>/<model>
os.environ["AZURE_API_KEY"] = os.getenv("AZURE_API_KEY")
os.environ["AZURE_API_BASE"] = os.getenv("AZURE_API_BASE")
os.environ["AZURE_API_VERSION"] = os.getenv("AZURE_API_VERSION")

# Define main async entrypoint
async def main():
    file_path = "./data/c.pdf" ## local filepath and file URL supported

    ## process only some pages or all
    select_pages = [3] ## None for all, but could be int or list(int) page numbers (1 indexed)

    output_dir = "./output_test" ## directory to save the consolidated markdown file
    result = await zerox(file_path=file_path, model=model, output_dir=output_dir,
                         custom_system_prompt=PROMPT, select_pages=select_pages, **kwargs)
    return result.pages

# run the main function:
result = asyncio.run(main())

