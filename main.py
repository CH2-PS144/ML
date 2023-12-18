from flask import Flask, request, jsonify
import pickle
import os
from google.cloud import storage
from werkzeug.utils import secure_filename
import cv2
import spacy
import re
import os

app = Flask(__name__)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "physedu.json"

# Global Variabel
bucket_name = "physude-apps"
storage_client = storage.Client()
bucket = storage_client.get_bucket(bucket_name)

app.config['ALLOWED_EXTENSIONS'] = set(['png', 'jpg', 'jpeg'])  
app.config['UPLOAD_FOLDER'] = './OCR/bucket-images/'
app.config['OUTPUT_FOLDER'] = './OCR/output-images/'
app.config['OCR_PATH'] = './OCR/model/model_COR.pkl'
app.config['NLP_PATH'] = './NLP/model-best'

ner = None
result = None

# Check Image Format
def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']

# Upload image to GCS
def upload_from_gcs(bucket_name, local_file_path, remote_blob_name):
    client = storage.Client()
    bucket = client.get_bucket(bucket_name)
    blob = bucket.blob(remote_blob_name)
    blob.upload_from_filename(local_file_path)
    os.remove(local_file_path)

# Formula calculation
def calculate_result(entities_list, numbers_list):
    switch_dict = {
        ('massa', 'percepatan'): lambda: f'Besar gaya: {numbers_list[0] * numbers_list[1]}',
        ('jarak', 'waktu'): lambda: f'Besar kecepatan: {numbers_list[0] / numbers_list[1]}',
        ('kecepatan', 'waktu'): lambda: f'Besar jarak: {numbers_list[0] * numbers_list[1]}',
        ('jarak', 'kecepatan'): lambda: f'Besar waktu: {numbers_list[0] / numbers_list[1]}',
        ('massa', 'volume'): lambda: f'Besar massa jenis: {numbers_list[0] / numbers_list[1]}',
        ('massa jenis', 'volume'): lambda: f'Besar massa:{numbers_list[0] * numbers_list[1]}',
        ('massa', 'massa jenis'): lambda: f'Besar volume: {numbers_list[0] / numbers_list[1]}',
        ('gaya', 'percepatan'): lambda: f'Besar massa: {numbers_list[0] / numbers_list[1]}',
        ('gaya', 'massa'): lambda: f'Besar percepatan gaya {numbers_list[0] / numbers_list[1]}',
        ('gaya', 'sejauh', 'jarak'): lambda: f'Besar usaha: {numbers_list[0] * numbers_list[1]}',
        ('massa', 'kalor jenis', 'perubahan suhu'): lambda: f'Besar kalor: {numbers_list[0] * numbers_list[1] * numbers_list[2]}',
        ('massa', 'kecepatan'): lambda: f'Besar energi kinetik: {0.5 * numbers_list[0] * numbers_list[1] ** 2}',
        ('massa', 'setinggi', 'tinggi', 'ketinggian'): lambda: f'Besar energi potensial:  {numbers_list[0] * numbers_list[1] * 9.8}',
        ('energi kinetik', 'energi potensial'): lambda: f'Besar energi mekanik: {numbers_list[0] + numbers_list[1]}',
        ('periode',): lambda: f'Besar frekuensi gelombang:  {1 / numbers_list[0]}',
        ('frekuensi',): lambda: f'Besar periode gelombang: {1 / numbers_list[0]}',
        ('frekuensi', 'panjang gelombang'): lambda: f'Besar kecepatan gelombang: {numbers_list[0] * numbers_list[1]}',
        ('jari-jari',): lambda: f'Besar jarak fokus cermin: {numbers_list[0] / 2}',
        ('muatan', 'tegangan'): lambda: f'Besar kapasitas listrik: {numbers_list[0] / numbers_list[1]}',
        ('kapasitas listrik', 'tegangan'): lambda: f'Besar muatan benda: {numbers_list[0] * numbers_list[1]}',
        ('kapasitas listrik', 'muatan'): lambda: f'Besar potensial listrik: {numbers_list[0] / numbers_list[1]}',
        ('arus listrik', 'resistor'): lambda: f'Besar tegangan: {numbers_list[0] * numbers_list[1]}',
        ('tegangan', 'resistor'): lambda: f'Besar arus listrik: {numbers_list[0] / numbers_list[1]}',
        ('tegangan', 'arus listrik'): lambda: f'Besar resistansi/hambatan: {numbers_list[0] / numbers_list[1]}',
        # ... tambahkan kasus lain sesuai kebutuhan
    }
    key = tuple(entities_list)
    if key in switch_dict:
        return switch_dict[key]()
    else:
        return print('There is no matching rule for the given entities_list.')

