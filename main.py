"""Main File"""

import io
import os
import re
import tempfile
import logging
from zipfile import ZipFile

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Security
from fastapi.responses import StreamingResponse
from fastapi.security import APIKeyHeader
from PdfFilter import (
    get_pdf_file_content,
    extract_odd_pages,
    extract_pages_into_individual_pdf_files,
)

load_dotenv()
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
app = FastAPI()
API_KEY = os.environ.get("API_KEY")
API_KEY_NAME = "X-API-Key"

api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


async def get_api_key(key_header: str = Security(api_key_header)):
    """Get API Key Dependency"""
    if key_header == API_KEY:
        return api_key_header
    raise HTTPException(status_code=403, detail="Could not validate credentials")


@app.post("/process_pdf/")
async def process_pdf(pdf_url: str, api_key=Depends(get_api_key)):
    """Process PDF api handler"""
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Extract booking ID from URL
            booking_id = re.search(r"all_products-(\w+-\w+)", pdf_url)
            if not booking_id:
                raise HTTPException(status_code=400, detail="Invalid PDF URL format")
            booking_id = booking_id.group(1)
            logger.info("Extracted booking id: %s", booking_id)

            # Download and process PDF
            logger.info("Downloading PDF from %s", pdf_url)
            pdf_content = get_pdf_file_content(pdf_url, logger)
            logger.info("PDF download complete")

            temp_input_file = os.path.join(temp_dir, "temp_input_file.pdf")
            with open(temp_input_file, "wb") as file:
                file.write(pdf_content)

            logger.info("Extracting odd pages")
            temp_odd_pages_file = os.path.join(temp_dir, "temp_odd_pages_file.pdf")
            extract_odd_pages(temp_input_file, temp_odd_pages_file)

            logger.info("Extracting individual pages")
            output_files = extract_pages_into_individual_pdf_files(
                temp_odd_pages_file, os.path.join(temp_dir, booking_id)
            )

            # Create zip file in memory
            zip_filename = f"{booking_id}.zip"
            logger.info("Creating zip file: %s", zip_filename)
            zip_buffer = io.BytesIO()
            with ZipFile(zip_buffer, "w") as zip_file:
                for file in output_files:
                    zip_file.write(file, os.path.basename(file))

            # Stream the zip file as a response
            zip_buffer.seek(0)
            logger.info("Streaming zip file: %s", zip_filename)
            return StreamingResponse(
                iter([zip_buffer.getvalue()]),
                media_type="application/zip",
                headers={"Content-Disposition": f"attachment; filename={zip_filename}"},
            )

        except Exception as e:
            logger.error("An error occurred: %s", str(e))
            raise HTTPException(
                status_code=500, detail=f"An error occurred: {str(e)}"
            ) from e
