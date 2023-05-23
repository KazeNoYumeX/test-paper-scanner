import os
import cv2
import pytesseract
import re
from pdf2image import convert_from_path

# 設定Tesseract OCR的路徑
pytesseract.pytesseract.tesseract_cmd = 'C:/Program Files/Tesseract-OCR/tesseract.exe'

# 定義正則表達式模式，用於識別選擇題的選項
option_pattern = r'\(\w\)\s*([A-Za-z\s]+)'

# 字元黑名單，用於過濾特定字元
char_blacklist = ['~', '@', '#', '$', '%', '¢', '“', '‘', '’', '∞', 'θ', '•', 'à', 'β', '∅', '³']


def pdf_to_images(pdf_path):
    return convert_from_path(pdf_path)


# 圖片預處理和OCR識別
def perform_ocr(pdf_images):
    texts = []

    # 逐一處理每個圖像
    for i, image in enumerate(pdf_images):
        # 將圖像儲存為檔案
        image_path = 'pdf_images_{}.jpg'.format(i)
        image.save(image_path)

        # 使用 cv2.imread() 讀取圖像檔案
        image = cv2.imread(image_path)

        # 在這裡進行你需要的圖像處理操作

        if image is None:
            print('無法讀取圖像')

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        thresholded = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

        # 將預處理後的圖片保存並使用進行OCR識別
        preprocessed_image_path = 'images_{}.jpg'.format(i)
        cv2.imwrite(preprocessed_image_path, thresholded)

        # 進行OCR識別
        text = pytesseract.image_to_string(preprocessed_image_path, lang='chi_tra')

        # 刪除暫存的圖像檔案
        os.remove(preprocessed_image_path)
        os.remove(image_path)

        # 保存識別結果
        after_process = post_process_text(text)
        print(after_process)
        texts.append(after_process)

    return texts


# 文本後處理，包括去除黑名單字元和其他後續處理操作
def post_process_text(text):
    # 過濾字元黑名單
    return ''.join(char for char in text if char not in char_blacklist)


# 提取題目和選項
def extract_question_and_options(text):
    # 利用正則表達式匹配選項
    options = re.findall(option_pattern, text)
    print(options)
    # 提取題目
    question = text.split(options[0])[0]

    return question, options


# 主程式
def main():
    # 讀取圖片並進行OCR識別
    pdf_path = 'test.pdf'
    # pdf_path = 'test1.pdf'
    pdf_images = pdf_to_images(pdf_path)
    ocr_text = perform_ocr(pdf_images)

    # ocr scan result
    print(ocr_text)


if __name__ == '__main__':
    main()
