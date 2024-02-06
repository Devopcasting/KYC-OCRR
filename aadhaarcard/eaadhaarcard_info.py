import pytesseract
import configparser
import re
from ocrr_log_mgmt.ocrr_log import OCRREngineLogging
from helper.eaadhaarcard_text_coordinates import TextCoordinates

class EaadhaarCardInfo:
    def __init__(self, document_path: str) -> None:
        """Read config.ini"""
        config = configparser.ConfigParser(allow_no_value=True)
        config.read(r'C:\Program Files (x86)\OCRR\config\config.ini')
        self.DOCUMENT_MODE = int(config['Mode']['ShowAvailableRedaction'])

        """Logger"""
        log_config = OCRREngineLogging()
        self.logger = log_config.configure_logger()

        self.coordinates_default = TextCoordinates(document_path, lang_type="default").generate_text_coordinates()
        self.coordinates_regional = TextCoordinates(document_path, lang_type="regional").generate_text_coordinates()
        self.coordinates = TextCoordinates(document_path).generate_text_coordinates()
        
        self.text_data_default = pytesseract.image_to_string(document_path)
        self.text_data_regional = pytesseract.image_to_string(document_path, lang="hin+eng")

        self.states = ['andhra pradesh', 'arunachal pradesh', 'assam', 'bihar', 'chandigarh (ut)', 
                       'chhattisgarh', 'dadra and nagar haveli (ut)', 'daman and diu (ut)', 'delhi (nct)', 
                       'goa', 'gujarat', 'haryana', 'himachal pradesh', 'jammu and kashmir', 'jharkhand', 
                       'karnataka', 'kerala', 'lakshadweep (ut)', 'madhya pradesh', 'maharashtra', 'manipur', 
                       'meghalaya', 'mizoram', 'nagaland', 'odisha', 'puducherry (ut)', 'punjab', 'rajasthan', 
                       'sikkim', 'tamil nadu', 'telangana', 'tripura', 'uttarakhand', 'uttar pradesh', 'bangalore']
    
    """func: extract dob"""
    def extract_dob(self) -> dict:
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
            return result
        
        """Get first 6 chars"""
        width = dob_coordinates[2] - dob_coordinates[0]
        result = {
            "DOB": dob_text,
            "coordinates": [[dob_coordinates[0], dob_coordinates[1], dob_coordinates[0] + int(0.54 * width), dob_coordinates[3]]]
        }
        return result

    """func: extract gender"""
    def extract_gender(self):
        result = {}
        gender_text = ""
        gender_coordinates = []

        """get the index number of Male/Female"""
        matching_index = 0
        for i ,(x1,y1,x2,y2,text) in enumerate(self.coordinates_default):
            if text.lower() in ["male", "female"]:
                matching_index = i
                gender_text = text
                break
        if matching_index == 0:
            return result
        
        """reverse loop from Male/Female index until DOB comes"""
        for i in range(matching_index, -1, -1):
            if re.match(r'^\d{2}/\d{2}/\d{4}$', self.coordinates_default[i][4]) or re.match(r'^\d{4}$', self.coordinates_default[i][4]):
                break
            else:
                gender_coordinates.append([self.coordinates_default[i][0], self.coordinates_default[i][1], 
                                           self.coordinates_default[i][2], self.coordinates_default[i][3]])
        
        result = {
            "Gender": gender_text,
            "coordinates": [[gender_coordinates[-1][0], gender_coordinates[-1][1], gender_coordinates[0][2], gender_coordinates[0][3]]]
        }

        return result

    """func: extract aadhaar card number"""
    def extract_aadhaarcard_number(self):
        result = {}
        aadhaarcard_text = ""
        aadhaarcard_coordinates = []
        text_coordinates = []

        """get the index of male/female"""
        matching_index = 0
        for i,(x1,y1,x2,y2,text) in enumerate(self.coordinates):
            if text.lower() in ["male", "female"]:
                matching_index = i
        if matching_index == 0:
            return result
        
        """get the coordinates of aadhaar card number"""
        for i in range(matching_index, len(self.coordinates)):
            text = self.coordinates[i][4]
            if len(text) == 4 and text.isdigit() and text[:2] != '19':
                text_coordinates.append((text))
                aadhaarcard_text += ' '+ text
            if len(text_coordinates) == 3:
                break
        
        for i in text_coordinates[:-1]:
            for k,(x1,y1,x2,y2,text) in enumerate(self.coordinates):
                if i in text:
                    aadhaarcard_coordinates.append([x1, y1, x2, y2])
        result = {
            "Aadhaar Card Number": aadhaarcard_text,
            "coordinates": aadhaarcard_coordinates
        }
        return result


    """func: extract name in english"""
    def extract_name_in_english(self):
        result = {}
        name_coordinates = []

        """get clean text list"""
        clean_text = [i for i in self.text_data_default.split("\n") if len(i) != 0]

        """get the above matching text"""
        matching_text = []
        for i,text in enumerate(clean_text):
            if "dob" in text.lower() or "birth" in text.lower() or "bith" in text.lower() or "year" in text.lower() or "binh" in text.lower():
                matching_text = clean_text[i - 1].split()
                break
        if not matching_text:
            return result
        clean_matching_text = [i for i in matching_text if i.isalpha()]

        if len(clean_matching_text) > 1:
            clean_matching_text = clean_matching_text[:-1]
        
        for i, (x1, y1, x2, y2, text) in enumerate(self.coordinates):
            if text in clean_matching_text:
                name_coordinates.append([x1, y1, x2, y2])
        
        result = {
            "Name": " ".join(clean_matching_text),
            "coordinates": name_coordinates
        }
        
        return result
    
    """func: extract name in regional language"""
    def extract_name_in_regional(self):
        result = {}
        name_coordinates = []

        """get clean text list"""
        clean_text = [i for i in self.text_data_regional.split("\n") if len(i) != 0]

        """get the above matching text"""
        matching_text = []
        keywords_regex = r"\b(?:dob|birth|bith|year|binh|008)\b"
        for i,text in enumerate(clean_text):
            if re.search(keywords_regex, text.lower(), flags=re.IGNORECASE):
                matching_text = clean_text[i - 2].split()
                break
        if not matching_text:
            return result
        
        if len(matching_text) > 1:
            matching_text = matching_text[:-1]
        
        for i, (x1, y1, x2, y2, text) in enumerate(self.coordinates_regional):
            if text in matching_text:
                name_coordinates.append([x1, y1, x2, y2])
        
        result = {
            "Name": " ".join(matching_text),
            "coordinates": name_coordinates
        }

        return result


    """func: extract mobile number"""
    def extract_mobile_number(self):
        result = {}
        mobile_number = ""
        mobile_coordinates = []

        """get the coordinates"""
        for i,(x1, y1, x2, y2,text) in enumerate(self.coordinates):
            if len(text) == 10 and text.isdigit():
                mobile_coordinates = [x1, y1, x2, y2]
                mobile_number = text
                break
        if not mobile_coordinates:
            return result
        
        """get first 6 chars"""
        width = mobile_coordinates[2] - mobile_coordinates[0]
        result = {
            "Mobile Number" : mobile_number,
            "coordinates" : [[mobile_coordinates[0], mobile_coordinates[1], mobile_coordinates[0] + int(0.54 * width), mobile_coordinates[3]]]
        }
        return result

    """func: extract pin code"""
    def extract_pin_code(self):
        result = {}
        pin_code = ""
        pin_code_coordinates = []
        get_coords_result = []

        """get the coordinates"""
        for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates):
            if len(text) == 6 and text.isdigit():
                pin_code_coordinates.append([x1, y1, x2, y2])
                pin_code = text
        if not pin_code_coordinates:
            return result
        
        for i in pin_code_coordinates:
            coords_result = self.get_first_3_chars(i)
            get_coords_result.append(coords_result)
        result = {
                "Pincode": pin_code,
                "coordinates": get_coords_result
        }
        return result
    
    """"func: extract state name"""
    def extract_state_name(self):
        result = {}
        state_name = ""
        state_coordinates = []

        """get the coordinates"""
        for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates):
            if text.lower() in self.states:
                state_coordinates.append([x1, y1, x2, y2])
                state_name = text
                break
        if not state_coordinates:
            return result
        
        result = {
            "State": state_name,
            "coordinates": state_coordinates
        }

        return result

        
    """func: get first 3 chars"""
    def get_first_3_chars(self, coords: list) -> list:
        width = coords[2] - coords[0]
        result = [coords[0], coords[1], coords[0] + int(0.30 * width), coords[3]]
        return result

    """func: collect e-aadhaar card info"""
    def collect_eaadhaarcard_info(self) -> dict:
        eaadhaarcard_doc_info_list = []

        """Check Document mode"""
        if self.DOCUMENT_MODE == 1:
             
            """Collect: Name in regional"""
            name_in_regional = self.extract_name_in_regional()
            if name_in_regional:
                eaadhaarcard_doc_info_list.append(name_in_regional)
            else:
                self.logger.error("| E-Aadhaar Card Name in regional language not found")
                
            """Collect: Name in english"""
            name_in_english = self.extract_name_in_english()
            if name_in_english:
                eaadhaarcard_doc_info_list.append(name_in_english)
            else:
                self.logger.error("| E-Aadhaar Card Name in english not found")
            
            """Collect: DOB"""
            dob = self.extract_dob()
            if dob:
                eaadhaarcard_doc_info_list.append(dob)
            else:
                self.logger.error("| E-Aadhaar Card DOB not found")

            """Collect: Gender"""
            gender = self.extract_gender()
            if gender:
                eaadhaarcard_doc_info_list.append(gender)
            else:
                self.logger.error("| E-Aadhaar Card Gender not found")
            
            """Collect: Aadhaar Card Number"""
            aadhaarcard_number = self.extract_aadhaarcard_number()
            if aadhaarcard_number:
                eaadhaarcard_doc_info_list.append(aadhaarcard_number)
            else:
                self.logger.error("| E-Aadhaar Card Number not found")
            
            """Collect: Mobile Number"""
            mobile_number = self.extract_mobile_number()
            if mobile_number:
                eaadhaarcard_doc_info_list.append(mobile_number)
            else:
                self.logger.error("| E-Aadhaar Mobile Number not found")

            """Collect: Pin Code"""
            pincode = self.extract_pin_code()
            if pincode:
                eaadhaarcard_doc_info_list.append(pincode)
            else:
                self.logger.error("| E-Aadhaar Pincode not found")
            
            """Collect: State name"""
            state = self.extract_state_name()
            if state:
                eaadhaarcard_doc_info_list.append(state)
            else:
                self.logger.error("| E-Aadhaar State name not found")

            """"check eaadhaarcard_doc_info_list"""
            if len(eaadhaarcard_doc_info_list) == 0:
                return {"message": "Unable to extract E-Aadhaar information", "status": "REJECTED"}
            else:
                return {"message": "Successfully Redacted E-Aadhaar Card Document", "status": "REDACTED", "data": eaadhaarcard_doc_info_list}

        else:

            """Collect: Name in regional"""
            name_in_regional = self.extract_name_in_regional()
            if not name_in_regional:
                self.logger.error("| E-Aadhaar Card Name in regional language not found")
                return {"message": "Unable to extract name in regional from E-Aadhaar Document", "status": "REJECTED"}
            eaadhaarcard_doc_info_list.append(name_in_regional)

            """Collect: Name in english"""
            name_in_english = self.extract_name_in_english()
            if not name_in_english:
                self.logger.error("| E-Aadhaar Card Name in english not found")
                return {"message": "Unable to extract name in english from E-Aaadhaar Document", "status": "REJECTED"}
            eaadhaarcard_doc_info_list.append(name_in_english)

            """Collect: DOB"""
            dob = self.extract_dob()
            if not dob:
                self.logger.error("| E-Aadhaar Card DOB not found")
                return {"message": "Unable to extract DOB from E-Aadhaar Document", "status": "REJECTED"}
            eaadhaarcard_doc_info_list.append(dob)

            """Collect: Gender"""
            gender = self.extract_gender()
            if not gender:
                self.logger.error("| E-Aadhaar Card Gender not found")
                return {"message": "Unable to extract gender from E-Aadhaar Document", "status": "REJECTED"}
            eaadhaarcard_doc_info_list.append(gender)

            """Collect: Aadhaar Card Number"""
            aadhaarcard_number = self.extract_aadhaarcard_number()
            if not aadhaarcard_number:
                self.logger.error("| E-Aadhaar Card Number not found")
                return {"message": "Unable to extract aadhaar card number", "status": "REJECTED"}
            eaadhaarcard_doc_info_list.append(aadhaarcard_number)

            """Collect: Mobile Number"""
            mobile_number = self.extract_mobile_number()
            if mobile_number:
                eaadhaarcard_doc_info_list.append(mobile_number)

            """Collect: Pin Code"""
            pincode = self.extract_pin_code()
            if pincode:
                eaadhaarcard_doc_info_list.append(pincode)
        
            return {"message": "Successfully Redacted E-Aadhaar Card Document", "status": "REDACTED", "data": eaadhaarcard_doc_info_list}
