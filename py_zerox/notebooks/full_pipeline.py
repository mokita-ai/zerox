import sys
import os
import json
from pyzerox import zerox
import asyncio


os.environ['AZURE_API_KEY']='0f392a5abe5e4e1eb41ecddddea0781e'
os.environ['AZURE_API_BASE']='https://mokita-azure-openai-service-eastus-1.openai.azure.com/'
os.environ['AZURE_API_VERSION']='2024-02-15-preview'
 
# Add the parent directory to the system path to access 'utils'
parent_dir = os.path.abspath(os.path.join(os.getcwd(), ".."))
os.chdir(parent_dir)
sys.path.append(parent_dir)



model = "azure/gpt-4o-mini"
latex_ground_truth_file = "../validation dataset/s4/sec_gov_archives_edgar_data_84246_000155837024013506_rli_20240930x10q_htm_cut.tex"
pdf_file_location = '../validation dataset/s4/sec.gov_Archives_edgar_data_84246_000155837024013506_rli-20240930x10q.htm_cut.pdf'



kwargs = {
    "temperature": 0,
    "seed" : 5331,
    "top_p": 1.0,
    # "frequency_penalty": 1.3,
}


prompt = prompt = r"""
You are a system that converts PDF files to Latex.
Follow these guidelines for an effective conversion:

General guidelines:
- The PDF is given a a sequence of images; Convert them together and respect their sequence.
- Keep the original pages structure in the output.
- Use consistent section headings for all pages.
- For each page, check if it is a continuance of the hierarchy from the previous page.
- Respect the hierarchy of titles and subtitles using the following order: [ "section", "subsection", "subsubsection", "paragraph" ]
- A section, subsection, subsubsection, or a paragraph can start at a page and end in a following page.
- Standardize lists (bullet points, numbers, etc.) into a unified format.
- If a page has both tables and text, include both.
- Correctly escape special latex characters such as: & | % in order not to disrupt the latex parsing and rendering.
- Ignore special formatting latex such as \quad, \bigskip, \href, \underline etc
- Do not output sections, subsections or header that do not exist in the document.
- Do not output any latex comments

Tables guidelines:
- Plan tables ahead: output metadata for tables (number of columns and rows, what are the column headers, etc). Output the metadata in a separate section denoted by \tablemeta{...} where the elipses are placeholders for the metadata
- Use the table meta data to identify and format all tables including their content.
- Output the table latex.
- Output the column headers as a row.
- Be aware of column spans and row spans in tables.

Avoid these mistakes:
- Don NOT output tables as sections or subsections.
- Tables should have consistent unmber of columns. 
- Be careful with two-column texts that have line-wide tables and vice versa. 
- If a cell spans multiple columns, repeat its content for each column.
- If a cell spans multiple rows, repeat its content for each row.
- Do not remove spaces from section headers (e.g. \section{ThisIsHeader} is NOT correct, it should be \section{This is Header} )

Return only the Latex with no explanation.
"""



async def main():
    result = await zerox(file_path=pdf_file_location,
                     model=model, 
                     select_pages=[1, 2],
                     custom_system_prompt=prompt,
                     postprocessing_propmt="",
                     maintain_format=True,
                     **kwargs)
                      

    concated_text = ""

    for page in result.pages:
        concated_text += page.content + "\n"


    print("Predicted latex:\n")
    print(concated_text)

asyncio.run(main())