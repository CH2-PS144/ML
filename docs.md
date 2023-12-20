# Machine Learning API Documentation

## Post a successfully run API
Endpoint : POST http://34.87.40.161:8000/predict
Response Body Success :
```json
{
    "question": "Seorang siswa berlari dengan jarak 5OOm, dia berlari dengan kecepatan 2m/s. Hitunglah besar waktu yang ditempuh oleh siswa tersebut!",
    "result": "Besar waktu: 2.5"
}
```

## Post not a picture (.png, .jpeg, .jpg)
Endpoint : POST http://34.87.40.161:8000/predict
Response Body Error :
```json
  {
      "status": {
          "code": 400,
          "message": "File failed to upload, Make sure you upload a .PNG .JPG .JPEG file"
      }
  }
```

## Post but not question type
Endpoint : POST http://34.87.40.161:8000/predict
Response Body Error :
```json
  {
    "question": "your data is not question type",
    "result": "no calculation"
  }
```
