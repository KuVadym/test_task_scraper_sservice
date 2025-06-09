from types import SimpleNamespace
from pdf2image import convert_from_path
import pytesseract
import requests
from PIL import Image
import os
import re
import io


# Укажите путь к исполняемому файлу tesseract, если он не находится в системном PATH
# Например, для Windows это может быть что-то вроде:
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def remove_text_before_keyword(text, keyword):
   """Удаляет текст до и включая ключевое слово."""
   index = text.find(keyword)
   if index != -1:
       return text[index + len(keyword):].strip()
   return text


def extract_text_between_labels(text, start_label, end_label):
   """Извлекает текст между двумя метками в тексте."""
   pattern = rf'{re.escape(start_label)}(.*?){re.escape(end_label)}'
   matches = re.findall(pattern, text, re.DOTALL)
   return matches


def split_text_by_newline(text):
   """Разделяет текст по символам новой строки."""
   return re.split(r'\n+', text)


def extract_text_from_pdf(pdf_path):
   """Извлекает текст из PDF-файла с помощью OCR."""
   if not os.path.exists(pdf_path):
       raise FileNotFoundError(f"Файл {pdf_path} не найден.")

   try:
       pages = convert_from_path(pdf_path, 300, poppler_path=r'C:\Users\hamster\Downloads\Release-24.07.0-0\poppler-24.07.0\Library\bin') # 300 dpi для лучшего качества OCR
   except Exception as e:
       raise RuntimeError(f"Ошибка при преобразовании PDF в изображения: {e}")

   text = ""
   image_bytes = []
   for page_number, page_image in enumerate(pages):
       try:
           page_text = pytesseract.image_to_string(page_image)
           text += f"--- Page {page_number + 1} ---\n{page_text}\n\n"
           img_byte_arr = io.BytesIO()
           page_image.save(img_byte_arr, format='JPEG')
           image_bytes.append(img_byte_arr.getvalue())
       except Exception as e:
           print(f"Ошибка при выполнении OCR на странице {page_number + 1}: {e}")

   return text, image_bytes


def save_text_to_file(text, output_file):
   """Сохраняет текст в файл."""
   try:
       with open(output_file, 'w', encoding='utf-8') as file:
           file.write(text)
   except Exception as e:
       raise RuntimeError(f"Ошибка при сохранении текста в файл {output_file}: {e}")


def gather_and_validate_adrress(pdf_path, auth_id, auth_token):
    """Основная функция для обработки PDF и сохранения результатов."""
    try:
       # Извлечение текста из PDF
        extracted_text, image_bytes = extract_text_from_pdf(pdf_path)
        # print(extracted_text)
    
       # Извлечение текста между метками
        labels_text = extract_text_between_labels(extracted_text, 'Buyer', 'USPS TRACKING #')
        if not labels_text:
            raise ValueError("Не удалось найти текст между метками 'Buyer' и 'USPS TRACKING #'")

       # Обработка первого найденного текста
        extracted_text = re.sub(r'\bsHiP\b', '', labels_text[0], flags=re.IGNORECASE).strip()
        lines = split_text_by_newline(extracted_text)
        lines = [line for line in lines if not re.search(r'\s*@', line)]
        print(lines)
        if len(lines) < 3:
            raise ValueError("Ожидалось, что в тексте будет минимум 3 строки.")

        name = lines[0].strip()
        address_match = re.search(r':\s*(.*)', lines[1])
        address = address_match.group(1).strip() if address_match else lines[1].strip()
        city = lines[2].strip()
       # Создание объекта с данными
        people = SimpleNamespace(
            name=name,
            address=address,
            city=city,
            validation = True,
            images=image_bytes
        )
        full_address = f"{address}, {city}"
        print(f'Adrress {full_address}')
        if not validate_address(full_address, auth_id, auth_token):
            people.validation = False
       # Сохранение текста в файл
        # save_text_to_file(str(people), output_file)
        return people
        # print(f"Текст извлечен и сохранен в файл: {output_file}")

    except Exception as e:
        print(f"Произошла ошибка: {e}")

def validate_address(address, auth_id, auth_token):
   """Проверяет корректность адреса с использованием SmartyStreets API."""
   url = "https://us-street.api.smartystreets.com/street-address"
   params = {
       'auth-id': auth_id,
       'auth-token': auth_token,
       'street': address
   }
   
   try:
       response = requests.get(url, params=params)
       response.raise_for_status()
       data = response.json()
       print(data)
       if data:
           for result in data:
               # Печатаем отформатированный адрес и дополнительные данные
                formatted_address = result.get('delivery_line_1', '') + ' ' + result.get('delivery_line_2', '')
                formatted_address += ', ' + result.get('last_line', '').strip()
                print(f"Адрес проверен: {formatted_address}")
                return True
       else:
           print("Адрес не найден.")
           return False

   except requests.RequestException as e:
       print(f"Ошибка запроса: {e}")
       return False

def process_all_pdfs_in_directory(directory_path, auth_id, auth_token):
    """Обрабатывает все PDF-файлы в указанной директории."""
    results = []
    
    # Получаем список всех PDF-файлов в директории
    pdf_files = [f for f in os.listdir(directory_path) if f.endswith('.pdf')]

    for pdf_file in pdf_files:
        pdf_path = os.path.join(directory_path, pdf_file)
        print(f"Обработка файла: {pdf_file}")
        try:
            # Извлекаем данные из PDF
            result = gather_and_validate_adrress(pdf_path, auth_id, auth_token)
            if result:
                results.append(result)
        except Exception as e:
            print(f"Ошибка при обработке файла {pdf_file}: {e}")
    
    return results

   
if __name__ == "__main__":
     # Файл для сохранения извлеченного текста
    directory_path = 'download'
    auth_id = '4764b878-fe6b-8431-2bd2-5df1f7466607'  # Ваш Auth ID для SmartyStreets API
    auth_token = 'Xb7qgRPNT7LPKMAtJ4kr'  # Ваш Auth Token для SmartyStreets API
    # results = process_all_pdfs_in_directory(directory_path, auth_id, auth_token)

    # for result in results:
    #     print(f"Результат: Имя: {result.name}, Адрес: {result.address}, Город: {result.city}")
    res = gather_and_validate_adrress('download/66aff4d037521881d42c1d6a.pdf', auth_id, auth_token)
    print(res)