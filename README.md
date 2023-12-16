# Predict API
*This is a python code, so make sure you have python installed on your system.*

## Trigger the predict function from the model and get the API prediction endpoint :

1. Clone the repository then open it using your code editor.
2. Download the OCR model file with the __.pkl__ file format (or you can download it manually [here](https://drive.google.com/file/d/1oj9TXcMqGw8eSdkxZ4SoBWC-RLltfzV8/view?usp=sharing)) and name it "__model_COR.pkl__" (to match with the scripts), then create 2 new folders with the name "__OCR/model__" and move the OCR model to the "__model__" folder
3. Now download the NER model you can download it [here](https://drive.google.com/file/d/1X9fk6UyP6BoBQZsGYMxqTcDrHeRx9Gxp/view?usp=sharing) and *extract here*, then create a new folder with the name "__NLP__" then move the folder you extracted earlier with the name "__model-best__" then now move it to the folder "__NLP__"
4. This code uses Google Cloud Storage, so you will need to create your own GCS Bucket with the name "physude-apps", create a folder called "Image-questions" inside the bucket, take the credential file (a .json file) and name it "__physedu.json__" (to match with the script), then create a new folder called "__credential__" and copy the .json file to this folder.
5. Open terminal in the project root directory, then run `pip install -r requirements.txt` to install the dependencies.
6. Run the app using the command: `python main.py`.
7. By default, the server will run on the localhost with the port 8000, open [http://localhost:8000](http://localhost:8000) to view it in your browser.
8. If it shows 'OK' then you have successfully run the predict api.
9. The next step is to configure the backend service, you can find it in the [backend](/) repository.
