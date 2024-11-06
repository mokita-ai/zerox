import logging
import os
import asyncio
from typing import List, Optional, Tuple, Iterable, Union
from pdf2image import convert_from_path

# Package Imports
from .image import save_image
from .text import format_markdown
from ..constants import PDFConversionDefaultOptions, Messages
from ..models import litellmmodel


async def convert_pdf_to_images(local_path: str, temp_dir: str) -> List[str]:
    """Converts a PDF file to a series of images in the temp_dir. Returns a list of image paths in page order."""
    options = {
        "pdf_path": local_path,
        "output_folder": temp_dir,
        "dpi": PDFConversionDefaultOptions.DPI,
        "fmt": PDFConversionDefaultOptions.FORMAT,
        "size": PDFConversionDefaultOptions.SIZE,
        "thread_count": PDFConversionDefaultOptions.THREAD_COUNT,
        "use_pdftocairo": PDFConversionDefaultOptions.USE_PDFTOCAIRO,
        "paths_only": True,
    }

    try:
        image_paths = await asyncio.to_thread(
            convert_from_path, **options
        )
        return image_paths
    except Exception as err:
        logging.error(f"Error converting PDF to images: {err}")


async def process_page(
    image: Union[str, List[str]],
    model: litellmmodel,
    temp_directory: str = "",
    input_token_count: int = 0,
    output_token_count: int = 0,
    prior_page: str = "",
    prior_image: str = "",
    postprocessing_propmt: Optional[str] = None,
    semaphore: Optional[asyncio.Semaphore] = None,
    fewshot_examples_paths: Optional[Iterable[Tuple[os.PathLike, os.PathLike]]] = None
) -> Tuple[str, int, int, str]:
    """Process a single page of a PDF"""

    # If semaphore is provided, acquire it before processing the page
    if semaphore:
        async with semaphore:
            return await process_page(
                image,
                model,
                temp_directory,
                input_token_count,
                output_token_count,
                prior_page,
            )

    image_paths = [ os.path.join(temp_directory, img)  for img in image ]
    if prior_image != "":
        prior_image_path = os.path.join(temp_directory, prior_image)
    else:
        prior_image_path = None
    # Get the completion from LiteLLM
    try:
        completion = await model.completion(
            image_paths=image_paths,
            maintain_format=True,
            prior_page=prior_page,
            prior_page_path=prior_image_path,
            fewshot_examples_paths=fewshot_examples_paths
        )

        formatted_markdown = format_markdown(completion.content)
        input_token_count += completion.input_tokens
        output_token_count += completion.output_tokens
        # prior_page = formatted_markdown

        # with open("beforePP.tex", "w") as f:
        #     f.write(formatted_markdown)  
        if postprocessing_propmt:
            formatted_markdown = await model.cleaning_postprocessing(formatted_markdown , postprocessing_propmt)

        # with open("afterPP.tex", "w") as f:
        #     f.write(formatted_markdown)



        return formatted_markdown, input_token_count, output_token_count, None# prior_page

    except Exception as error:
        logging.error(f"{Messages.FAILED_TO_PROCESS_IMAGE} Error:{error}")
        return "", input_token_count, output_token_count, ""


async def process_pages_in_batches(
    images: List[str],
    concurrency: int,
    model: litellmmodel,
    temp_directory: str = "",
    input_token_count: int = 0,
    output_token_count: int = 0,
    prior_page: str = "",
    fewshot_examples_paths: Iterable[Tuple[os.PathLike, os.PathLike]]=None
):
    # Create a semaphore to limit the number of concurrent tasks
    semaphore = asyncio.Semaphore(concurrency)

    # Process each page in parallel
    tasks = [
        process_page(
            images,
            model,
            temp_directory,
            input_token_count,
            output_token_count,
            prior_page,
            semaphore,
            fewshot_examples_paths
        )
    ]

    # Wait for all tasks to complete
    return await asyncio.gather(*tasks)

