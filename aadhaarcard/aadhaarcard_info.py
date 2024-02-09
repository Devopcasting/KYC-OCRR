import pytesseract
import configparser
import re
from ocrr_log_mgmt.ocrr_log import OCRREngineLogging
from helper.eaadhaarcard_text_coordinates import TextCoordinates

class AaadhaarCardInfo:
    def __init__(self, document_path: str) -> None:
        
        self.document_path = document_path

        """Read config.ini"""
        config = configparser.ConfigParser(allow_no_value=True)
        config.read(r'C:\Program Files (x86)\OCRR\config\config.ini')
        self.DOCUMENT_MODE = int(config['Mode']['ShowAvailableRedaction'])

        """Logger"""
        log_config = OCRREngineLogging()
        self.logger = log_config.configure_logger()

        """Get coordinates"""
        self.coordinates_default = TextCoordinates(document_path, lang_type="default").generate_text_coordinates()
        self.coordinates_regional = TextCoordinates(document_path, lang_type="regional").generate_text_coordinates()
        print(self.coordinates_regional)
        #print(self.coordinates_default)

        """Get String"""
        self.text_data_default = pytesseract.image_to_string(document_path)
        self.text_data_regional = pytesseract.image_to_string(document_path, lang="hin+eng")
        print(self.text_data_regional)
        #print(self.text_data_default)

    """func: extract DOB"""
    def extract_dob(self):
        result = {}
        dob_text = ""
        dob_coordinates = []
        
        """Data patterns: DD/MM/YYY, DD-MM-YYY"""
        date_pattern = r'\d{2}/\d{2}/\d{4}|\d{2}-\d{2}-\d{4}|\d{4}'

        for i, (x1, y1, x2, y2, text) in enumerate(self.coordinates_default):
            match = re.search(date_pattern, text)
            if match:
                dob_coordinates = [x1, y1, x2, y2]
                dob_text = text
                break
        
        if not dob_coordinates:
            result = {
                "Aadhaar DOB": " ",
                "coordinates": []
            }
            return result
        
        """Get first 6 chars"""
        width = dob_coordinates[2] - dob_coordinates[0]
        result = {
            "Aadhaar DOB": dob_text,
            "coordinates": [[dob_coordinates[0], dob_coordinates[1], dob_coordinates[0] + int(0.54 * width), dob_coordinates[3]]]
        }
        return result
    

    """func: extract Gender"""
    def extract_gender(self):
        result = {}
        gender_text = ""
        gender_coordinates = []

        gender_pattern = r"male|female"
        for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates_default):
            if re.search(gender_pattern, text, flags=re.IGNORECASE):
                gender_coordinates.append([x1, y1, x2, y2])
                gender_text = text
                break
        if not gender_coordinates:
            result = {
                "Aadhaar Gender": " ",
                "coordinates": []
            }
            return result
        result = {
            "Aadhaar Gender": gender_text,
            "coordinates": gender_coordinates
        }
        return result
    
    """func: extact aadhaar card number"""
    def extract_aadhaar_number(self):
        result = {}
        aadhaarcard_text = ""
        aadhaarcard_coordinates = []
        text_coordinates = []

        """get the index of male/female"""
        matching_index = 0
        gender_pattern = r"male|female"
        for i,(x1,y1,x2,y2,text) in enumerate(self.coordinates_default):
            if re.search(gender_pattern, text, flags=re.IGNORECASE):
                matching_index = i
        if matching_index == 0:
            result = {
                "Aadhaar Number": " ",
                "coordinates": []
            }
            return result
        
        """get the coordinates of aadhaar card number"""
        for i in range(matching_index, len(self.coordinates_default)):
            text = self.coordinates_default[i][4]
            if len(text) == 4 and text.isdigit() and text[:2] != '19':
                text_coordinates.append((text))
                aadhaarcard_text += ' '+ text
            if len(text_coordinates) == 3:
                break
        
        for i in text_coordinates[:-1]:
            for k,(x1,y1,x2,y2,text) in enumerate(self.coordinates_default):
                if i in text:
                    aadhaarcard_coordinates.append([x1, y1, x2, y2])
        result = {
            "Aadhaar Number": aadhaarcard_text,
            "coordinates": aadhaarcard_coordinates
        }
        return result

    """func: collect aadhaar card info"""
    def collect_aadhaarcard_info(self) -> dict:
        aadhaarcard_doc_info_list = []

        """Check Document mode"""
        if self.DOCUMENT_MODE == 1:

            """Collect: DOB"""
            dob = self.extract_dob()
            if len(dob['coordinates']) != 0:
                aadhaarcard_doc_info_list.append(dob)
            else:
                aadhaarcard_doc_info_list.append(dob)
                self.logger.error("| Aadhaar Card DOB not found")

            """Collect: Gender"""
            gender = self.extract_gender()
            if len(gender['coordinates']) != 0:
                aadhaarcard_doc_info_list.append(gender)
            else:
                self.logger.error("| Aadhaar Card Gender not found")
                aadhaarcard_doc_info_list.append(gender)

            """Collect: Aadhaar card number"""
            aadhaar_card_number = self.extract_aadhaar_number()
            if len(aadhaar_card_number['coordinates']) != 0:
                aadhaarcard_doc_info_list.append(aadhaar_card_number)
            else:
                self.logger.error("| Aadhaar Card Number not found")
                aadhaarcard_doc_info_list.append(aadhaar_card_number)


            print(aadhaarcard_doc_info_list)
            """"check eaadhaarcard_doc_info_list"""
            if len(aadhaarcard_doc_info_list) == 0:
                return {"message": "Unable to extract Aadhaar information", "status": "REJECTED"}
            else:
                return {"message": "Successfully Redacted Aadhaar Card Document", "status": "REDACTED", "data": aadhaarcard_doc_info_list}

        else:
            """Collect: DOB"""
            dob = self.extract_dob()
            if len(dob['coordinates']) != 0:
                aadhaarcard_doc_info_list.append(dob)
            else:
                self.logger.error("| Aadhaar Card DOB not found")
                return {"message": "Unable to extract DOB from Aadhaar Document", "status": "REJECTED"}

            """Collect: Gender"""
            gender = self.extract_gender()
            if len(gender['coordinates']) != 0:
                aadhaarcard_doc_info_list.append(gender)
            else:
                self.logger.error("| Aadhaar Card Gender not found")
                return {"message": "Unable to extract Gender from Aadhaar Document", "status": "REJECTED"}

            """Collect: Aadhaar card number"""
            aadhaar_card_number = self.extract_aadhaar_number()
            if len(aadhaar_card_number["coordinates"]) != 0:
                aadhaarcard_doc_info_list.append(aadhaar_card_number)
            else:
                self.logger.error("| Aadhaar Card Number not found")
                return {"message": "Unable to extract Aadhaar Number", "status": "REJECTED"}

            print(aadhaarcard_doc_info_list)
           
            return {"message": "Successfully Redacted Aadhaar Card Document", "status": "REDACTED", "data": aadhaarcard_doc_info_list}


