import re
import pytesseract
from ocrr_log_mgmt.ocrr_log import OCRREngineLogging
from helper.pancard_text_coordinates import TextCoordinates
from pancard.pattern2 import PanCardPattern2
from pancard.pattern1 import PanCardPattern1

class PancardDocumentInfo:
    def __init__(self, document_path: str) -> None:
        """Logger"""
        log_config = OCRREngineLogging()
        self.logger = log_config.configure_logger()

        """Get the coordinates of all the extracted text"""
        self.coordinates = TextCoordinates(document_path).generate_text_coordinates()

        """Get the text from document"""
        tesseract_config = r'--oem 3 --psm 11'
        self.text_data = pytesseract.image_to_string(document_path, lang="eng", config=tesseract_config)
    
    """func: extract pancard number"""
    def extract_pancard_number(self) -> dict:
        result = {}
        pancard_text = ""
        pancard_coordinates = []
        matching_text_index = None
        matching_text_regex = r"\b(?:permanent|pe@fanent|pe@ffignent|pertianent|account|number|card|perenent|accoun|pormanent)\b"

        """find matching text pattern"""
        for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates):
            if re.search(matching_text_regex, text.lower(), flags=re.IGNORECASE):
                matching_text_index = i
                break

        if matching_text_index is None:
            """find pancard number without matching pattern text"""
            for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates):
                if len(text) == 10 and text.isupper() and text.isalnum():
                    pancard_coordinates = [x1, y1, x2, y2]
                    pancard_text = text
                    break
                elif len(text) == 10 and text.isalnum():
                    pancard_coordinates = [x1, y1, x2, y2]
                    pancard_text = text.capitalize
                    break          
        else:
            """find pancard using matching pattern text index"""
            for i in range(matching_text_index,  len(self.coordinates)):
                text = self.coordinates[i][4]
                if len(text) == 10 and text.isupper() and text.isalnum():
                    pancard_coordinates = [self.coordinates[i][0], self.coordinates[i][1], self.coordinates[i][2], self.coordinates[i][3]]
                    pancard_text = text
                    break
                elif len(text) == 10 and text.isalnum():
                    pancard_coordinates = [self.coordinates[i][0], self.coordinates[i][1], self.coordinates[i][2], self.coordinates[i][3]]
                    pancard_text = text.capitalize
                    break

        if not pancard_coordinates:
            return result
        
        width = pancard_coordinates[2] - pancard_coordinates[0]
        result = {
            "PancardNumber": pancard_text,
            "coordinates": [[pancard_coordinates[0], pancard_coordinates[1], 
                       pancard_coordinates[0] + int(0.65 * width),pancard_coordinates[3]]]
        }
        return result


    """func: extract dob"""
    def extract_dob(self):
        result = {}
        dob_text = ""
        dob_coordinates = []

        """Data patterns: DD/MM/YYY, DD-MM-YYY"""
        date_pattern = r'\d{2}/\d{2}/\d{4}|\d{2}-\d{2}-\d{4}'

        for i, (x1, y1, x2, y2, text) in enumerate(self.coordinates):
            match = re.search(date_pattern, text)
            if match:
                dob_coordinates = [x1, y1, x2, y2]
                dob_text = text
                break
        if not dob_coordinates:
            return result
        
        """Get first 6 chars"""
        width = dob_coordinates[2] - dob_coordinates[0]
        result = {
            "DOB": dob_text,
            "coordinates": [[dob_coordinates[0], dob_coordinates[1], dob_coordinates[0] + int(0.54 * width), dob_coordinates[3]]]
        }
        return result

    """func: identify pancard pattern"""
    def identify_pancard_pattern(self) -> int:
        pancard_pattern_keyword_search = ["name", "father's", "father", "/eather's", "uiname"]
        for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates):
            if text.lower() in pancard_pattern_keyword_search:
                return 1
        return 2


    """func: collect pancard information"""
    def collect_pancard_info(self) -> dict:
        pancard_doc_info_list = []

        """Collect: Pancard Number"""
        pancard_number = self.extract_pancard_number()
        if not pancard_number:
            self.logger.error("| Pancard Number not found")
            return {"message": "Unable to extract Pancard Number", "status": "REJECTED"}
        pancard_doc_info_list.append(pancard_number)

        """Collect: DOB"""
        dob = self.extract_dob()
        if not dob:
            self.logger.error("| Pancard DOB not found")
            return {"message": "Unable to extract DOB from Pancard Document", "status": "REJECTED"}
        pancard_doc_info_list.append(dob)

        """Collect: Pancard username and father's name"""
        pattern_number = self.identify_pancard_pattern()
        if pattern_number == 1:
            matching_text_keyword_username = ["name", "uiname"]
            matching_text_keyword_fathername = ["father's name", "father", "/eather's"]
        
            username_p1 = PanCardPattern1(self.coordinates, self.text_data, matching_text_keyword_username, 1).extract_username_fathername_p1()
            fathername_p1 = PanCardPattern1(self.coordinates, self.text_data, matching_text_keyword_fathername, 2).extract_username_fathername_p1()
            
            if username_p1 and fathername_p1:
                pancard_doc_info_list.append(username_p1)
                pancard_doc_info_list.append(fathername_p1)
            else:
                self.logger.error("| Pancard Username or Father name not found")
                return {"message": "Unable to extract Username or Father's name from Pancard document", "status": "REJECTED"}
        else:
            username_p2 = PanCardPattern2(self.coordinates, self.text_data, 1).extract_username_p2()
            fathername_p2 = PanCardPattern2(self.coordinates, self.text_data, 2).extract_fathername_p2()

            if username_p2 and fathername_p2:
                pancard_doc_info_list.append(username_p2)
                pancard_doc_info_list.append(fathername_p2)
            else:
                self.logger.error("| Pancard Username or Father name not found")
                return {"message": "Unable to extract Username or Father's name from Pancard document", "status": "REJECTED"}

        return {"message": "Successfully Redacted PAN Card Document", "status": "REDACTED", "data": pancard_doc_info_list}