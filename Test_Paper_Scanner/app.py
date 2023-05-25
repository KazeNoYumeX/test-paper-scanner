import datetime as dt
import io
import os
import re
import cv2
import pypandoc
import pytesseract
from flask import Flask, request, jsonify
from pdf2image import convert_from_path
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from Test_Paper_Scanner.config_loader import config
from Test_Paper_Scanner.test_paper_scanner_logger import logger_handler

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


# 將PDF轉換為文本
def pdf_to_text(pdf_path):
    rsrcmgr = PDFResourceManager()
    retstr = io.StringIO()
    codec = 'utf-8'
    laparams = LAParams(line_margin=0.5, char_margin=2.0, word_margin=0.1, boxes_flow=0.5)
    device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
    with open(pdf_path, 'rb') as fp:
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        for page in PDFPage.get_pages(fp, check_extractable=True):
            interpreter.process_page(page)
    device.close()
    text = retstr.getvalue()
    retstr.close()
    return text


# 將文本轉換為Markdown
def text_to_markdown(text):
    output = pypandoc.convert_text(text, 'md', format='html')
    return output


# 調整Markdown格式
def adjust_markdown(markdown):
    # 在段落前插入空行
    markdown = markdown.replace('\n\n', '\n\n\n')
    # 調整標題格式
    markdown = markdown.replace('#', '# ')

    # 移除多餘的空白和換行
    markdown = re.sub(r'\s+', ' ', markdown)

    # 移除段落編號
    markdown = re.sub(r'\d+\.', '', markdown)

    # 在句子結尾加入換行符號
    markdown = re.sub(r'([。？！])', r'\1\n\n', markdown)

    # replace ╳ to x
    markdown = markdown.replace('╳', 'x')

    # replace ○１○２○３○４ to A B C D
    markdown = markdown.replace('○１', ' A')
    markdown = markdown.replace('○２', ' B')
    markdown = markdown.replace('○３', ' C')
    markdown = markdown.replace('○４', ' D')

    # 移除開頭的換行符號
    markdown = markdown.lstrip('\n')

    return markdown


# OCR
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


# PDF to Markdown
@app.route('/pdf_to_markdown', methods=['POST'])
def pdf_to_markdown():
    # 確保有上傳檔案
    if 'file' not in request.files:
        return response_json(422, 'No file uploaded')

    file = request.files['file']

    # Check file type is pdf
    mime_type = file.mimetype.split('/')[-1]

    if mime_type == 'pdf':
        file_path = 'uploaded_file.pdf'
    else:
        return response_json(405, 'File type not allowed')

    try:
        file.save(file_path)

        markdown_path = 'output3.md'

        # 提取PDF文本
        text = pdf_to_text(file_path)

        # 將文本轉換為Markdown
        markdown = text_to_markdown(text)

        # 調整Markdown格式
        markdown = adjust_markdown(markdown)

        # 將結果寫入文件
        with open(markdown_path, 'w', encoding='utf-8') as f:
            f.write(markdown)

        return response_json(200)
    except Exception as e:
        return response_json(500, str(e))


def initialize():
    app.logger.debug("Test Paper Scanner Start!")
    app.run()
