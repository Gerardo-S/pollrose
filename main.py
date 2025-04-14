import sys
import threading
import time
import os
from fastapi import FastAPI, UploadFile, File, Form, Header, HTTPException
from fastapi.staticfiles import StaticFiles
import subprocess
from pathlib import Path

app = FastAPI()

# Define paths based on project structure
SCRIPT_PATH = Path("scripts/pollrose_mpl_09082020.py")  # Adjust if needed
DATA_PATH = Path("data")
FIGURE_PATH = Path("figures")

# Ensure output directory exists
FIGURE_PATH.mkdir(parents=True, exist_ok=True)
app.mount("/figures", StaticFiles(directory=FIGURE_PATH), name="figures")
# Set your API key
FASTAPI_KEY = os.environ["FASTAPI_KEY"] 
@app.get("/")
def home():
    return {"message": "Pollrose API is running!"}

# Use the following for user query 
# def generate_Pollrose(
#     site: str = Query(..., description="Site name (e.g., 'Jan' or 'Apr')"),
#     datafile: str = Query(..., description="CSV filename (e.g., 'January_Data.csv')"),
#     bdate: str = Query("1-15-2016", description="Start date (e.g., '1-15-2016')"),
#     edate: str = Query("1-16-2016", description="End date (e.g., '1-16-2016')"),
#     pollv: str = Query("PM25", description="Pollution variable (e.g., 'PM25' or 'O3')"),
   
                       
# ):
# Remove generatated figure from server after xx's
def delete_file_later(path: Path, delay: int =420):
        def delayed_delete():
            time.sleep(delay)
            try:
                 if path.exists():
                      os.remove(path)
                      print(f"[Cleanup] Deleted file: {path}")
            except Exception as e:
                 print(f"[Cleanup] Failed to delete {path}: {e}")
        threading.Thread(target=delayed_delete, daemon=True).start()


@app.post("/generate-pollrose/")       
def generate_pollrose_from_csv(
    file: UploadFile = File(...),
    site: str = Form(...),
    bdate: str = Form(...),
    edate: str = Form(...),
    pollv: str = Form(...),
    x_api_key: str = Header(default=None)
):
    if x_api_key != FASTAPI_KEY:
        raise HTTPException(status_code=403, detail="Unauthorized")
    """
    Run the pollution script and generate a plot based on user input.
    """
    pollv = pollv.lower()


    # Define the output file name
    output_filename = f"PRose_{site}_{bdate}_{edate}_{pollv}.png"
    output_path = FIGURE_PATH / output_filename
    was_cached = output_path.exists()

    if was_cached:
         print(f"[Cache Hit] Using existing figure: {output_path}")

    #  Save uploaded file to DATA_PATH
    data_file_path = DATA_PATH / file.filename
    with open(data_file_path, "wb") as f:
        f.write(file.file.read())
    # If figure already exists, skip re-generation
    if output_path.exists():
         print(f"[Info] Figure already exists, skipping regeneration: {output_path}")
    else:
    # Run the windrose script as a subprocess
        print(f"[Info] Generating new figure at: {output_path}")
        process = subprocess.run(
            [
            sys.executable,
            str(SCRIPT_PATH),
            "--ifile", str(data_file_path),
            "--site", site,
            "--bdate", bdate,
            "--edate", edate,
            "--binwidth", "22.5",
            "--fromnorth",
            "--bounds", "[0,10,20,30,40,50,60,np.inf]",
            "--max-pct", "60",
            "--wscut", "0.0",
            "--pollv", pollv, #Pass the selected pollutant
            "--outpath", str(FIGURE_PATH)
            ],
            capture_output=True,
            text=True
        )

        # Check for errors
        if process.returncode != 0:
            print("[Error] Subprocess stderr:", process.stderr)
            return {"error": "Failed to generate pollrose", "details": process.stderr}
    
    print("output_filename: ", output_filename)


    response = {"message": "Pollrose generated successfully!", 
            "image": f"figures/{output_filename}", 
            "cached": was_cached
            }

   
    # Delete files after delay
    delete_file_later(output_path, delay=420)
    delete_file_later(data_file_path, delay=420)

    return response