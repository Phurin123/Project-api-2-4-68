from flask import Flask, request, jsonify, send_from_directory
import uuid
import os
from PIL import Image
from werkzeug.utils import secure_filename
from ultralytics import YOLO
from flask_cors import CORS
from urllib.parse import quote

# การตั้งค่า Flask
app = Flask(__name__)
CORS(app)

# การตั้งค่าการอัปโหลดไฟล์
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'jfif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# สร้างโฟลเดอร์สำหรับการอัปโหลดไฟล์หากไม่มี
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ใช้ relative path สำหรับโมเดล YOLO
try:
    model_porn_path = os.path.join(os.path.dirname(__file__), 'models', 'best-porn.pt')
    model_porn = YOLO(model_porn_path)
except Exception as e:
    print(f"Error loading YOLO porn model: {e}")
    model_porn = None

# ใช้ relative path สำหรับโมเดล YOLO
try:
    model_weapon_path = os.path.join(os.path.dirname(__file__), 'models', 'best-weapon.pt')
    model_weapon = YOLO(model_weapon_path)
except Exception as e:
    print(f"Error loading YOLO weapon model: {e}")
    model_weapon = None

# ฟังก์ชันตรวจสอบประเภทไฟล์
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ฟังก์ชันตรวจสอบว่าไฟล์เป็นภาพจริงหรือไม่
def is_image(file_path):
    try:
        with Image.open(file_path) as img:
            img.verify()  # ตรวจสอบว่าเป็นไฟล์รูปภาพที่อ่านได้
        return True
    except (IOError, SyntaxError):
        return False

# ฟังก์ชันแปลง .jfif เป็น .jpg
def convert_jfif_to_jpg(input_path, output_path):
    try:
        with Image.open(input_path) as img:
            img.convert('RGB').save(output_path, 'JPEG')
        print(f"File converted and saved as {output_path}")
    except Exception as e:
        print(f"Error converting image: {e}")

# API สำหรับขอ API Key
@app.route('/request-api-key', methods=['POST'])
def request_api_key():
    data = request.get_json()
    email = data.get('email')
    if email:
        api_key = str(uuid.uuid4())
        return jsonify({'apiKey': api_key})
    return jsonify({'error': 'Email is required'}), 400

# API สำหรับการวิเคราะห์ภาพ
@app.route('/analyze-image', methods=['POST'])
def analyze_image():
    if model_porn is None or model_weapon is None:
        return jsonify({'error': 'Models not loaded successfully'}), 500

    # ตรวจสอบว่าไฟล์ภาพถูกส่งมาหรือไม่
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400

    file = request.files['image']
    
    # เข้ารหัสชื่อไฟล์ที่เป็นภาษาไทย
    filename = quote(file.filename)
    filename = secure_filename(filename)  # ใช้ secure_filename หลังจากเข้ารหัส

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)

    # ถ้าเป็นไฟล์ .jfif ให้แปลงเป็น .jpg
    if filename.lower().endswith('.jfif'):
        new_filename = filename.rsplit('.', 1)[0] + '.jpg'
        new_file_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
        convert_jfif_to_jpg(file_path, new_file_path)
        os.remove(file_path)  # ลบไฟล์ .jfif หลังจากแปลง
        file_path = new_file_path
        filename = new_filename

    # ตรวจสอบว่าไฟล์เป็นรูปภาพจริงหรือไม่
    if not is_image(file_path):
        os.remove(file_path)
        return jsonify({'error': 'File is not a valid image'}), 400

    try:
        # ใช้โมเดล YOLO วิเคราะห์ภาพโป๊เปลือย
        results_porn = model_porn.predict(source=file_path)
        has_inappropriate_content = False  # ตรวจสอบเนื้อหาที่ไม่เหมาะสม
        detections_porn = []

        for result in results_porn:
            for box in result.boxes:
                label = model_porn.names[int(box.cls)]
                confidence = float(box.conf)
                if label.lower() in ["inappropriate", "porn"]:  # ตัวอย่างคลาสที่ถือว่าไม่เหมาะสม
                    has_inappropriate_content = True

                detections_porn.append({
                    "label": label,
                    "confidence": confidence,
                    "bbox": box.xywh.tolist()
                })

        # ถ้าผ่านการตรวจสอบโป๊เปลือยแล้ว ให้ส่งไปตรวจสอบอาวุธ
        if not has_inappropriate_content:
            results_weapon = model_weapon.predict(source=file_path)
            detections_weapon = []

            for result in results_weapon:
                for box in result.boxes:
                    label = model_weapon.names[int(box.cls)]
                    confidence = float(box.conf)

                    detections_weapon.append({
                        "label": label,
                        "confidence": confidence,
                        "bbox": box.xywh.tolist()
                    })

            # สร้างภาพที่มี bounding boxes
            processed_image = Image.open(file_path)
            # ใส่โค้ดที่นี่เพื่อวาด bounding boxes บน processed_image (ตามที่ต้องการ)
            result_image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'processed_' + filename)
            processed_image.save(result_image_path)  # บันทึกภาพที่มีการประมวลผล

            os.remove(file_path)  # ลบไฟล์ที่อัปโหลดหลังจากการวิเคราะห์

            return jsonify({
                'status': 'passed',
                'detections_porn': detections_porn,
                'detections_weapon': detections_weapon,
                'processed_image_url': f'/uploads/{quote(result_image_path)}'  # ส่ง URL ของภาพที่ประมวลผล
            })

        else:
            os.remove(file_path)  # ลบไฟล์ที่อัปโหลดหลังจากการวิเคราะห์
            return jsonify({
                'status': 'failed',
                'detections_porn': detections_porn
            })

    except Exception as e:
        os.remove(file_path)  # ลบไฟล์ในกรณีที่เกิดข้อผิดพลาด
        return jsonify({'error': f'Error during analysis: {e}'}), 500

# การให้บริการไฟล์ที่อัปโหลด
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# API สำหรับรายงานปัญหา
@app.route('/report-issue', methods=['POST'])
def report_issue():
    try:
        data = request.get_json()
        issue_description = data.get('issue')

        if issue_description:
            with open('issues.txt', 'a') as file:
                file.write(issue_description + '\n')
            return jsonify({'success': True})
        return jsonify({'error': 'Issue description is required'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API สำหรับดาวน์โหลดเอกสารคู่มือ
@app.route('/download-manual', methods=['GET'])
def download_manual():
    manual_path = os.path.join(os.path.dirname(__file__), 'manual.pdf')  # ใช้ relative path
    if os.path.exists(manual_path):
        return send_from_directory(os.path.dirname(manual_path), os.path.basename(manual_path), as_attachment=True)
    return jsonify({'error': 'Manual file not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)
