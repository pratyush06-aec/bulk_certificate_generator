import csv
import io
import openpyxl
from fastapi import HTTPException, UploadFile
from typing import List, Dict, Any

async def parse_attendees_file(file: UploadFile) -> List[Dict[str, Any]]:
    filename = file.filename.lower()
    
    if not (filename.endswith(".csv") or filename.endswith(".xlsx")):
        raise HTTPException(status_code=400, detail="Unsupported file format. Please upload .csv or .xlsx")
        
    content = await file.read()
    
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
        
    recipients = []
    
    if filename.endswith(".csv"):
        try:
            text_content = content.decode("utf-8-sig") # handle BOM if present
            reader = csv.DictReader(io.StringIO(text_content))
            
            if not reader.fieldnames:
                raise HTTPException(status_code=400, detail="CSV is empty or missing headers.")
                
            # Normalize headers
            normalized_headers = [str(f).strip().lower() for f in reader.fieldnames]
            if "name" not in normalized_headers:
                raise HTTPException(status_code=400, detail="CSV must contain a 'name' column.")
                
            reader.fieldnames = normalized_headers
                
            for row in reader:
                # We specifically just extract 'name' per ponytail principles (YAGNI for position)
                recipients.append({"name": row.get("name", "").strip()})
                
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="Invalid file encoding. Please use UTF-8.")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error parsing CSV: {str(e)}")
            
    elif filename.endswith(".xlsx"):
        try:
            wb = openpyxl.load_workbook(filename=io.BytesIO(content), data_only=True)
            sheet = wb.active
            
            rows = list(sheet.iter_rows(values_only=True))
            if not rows:
                raise HTTPException(status_code=400, detail="Excel file is empty.")
                
            headers = [str(h).strip().lower() if h else "" for h in rows[0]]
            if "name" not in headers:
                raise HTTPException(status_code=400, detail="Excel file must contain a 'name' column.")
                
            name_idx = headers.index("name")
            
            for row in rows[1:]:
                # Check bounds and avoid 'None' string casting
                name_val = str(row[name_idx]).strip() if len(row) > name_idx and row[name_idx] is not None else ""
                recipients.append({"name": name_val})
                
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error parsing Excel file: {str(e)}")
            
    return recipients
