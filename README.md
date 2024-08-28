# OCR KTP Flask Application

This Flask application performs Optical Character Recognition (OCR) on Indonesian KTP (Identity Card) images. The app uses `EasyOCR` and `Tesseract` to extract and process text from uploaded KTP images.

## Features

- **OCR Processing**: Extracts text from KTP images using EasyOCR or Tesseract.
- **API Key Authentication**: Secures the API using an API key.
- **Error Handling**: Graceful handling of various error scenarios, including invalid file types, missing data, and internal server errors.

## Requirements

- Python 3.10+
- Flask
- EasyOCR
- PyTesseract
- Pillow
- pytest (for testing)

## Installation

1. **Clone the repository**:

   ```bash
   git clone https://github.com/yourusername/ocr-ktp-flask.git
   cd ocr-ktp-flask
   ```

2. **Create a virtual environment** (optional but recommended):

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install the dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Install Tesseract**:
   - On Ubuntu:
     ```bash
     sudo apt-get install tesseract-ocr
     ```
   - On macOS:
     ```bash
     brew install tesseract
     ```
   - On Windows, download the installer from the [Tesseract website](https://github.com/tesseract-ocr/tesseract).

## Usage

1. **Run the Flask application**:

   ```bash
   flask run
   ```

2. **Access the application**:

   - Visit `http://127.0.0.1:5000/` to interact with the application.

3. **Endpoints**:

   - **`GET /`**: Returns a welcome message.
   - **`GET /healthz`**: Returns the health status of the application.
   - **`POST /`**: Upload an image for OCR processing. Requires an `X-API-KEY` header and form data with the image file.

   **Example cURL request**:

   ```bash
   curl -X POST -H "X-API-KEY: YOUR_API_KEY" -F "image=@path_to_image/sample_ktp.png" -F "ocr_choice=easyocr" http://127.0.0.1:5000/
   ```

## API Key Configuration

The application requires an API key to access protected endpoints. The default API key is `67BD92FF-9408-43C4-A9F3-8CC942694F1E`.

To change the API key:

1. Update the `API_KEY` in `app.py`.
2. Pass the new API key in the `X-API-KEY` header with each request.

## Testing

To run the unit tests:

1. **Install test dependencies**:

   ```bash
   pip install pytest pytest-cov
   ```

2. **Run the tests**:

   ```bash
   pytest
   ```

3. **Generate a test coverage report**:
   ```bash
   pytest --cov=app --cov-report=html
   ```

## Project Structure

```plaintext
ocr-ktp-flask/
├── app.py              # Main Flask application
├── tests/
│   ├── test_app.py     # Unit tests for the application
├── requirements.txt    # Python dependencies
├── README.md           # Project documentation
└── ...                 # Other necessary files
```
