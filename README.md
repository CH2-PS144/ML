# Predict API
*This is a python code, so make sure you have python installed on your system.*

## Trigger the predict function from the model and get the API prediction endpoint :

1. Clone the repository then open it using your code editor.
2. Download the OCR model file with the __.pkl__ file format, you can download it [here](https://drive.google.com/file/d/1mPkD_LbiXgNRYdDyaSfc95oz2Piu6Inq/view?usp=sharing)
3. Also download the NLP model you can download it [here](https://drive.google.com/file/d/1hqUd9mQQ-X3M5Y6zi0W_uozhSWNjnwwb/view?usp=sharing)
4. After you download it now right click on all zip file and then click *extract here*
5. This code uses Google Cloud Storage, so you will need to create your own GCS Bucket with the name "physude-apps", create a folder called "Image-questions" inside the bucket, take the credential file (a .json file) and name it "__physedu.json__" (to match with the script), then copy it to the root directory of this project.
6. Now your root directory will look like [this](https://drive.google.com/file/d/1Vd1t0QhQocN6tpfGEIvkvKuchxLf4hge/view?usp=sharing)
7. Open terminal in the project root directory.
8. Run `pip3 install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cpu` and then run `pip install -r requirements.txt` to install the dependencies
9. Run the app using the command: `python main.py`.
10. By default, the server will run on the localhost with the port 8000, open [http://localhost:8000](http://localhost:8000) to view it in your browser.
11. If it shows 'OK' then you have successfully run the predict api.
12. The next step is to configure the backend service, you can find it in the [backend](https://github.com/CH2-PS144/Backend) repository.
