from flask import Flask, request, jsonify, make_response
import easyocr, pytesseract
import numpy as np
import cv2, os
from ultralytics import YOLO
from PIL import Image, ImageEnhance, ImageFilter
from scipy.ndimage import rotate
from io import BytesIO
import re, datetime, textdistance, time

app = Flask(__name__)
app.json.sort_keys = False  # Ensure JSON response keeps order

MODEL_DIR = 'models/best.pt'  # Update with your model path
model = YOLO(MODEL_DIR)  # Load YOLO model
API_KEY = os.getenv('API_KEY') 

def validate_api_key(api_key):
    return api_key == API_KEY

def api_key_required(f):
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-KEY')
        if not api_key or not validate_api_key(api_key):
            error_response = make_response(jsonify({
                'error': True, 
                'message': 'API key required',
                'data':{}
                }), 401)
            return error_response
        return f(*args, **kwargs)
    return decorated_function

def correct_skew(img_blur, delta=1, limit=90):
    def determine_score(arr, angle):
        data = rotate(arr, angle, reshape=False, order=0)
        histogram = np.sum(data, axis=1, dtype=float)
        score = np.sum((histogram[1:] - histogram[:-1]) ** 2, dtype=float)
        return histogram, score

    gray = cv2.cvtColor(img_blur, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

    scores = []
    angles = np.arange(-limit, limit + delta, delta)
    for angle in angles:
        histogram, score = determine_score(thresh, angle)
        scores.append(score)

    best_angle = angles[scores.index(max(scores))]

    (h, w) = img_blur.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, best_angle, 1.0)
    corrected = cv2.warpAffine(img_blur, M, (w, h), flags=cv2.INTER_CUBIC, \
                               borderMode=cv2.BORDER_REPLICATE)

    return best_angle, corrected


def extract_date(date_text):
    try:
        match = re.search(r"(\d{1,2})([-/\.])(\d{2})\2(\d{4})", date_text)
        if match:
            day, month, year = int(match.group(1)), int(match.group(3)), int(match.group(4))
            return datetime.datetime(year, month, day)
        parsed_date = datetime.datetime.strptime(date_text, "%Y %m-%d")
        return parsed_date
    except ValueError:
        pass

    date_pattern = r"(\d{1,4})(?:[-/\.])(\d{1,2})(?:[-/\.])(\d{2,4})"
    match = re.search(date_pattern, date_text)
    if match:
        day, month, year = map(lambda x: int(x) if 1 <= int(x) <= 31 else None, match.groups())
        if day is not None and month is not None and year is not None:
            try:
                return datetime.datetime(year, month, day)
            except ValueError:
                return None
    return None

@app.route('/')
def hello():
    return jsonify({"error": False, "message": "System Ready!","data":{}}), 200
            
@app.route('/healthz')
def healthz():
    return jsonify({"error": False, "message": "System Healthy!","data":{}}), 200

