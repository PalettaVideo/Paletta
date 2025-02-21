To run the Python FastAPI application, follow the steps:<br/>

1. setup a new virtual environment inside the \paletta_code folder
   > py -m venv .venv
2. start the virtual environment to set up the application with requirements.txt: <br/>
   > cd .\paletta_code\
   > .\.venv\Scripts\activate
3. install all dependencies required by the application
   > pip install -r requirements.txt
4. to start the application, run the following command: <br/>
   > uvicorn app.main:app --reload
