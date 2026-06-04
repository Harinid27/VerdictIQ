# VerdictIQ Auth Backend Server

FastAPI-powered authentication service for VerdictIQ AI Legal Operating System.

## Stack
- Python 3.12
- FastAPI
- MongoDB Atlas (via Motor async driver)
- JWT Authentication
- bcrypt password hashing

## Set Up
1. Create a Python virtual environment:
   ```bash
   python -m venv venv
   source venv/Scripts/activate  # On Windows: venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the development server:
   ```bash
   uvicorn app.main:app --reload
   ```

The auth server will run on `http://localhost:8000`. You can inspect the Swagger docs at `http://localhost:8000/docs`.
