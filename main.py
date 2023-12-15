from flask import Flask, request, jsonify
import pickle
import os
from google.cloud import storage

# OCR Library
import cv2

# NLP Library
import spacy
import re

app = Flask(_name_)

# Atur variabel lingkungan GOOGLE_APPLICATION_CREDENTIALS ke path file kredensial JSON Anda
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./crendential/mineral-math-408204-b85e1d993f45.json"

# Path ke file JSON di Google Cloud Storage
bucket_name = "physude-apps"
storage_client = storage.Client()
bucket = storage_client.get_bucket(bucket_name)
ner = None
result = None
        

# Fungsi untuk download ke GCS
# Fungsi untuk download ke GCS
def download_to_gcs(bucket_name, source_blob_name, destination_file_path, keyfile_path):

    # Create a client
    client = storage.Client()

    # Get the bucket and blob
    bucket = client.get_bucket(bucket_name)
    blob = bucket.blob(source_blob_name)

    # Download the file from the bucket to the local file
    blob.download_to_filename(destination_file_path)



# Pre-processing gambar sebelum diload ke model
def resize_image(input_path, output_path, target_size):
    try:
        image = cv2.imread(input_path)

        if image is None:
            raise FileNotFoundError(f"file failed to upload, Make sure you upload a .PNG .JPG .JPEG file")

        scale_percent = target_size / max(image.shape[0], image.shape[1])
        width = int(image.shape[1] * scale_percent)
        height = int(image.shape[0] * scale_percent)
        dim = (width, height)

        resized_image = cv2.resize(image, dim, interpolation=cv2.INTER_AREA)

        border_x = (target_size - resized_image.shape[1]) // 2
        border_y = (target_size - resized_image.shape[0]) // 2
        resized_image = cv2.copyMakeBorder(resized_image, border_y, border_y, border_x, border_x, cv2.BORDER_CONSTANT)

        # Save gambar yang sudah diresized
        cv2.imwrite(output_path, resized_image)
        respond = jsonify("Image successfully resized and saved")
        respond.status_code = 200
        return respond

    except Exception as e:
        respond = jsonify({'message': {e}})
        respond.status_code = 400
        return respond




# Perhitungan fisika dari rumus
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
        return print('Tidak ada aturan yang cocok untuk entities_list yang diberikan.')


def image_to_model(output_path):
    try:
        # Path Gambar diconvert ke numpy array (dari opencv)
        img_model = cv2.imread(output_path)
    
        if img_model is None:
            raise FileNotFoundError(f"Image File Not Found")

        return img_model

    except FileNotFoundError as e:
        respond = jsonify({'message': {e}})
        respond.status_code = 400
        return respond


@app.route('/', methods=['GET','POST'])
def predict() :
    if request.method == 'POST' :

        filename = request.json['filename']

        download_to_gcs('physude-apps', 'Image-questions/'+filename, './OCR/bucket-images/test.png', './credential/mineral-math-408204-b85e1d993f45.json')
        
        # Proses model OCR
        ocr_path = './OCR/model/model_COR.pkl'
        nlp_path = './NLP/model-best'
        input_path = './OCR/bucket-images/test.png'
        output_path = './OCR/output-images/resized_image.jpg'
        target_size = 1200

        resize_image(input_path, output_path, target_size)
            
        image_to_model(output_path)

        with open(ocr_path, 'rb') as model_file:
            loaded_reader = pickle.load(model_file)

        # Hasil OCR model
        result = loaded_reader.readtext(output_path, detail=0)
            
        ner = spacy.load(nlp_path)

        array_string = ' '.join(map(str, result))
        questions = ner(array_string)

        variabel_list = []
        numbers_list = []

        # Pattern regex
        pattern = re.compile(r'\b(\d+)\s*(?=[a-zA-Z])|\b(\d+)\s*$')

        # Looping variabel di soal
        for ent in questions.ents:
            variabel_list.append((ent.text))
            variabel_list = variabel_list

        # Looping nilai di soal
        numbers_list = [match.group(1) or match.group(2) for match in pattern.finditer(array_string)]

        # Bersihkan sebelum di predict
        if len(variabel_list) > 2:
            variabel_list.pop(2)
        
        numbers_list = [int(x) for x in numbers_list]

        result_calculate = calculate_result(variabel_list, numbers_list)

        # data convert ke JSON
        if array_string and result_calculate:
            # Jika keduanya tidak kosong, buat data_to_save dengan nilai yang sesuai
            data_to_save = {'Soal': array_string, 'Hasil_Perhitungan': result_calculate}
        else:
            # Jika salah satu atau keduanya kosong, buat data_to_save tanpa NULL
            data_to_save = {'Soal': array_string or "Data Kosong", 'Hasil_Perhitungan': result_calculate or "Hasil tidak diketahui"}

        respond = jsonify(data_to_save)
        respond.status_code = 200
        return respond
        
    return "OK"

if _name_ == '_main_':
    app.run(debug=True, host="0.0.0.0", port=8000)