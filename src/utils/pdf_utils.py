import os
import re
import pdfplumber
from PyPDF2 import PdfReader, PdfWriter

def split_payslip_pdf(pdf_path, output_dir):
    reader = PdfReader(pdf_path)

    with pdfplumber.open(pdf_path) as pdf:
        for index, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            
            # Improved extraction logic for your specific layout
            name = "Unknown"
            emp_id = "00"

            lines = text.split('\n')
            for line in lines:
                # Look for Employee Name
                if "Employee Name" in line:
                    # Extracts everything after 'Employee Name' but before 'Bank Name'
                    name_part = re.search(r'Employee Name\s+(.*?)\s+Bank Name', line)
                    if name_part:
                        name = name_part.group(1).strip()
                
                # Look for Employee ID
                if "Employee ID" in line:
                    # Extracts digits after 'Employee ID' but before 'Account Number'
                    id_part = re.search(r'Employee ID\s+(\d+)', line)
                    if id_part:
                        emp_id = id_part.group(1).strip()

            # Formatting Name: Replace spaces with underscores for the filename
            formatted_name = name.replace(" ", "_")
            filename = f"{formatted_name}_{emp_id}.pdf"

            writer = PdfWriter()
            writer.add_page(reader.pages[index])

            output_path = os.path.join(output_dir, filename)
            with open(output_path, "wb") as f:
                writer.write(f)