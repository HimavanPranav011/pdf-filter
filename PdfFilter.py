"""PDF Filter Automation"""

import requests
from fastapi import HTTPException
from PyPDF2 import PdfReader, PdfWriter


def get_pdf_file_content(pdf_url: str, logger) -> bytes:
    """Download the PDF"""
    try:
        headers = {
            "Sec-Ch-Ua": '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Sec-Ch-Ua-Platform": '"macOS"',
        }
        response = requests.get(pdf_url, headers=headers)
        response.raise_for_status()
        return response.content
    except requests.RequestException as e:
        logger.error(f"Error fetching PDF: {str(e)}")
        raise HTTPException(
            status_code=400, detail=f"Error fetching PDF: {str(e)}"
        ) from e


def extract_odd_pages(input_file, output_file):
    """Extract the odd pages of a pdf file"""
    pdf_reader = PdfReader(input_file)
    pdf_writer = PdfWriter()

    for i, _ in enumerate(pdf_reader.pages):
        if i % 2 == 0:
            current_page = pdf_reader.pages[i]
            pdf_writer.add_page(current_page)

    with open(output_file, "wb") as out:
        pdf_writer.write(out)


def extract_pages_into_individual_pdf_files(input_file, output_initial: str):
    """Extract pages from a pdf file"""
    pdf_reader = PdfReader(input_file)
    output_files = []
    for i, _ in enumerate(pdf_reader.pages):
        pdf_writer = PdfWriter()
        current_page = pdf_reader.pages[i]
        pdf_writer.add_page(current_page)

        output_file = f"{output_initial}_{i+1}.pdf"
        with open(output_file, "wb") as out:
            pdf_writer.write(out)
        output_files.append(output_file)
    return output_files
