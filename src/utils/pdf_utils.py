import os
import re
import pdfplumber
from PyPDF2 import PdfReader, PdfWriter

def split_payslip_pdf(pdf_path, output_dir):
    reader = PdfReader(pdf_path)

    with pdfplumber.open(pdf_path) as pdf:
        for index, page in enumerate(pdf.pages):
            text = page.extract_text() or ""

            name = "Unknown"
            emp_id = None   # None means not found
            month = "Unknown"
            year = "Unknown"

            lines = text.split('\n')
            for line in lines:
                # --- Employee Name ---
                if "Employee Name" in line:
                    name_part = re.search(r'Employee Name\s+(.*?)\s+Bank Name', line)
                    if name_part:
                        name = name_part.group(1).strip()

                # # --- Employee Name ---
                # if "Employee Name" in line:
                #     # Try with "Bank Name" as right boundary (Sushil's format)
                #     name_part = re.search(r'Employee Name\s+(.*?)\s+Bank Name', line)
                #     if name_part:
                #         name = name_part.group(1).strip()
                #     else:
                #         # Fallback: grab everything after "Employee Name" (Shobha's format)
                #         name_part = re.search(r'Employee Name\s+(.+)', line)
                #         if name_part:
                #             name = name_part.group(1).strip()

                # --- Employee ID (optional) ---
                if "Employee ID" in line:
                    id_part = re.search(r'Employee ID\s+(\d+)', line)
                    if id_part:
                        emp_id = id_part.group(1).strip()

                # --- Month & Year from "PAYSLIP FOR THE MONTH OF <MONTH> <YEAR>" ---
                month_year = re.search(
                    r'PAYSLIP FOR THE MONTH OF\s+([A-Za-z]+)\s+(\d{4})',
                    line, re.IGNORECASE
                )
                if month_year:
                    month = month_year.group(1).capitalize()
                    year = month_year.group(2)

            # --- Build filename ---
            formatted_name = name.replace(" ", "_")

            if emp_id:
                filename = f"{formatted_name}_{month}_{year}_{emp_id}.pdf"
            else:
                filename = f"{formatted_name}_{month}_{year}.pdf"

            # --- Write page ---
            writer = PdfWriter()
            writer.add_page(reader.pages[index])

            output_path = os.path.join(output_dir, filename)
            with open(output_path, "wb") as f:
                writer.write(f)