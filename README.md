[![Python application](https://github.com/arakattack/ocr-ktp/actions/workflows/python-app.yml/badge.svg)](https://github.com/arakattack/ocr-ktp/actions/workflows/python-app.yml) [![Push docker](https://github.com/arakattack/ocr-ktp/actions/workflows/docker-image.yml/badge.svg?event=release)](https://github.com/arakattack/ocr-ktp/actions/workflows/docker-image.yml)
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

1. Create a virtual environment (recommended) and activate it.

2. Install the required dependencies:

   ```bash
   pip install --no-cache-dir -r requirements.txt
   ```

3. Create a file named `.env` in your project directory and add the following environment variables, replacing the placeholders with your actual values:

   ```env
   API_KEY=your-api-key  # (Optional, for API access control)
   ```

## Configuration

- Update the environment variables in `.env` API_KEY=your-api-key for static API Key authentication.

## Usage

1. Start the application:

   ```bash
   python app.py
   ```

   The application runs on `http://0.0.0.0:5000` (localhost) by default in debug mode.

2. Make a POST request to the `/` endpoint with an image file in the `image` field of your multipart form data and `ocr_choice` easyocr or pytesseract ocr engine switch.  The API key needs to be included in the request header (if configured).

### Example Request (using cURL)

```bash
curl -X POST http://localhost:5000/ \
  -H "X-API-KEY: your_api_key" \
  -F "image=@transcript.jpg" -F 'ocr_choice="easyocr"'
```

### Example Response (JSON)

```json
{
    "error": false,
    "message": "OCR Success!",
    "data": {
        "nik": "3026061812510006",
        "nama": "WIDIARSO",
        "tempat_lahir": "PEMALANG,",
        "tgl_lahir": "18-12-1959",
        "jenis_kelamin": "LAKI-LAKI",
        "agama": "ISLAM",
        "status_perkawinan": "KAWIN",
        "pekerjaan": "KARYAWAN SWASTA",
        "alamat": {
            "name": "SKU JLSUMATRA BLOK B78/15",
            "rt_rw": "0037004",
            "kel_desa": "MEKARSARI",
            "kecamatan": "TAMBUN SELATAN",
            "kabupaten": "KABUPATEN BEKASI",
            "provinsi": "PROVINSI JAWA BARAT\n-"
        },
        "time_elapsed": 2.512
    }
}
```

### Testing

Implement unit tests for your functions using a framework like pytest.
Manually test the API endpoint using tools like Postman or cURL as demonstrated in the “Usage” section.

### Deployment (Docker Compose)

```bash
run docker-compose up
```

```yaml
version: "3"

services:
  ocr:
    build:
      context: .
      dockerfile: Dockerfile
    image: ocr
    container_name: ocr
    environment:
      API_KEY: "your_value"
    restart: unless-stopped
    ports:
      - "8000:8000"
    networks:
      - ocr-network
    command: gunicorn app:app -w 4 -t 90 --log-level=debug -b 0.0.0.0:8000 --reload --threads 2 --worker-class gevent --keep-alive 5 --timeout 60 --worker-connections 1000
networks:
  ocr-network:
    driver: bridge
```