# Resize image from client input
def resize_image(input_path, output_path, target_size):
    image = cv2.imread(input_path)
    scale_percent = target_size / max(image.shape[0], image.shape[1])
    width = int(image.shape[1] * scale_percent)
    height = int(image.shape[0] * scale_percent)
    dim = (width, height)
    resized_image = cv2.resize(image, dim, interpolation=cv2.INTER_AREA)
    border_x = (target_size - resized_image.shape[1]) // 2
    border_y = (target_size - resized_image.shape[0]) // 2
    resized_image = cv2.copyMakeBorder(resized_image, border_y, border_y, border_x, border_x, cv2.BORDER_CONSTANT)
    return cv2.imwrite(output_path, resized_image)

# Load model OCR & Delete resized_image
def load_model_OCR(ocr_path, image_model, output_path):
    with open(ocr_path, 'rb') as model_file:
        loaded_reader = pickle.load(model_file)
    result = loaded_reader.readtext(image_model, detail=0)
    os.remove(output_path)
    return result



@app.route('/', methods=['GET','POST'])
def predict() :
    if request.method == 'POST' :
        reqImage = request.files['image']
        ocr_path = app.config['OCR_PATH']
        nlp_path = app.config['NLP_PATH']
        target_size = 1200

        if reqImage and allowed_file(reqImage.filename):

            filename = secure_filename(reqImage.filename)
            reqImage.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            output_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
            
            resize_image(input_path, output_path, target_size)

            image_model = cv2.imread(output_path)

            result = load_model_OCR(ocr_path, image_model, output_path)

            ner = spacy.load(nlp_path)

            array_string = ' '.join(map(str, result))
            questions = ner(array_string)

            variabel_list = []
            numbers_list = []

            pattern = re.compile(r'\b(\d+)\s*(?=[a-zA-Z])|\b(\d+)\s*$')

            for ent in questions.ents:
                variabel_list.append((ent.text))
                variabel_list = variabel_list

            numbers_list = [match.group(1) or match.group(2) for match in pattern.finditer(array_string)]

            if len(variabel_list) > 2:
                variabel_list.pop(2)
            
            numbers_list = [int(x) for x in numbers_list]

            result_calculate = calculate_result(variabel_list, numbers_list)

            if array_string and result_calculate:
                data_to_save = {'Soal': array_string, 'Hasil_Perhitungan': result_calculate}
            else:
                data_to_save = {'Soal': array_string or "Empty Data", 'Hasil_Perhitungan': result_calculate or "No calculation"}

            upload_from_gcs(bucket_name, input_path, 'Image-questions/'+filename)

            respond = jsonify(data_to_save)
            respond.status_code = 200
            return respond
        else :
            return jsonify({
                'status': {
                    'code': 400,
                    'message': 'File failed to upload, Make sure you upload a .PNG .JPG .JPEG file'
                }
            }), 400

    elif request.method == 'GET' :
        return jsonify({
        'Data': {
            'Project': 'Capstone Bangkit 2023 Batch 2',
            'Tema': 'Education, Learning, and Personal Development',
            'Judul': 'Physedu - Smart Camera Calculator and Learning for Junior High School Physics Needs',
            'Team': 'CH2-PS144',
            'Anggota': [
                { 'BangkitID': 'M006BSX1223', 'Nama': 'Ida Sri Afiqah', 'Universitas': 'Universitas Brawijaya' },
                { 'BangkitID': 'M227BSY0228', 'Nama': 'Fasal Alif Haikal Irawan', 'Universitas': 'Universitas Jember' },
                { 'BangkitID': 'M227BSX1101', 'Nama': 'Erika Divian Chandhani', 'Universitas': 'Universitas Jember' },
                { 'BangkitID': 'C354BSY3093', 'Nama': 'Iko Raga Ahana Vidiantara', 'Universitas': 'Universitas Muhammadiyah Jember' },
                { 'BangkitID': 'C408BSY4325', 'Nama': 'Slamet Rofikoh', 'Universitas': 'Sekolah Tinggi Ilmu Ekonomi Mandala' },
                { 'BangkitID': 'A227BSY2674', 'Nama': 'Hendarta Widya Ardana', 'Universitas': 'Universitas Jember' },
                { 'BangkitID': 'A622BSY2486', 'Nama': 'Rokman Nurhidayat', 'Universitas': 'Universitas Muhammadiyah Tangerang' },
            ],
            'Copyright': '©2023 All Rights Reserved!'
        }
    }), 200

    else :
        return jsonify({
            'status': {
                'code': 405,
                'message': 'Method not allowed'
            }
        }), 405

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8000)