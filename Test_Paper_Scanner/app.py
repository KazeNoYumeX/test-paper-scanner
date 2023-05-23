import datetime as dt
from Test_Paper_Scanner.test_paper_scanner_logger import logger_handler
from Test_Paper_Scanner.config_loader import config
import os
import cv2
import pytesseract
from pdf2image import convert_from_path
from flask import Flask, request, jsonify

LOG_LEVEL = config['DEFAULT']['LOG_LEVEL']

basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.logger.addHandler(logger_handler)
app.logger.setLevel(LOG_LEVEL)
app.config['PERMANENT_SESSION_LIFETIME'] = dt.timedelta(hours=2)
app.config['SECRET_KEY'] = os.urandom(32)
app.logger.debug("Starting Test Paper Scanner service...")

# For Windows, Set tesseract.exe path
# pytesseract.pytesseract.tesseract_cmd = 'C:/Program Files/Tesseract-OCR/tesseract.exe'

# For filter black list
char_blacklist = ['~', '@', '#', '$', '%', '¢', '“', '‘', '’', '∞', 'θ', '•', 'à', 'β', '∅', '³']


def pdf_to_images(pdf_path):
    return convert_from_path(pdf_path)


def perform_ocr(images, lang='chi_tra'):
    texts = []

    # 逐一處理每個圖像
    for i, image in enumerate(images):
        # 將圖像儲存為檔案
        image_path = 'pdf_images_{}.jpg'.format(i)
        image.save(image_path)

        # 使用 cv2.imread() 讀取圖像檔案
        image = cv2.imread(image_path)

        # 在這裡進行你需要的圖像處理操作

        if image is None:
            response_json(500, 'Can not read image')

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        thresholded = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

        # 將預處理後的圖片保存並使用進行OCR識別
        preprocessed_image_path = 'images_{}.jpg'.format(i)
        cv2.imwrite(preprocessed_image_path, thresholded)

        # 進行OCR識別
        text = pytesseract.image_to_string(preprocessed_image_path, lang=lang)

        # 刪除暫存的圖像檔案
        os.remove(preprocessed_image_path)
        os.remove(image_path)

        # 保存識別結果
        after_process = post_process_text(text)
        texts.append(after_process)

    return texts


# 文本後處理，包括去除黑名單字元和其他後續處理操作
def post_process_text(text):
    # 過濾字元黑名單
    return ''.join(char for char in text if char not in char_blacklist)


def response_json(code=200, msg=None, data=None):
    return jsonify({
        'code': code,
        'msg': msg,
        'data': data
    })


# 定義API路由
@app.route('/question_ocr', methods=['POST'])
def process_ocr():
    # 確保有上傳檔案
    if 'file' not in request.files:
        return response_json(422, 'No file uploaded')

    file = request.files['file']
    lang = request.form.get('lang', 'TW')

    if lang == 'tw':
        lang = 'chi_tra'
    elif lang == 'en':
        lang = 'eng'
    else:
        return response_json(405, 'Lang type not allowed')

    # Check file type is pdf
    file_type = file.filename.split('.')[-1]
    mime_type = file.mimetype.split('/')[-1]

    if mime_type == 'pdf':
        file_path = 'uploaded_file.' + file_type
    # elif mime_type == 'jpeg' or mime_type == 'png':
    #     file_path = 'uploaded_file.' + file_type
    else:
        return response_json(405, 'File type not allowed')

    file.save(file_path)

    try:
        images = file_path

        if mime_type == 'pdf':
            images = pdf_to_images(file_path)

        # 進行OCR識別
        ocr_text = perform_ocr(images, lang)

        os.remove(file_path)

        return response_json(200, None, {'texts': ocr_text})
    except Exception as e:
        return response_json(500, str(e))


def initialize():
    app.logger.debug("Test Paper Scanner Start!")
    app.run()