@app.route('/', methods=['POST'])
@api_key_required
def upload_image():
    if 'image' not in request.files:
        return jsonify({"error": True, "message": "No file part", "data": {}}), 400

    file = request.files['image']

    if file.filename == '':
        return jsonify({"error": True, "message": "No selected file", "data": {}}), 400
    
    # Get the OCR choice from the request, default to 'pytesseract' if not provided
    ocr_choice = request.form.get('ocr_choice', 'pytesseract').lower()
    
    try:
        img = Image.open(BytesIO(file.read()))
        print('Preprocess:', file)
        img = img.convert('RGB')
        img_cv2 = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        img_cv2 = cv2.resize(img_cv2, (640, 480))
        img_blur = cv2.GaussianBlur(img_cv2, (3, 3), 0)

        angle, corrected = correct_skew(img_blur)
        print('Rotate angle:', angle)
        img_pil = Image.fromarray(cv2.cvtColor(corrected, cv2.COLOR_BGR2RGB))
        img_pil = img_pil.filter(ImageFilter.SHARPEN)
        enhancer = ImageEnhance.Contrast(img_pil)
        img_pil = enhancer.enhance(2)
        img_cv2 = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

        results = model.predict(np.array(img_cv2), imgsz=(480, 640), iou=0.7, conf=0.5)
        pil_img = Image.fromarray(cv2.cvtColor(img_cv2, cv2.COLOR_BGR2RGB))

        extracted_data = {}
        start_time = time.time()

        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                class_id = box.cls[0].item()
                confidence = box.conf[0].item()
                class_name = model.names[class_id]

                cropped_img_pil = pil_img.crop((x1, y1, x2, y2))
                cropped_img_cv2 = cv2.cvtColor(np.array(cropped_img_pil), cv2.COLOR_RGB2BGR)

                if ocr_choice == "pytesseract":
                    cropped_img_cv2 = cv2.resize(cropped_img_cv2, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
                    gray = cv2.cvtColor(cropped_img_cv2, cv2.COLOR_BGR2GRAY)
                    th, threshed = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                    extracted_text = pytesseract.image_to_string(threshed, lang="ind", config="--oem 3 --psm 6")
                elif ocr_choice == "easyocr":
                    reader = easyocr.Reader(['id'])
                    ocr_result = reader.readtext(cropped_img_cv2, workers=0)
                    extracted_text = " ".join([detection[1] for detection in ocr_result])
                else:
                    return jsonify({"error": True, "message": "Invalid OCR choice", "data": {}}), 400

                extracted_data[class_name] = extracted_text

                prov_kab = extracted_data.get('prov_kab', '')

                if "KOTA" in prov_kab:
                    provinsi, kabupaten = prov_kab.split("KOTA", 1)
                    kabupaten = "KOTA " + kabupaten.strip()
                elif "KABUPATEN" in prov_kab:
                    provinsi, kabupaten = prov_kab.split("KABUPATEN", 1)
                    kabupaten = "KABUPATEN " + kabupaten.strip()
                elif "JAKARTA" in prov_kab:
                    provinsi, kabupaten = prov_kab.split("JAKARTA", 1)
                    kabupaten = kabupaten.strip()
                    provinsi = "PROVINSI DKI JAKARTA"
                else:
                    provinsi = prov_kab
                    kabupaten = ""
                provinsi = provinsi.strip()

                if class_name == 'jk':
                    if textdistance.levenshtein(extracted_text.upper(), "LAKI-LAKI") < textdistance.levenshtein(extracted_text.upper(), "PEREMPUAN"):
                        extracted_data[class_name] = "LAKI-LAKI"
                    else:
                        extracted_data[class_name] = "PEREMPUAN"
                if class_name == 'nik':
                    for char in ["!", "l", ")", "L", "|", "]"]:
                        extracted_text = extracted_text.replace(char, "1")
                    extracted_text = extracted_text.replace("b", "6")
                    extracted_text = extracted_text.replace("?", "7")
                    extracted_text = extracted_text.replace("D", "0")
                    extracted_text = extracted_text.replace("B", "8")
                    extracted_data[class_name] = extracted_text
                if class_name == 'ttl':
                    match = re.search(r'\d', extracted_text)
                    if match:
                        index = match.start()
                        extracted_data['tempat_lahir'] = extracted_text[:index].strip()
                        extracted_data['tgl_lahir'] = extract_date(extracted_text[index:].strip())

        finish_time = time.time() - start_time
        response = {
            "error": False,
            "message": "OCR Success!",
            "data": {
                "nik": extracted_data.get('nik', '').strip(),
                "nama": extracted_data.get('nama', '').upper().strip().replace(":", ""),
                "tempat_lahir": extracted_data.get('tempat_lahir', '').upper().strip(),
                "tgl_lahir": extracted_data.get('tgl_lahir', '').strftime('%d-%m-%Y') if extracted_data.get('tgl_lahir') else '',
                "jenis_kelamin": extracted_data.get('jk', '').upper().strip(),
                "agama": extracted_data.get('agama', '').upper().strip(),
                "status_perkawinan": extracted_data.get('perkawinan', '').upper().strip(),
                "pekerjaan": extracted_data.get('pekerjaan', '').upper().strip(),
                "alamat": {
                    "name": extracted_data.get('alamat', '').upper().strip(),
                    "rt_rw": extracted_data.get('rt_rw', '').strip(),
                    "kel_desa": extracted_data.get('kel_desa', '').upper().strip(),
                    "kecamatan": extracted_data.get('kecamatan', '').upper().strip(),
                    "kabupaten": kabupaten.upper(),
                    "provinsi": provinsi.upper()
                },
                "time_elapsed": round(finish_time, 3)
            }
        }
        return jsonify(response), 200

    except Exception as e:
        return jsonify({"error": True, "message": str(e), "data": {}}), 500

if __name__ == '__main__':
    app.run(debug=True)
