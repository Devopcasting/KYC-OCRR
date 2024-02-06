import re
import pytesseract
import configparser
from ocrr_log_mgmt.ocrr_log import OCRREngineLogging
from helper.passport_text_coordinates import TextCoordinates

class PassportDocumentInfo:
    def __init__(self, document_path) -> None:
        """Read config.ini"""
        config = configparser.ConfigParser(allow_no_value=True)
        config.read(r'C:\Program Files (x86)\OCRR\config\config.ini')
        self.DOCUMENT_MODE = int(config['Mode']['ShowAvailableRedaction'])

        """Logger"""
        log_config = OCRREngineLogging()
        self.logger = log_config.configure_logger()

        """Get the coordinates of all the extracted text"""
        self.coordinates = TextCoordinates(document_path).generate_text_coordinates()

        """Get the text from document"""
        tesseract_config = r'--oem 3 --psm 11'
        self.text_data = pytesseract.image_to_string(document_path, lang="eng", config=tesseract_config)
    
        """List of states"""
        self.states = ['andhra pradesh', 'arunachal pradesh', 'assam', 'bihar', 'chandigarh (ut)', 
                       'chhattisgarh', 'dadra and nagar haveli (ut)', 'daman and diu (ut)', 'delhi (nct)', 
                       'goa', 'gujarat', 'haryana', 'himachal pradesh', 'jammu and kashmir', 'jharkhand', 
                       'karnataka', 'kerala', 'lakshadweep (ut)', 'madhya pradesh', 'maharashtra', 'manipur', 
                       'meghalaya', 'mizoram', 'nagaland', 'odisha', 'puducherry (ut)', 'punjab', 'rajasthan', 
                       'sikkim', 'tamil nadu', 'telangana', 'tripura', 'uttarakhand', 'uttar pradesh', 'mumbai']
    
    """func: extract passport number"""
    def extract_passport_number(self):
        result =  {}
        passport_number = ""
        matching_line_index_top = None
        matching_line_index_bottom = None
        matching_passport_text = None
        matching_text_regex = r"passport"
        matching_passport_number_coords_top = []
        matching_passport_number_coords_bottom = []

        """find matching text index"""
        for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates):
            if re.search(matching_text_regex, text.lower(), flags=re.IGNORECASE):
                matching_line_index_top = i
                break
        if matching_line_index_top is None:
            return result
        
        """get the top passport number coordinates"""
        for i in range(matching_line_index_top, len(self.coordinates)):
            text = self.coordinates[i][4]
            if len(text) == 8 and text.isupper() and text.isalnum():
                matching_passport_number_coords_top = [self.coordinates[i][0], self.coordinates[i][1],
                                         self.coordinates[i][2], self.coordinates[i][3]]
                matching_line_index_bottom = i
                matching_passport_text = text
                passport_number = text
                break
        if matching_line_index_bottom is None:
            return result
                
        """get the bottom passport number coordinates"""
        for i in range(matching_line_index_bottom + 1, len(self.coordinates)):
            text = self.coordinates[i][4]
            if matching_passport_text in text:
                 matching_passport_number_coords_bottom = [self.coordinates[i][0], self.coordinates[i][1],
                                         self.coordinates[i][2], self.coordinates[i][3]]
                 break
        if matching_passport_number_coords_bottom:
            result = {
                "Passport Number": passport_number,
                "coordinates": [matching_passport_number_coords_top, matching_passport_number_coords_bottom]
            }
        else:
            result = {
                "Passport Number": passport_number,
                "coordinates": [matching_passport_number_coords_top]
            }
        return result
    
    """func: extract dates"""
    def extract_dates(self):
        result = {}
        date_text = ""
        date_coords = []
        date_coordinates = []

        """date pattern"""
        date_pattern = r'\d{2}/\d{2}/\d{4}'

        """get the coordinates"""
        for i, (x1,y1,x2,y2,text) in enumerate(self.coordinates):
            date_match = re.search(date_pattern, text)
            if date_match:
                date_coords.append([x1, y1, x2, y2])
                date_text += " "+ text
        
        if not date_coords:
            return result
        
        """get the first 6 chars"""
        for i in date_coords:
            width = i[2] - i[0]
            date_coordinates.append([i[0], i[1], i[0] + int(0.54 * width), i[3]])
        
        result = {
            "Dates": date_text,
            "coordinates": date_coordinates
        }

        return result

    """func: extract gender"""
    def extract_gender(self):
        result = {}
        gender_text = ""
        matching_text_keyword = ['M', 'F']
        gender_coordinates = []

        """get the coordinates"""
        for i, (x1,y1,x2,y2,text) in enumerate(self.coordinates):
            if text in matching_text_keyword:
                gender_coordinates = [x1, y1, x2, y2]
                gender_text = text
                break
        if not gender_coordinates:
            return result
        
        result = {
            "Gender": gender_text,
            "coordinates": [gender_coordinates]
        }
        
        return result

    """func: extract surname"""
    def extract_surname(self):
        result = {}
        surname_text = ""
        surname_coords = []
        surname_coordinates = []
        matching_text = "Surname"

        """clean text"""
        clean_text = [i for i in self.text_data.split("\n") if len(i) != 0]

        """find the line that matches search text"""
        matching_text_index = self.__find_matching_line_index(clean_text, matching_text)
        if matching_text_index == 0:
            return result
        
        """get the next line in the text"""
        next_line_list = []
        for line in clean_text[matching_text_index + 2 :]:
            if line.lower() in 'faa ora arr /given names':
                break
            else:
                next_line_list.append(line)
        if not next_line_list:
            return result
        
        """get the coordinates"""
        for i in next_line_list:
            for k, (x1, y1, x2, y2, text) in enumerate(self.coordinates):
                if i == text:
                    surname_coords.append([x1, y1, x2, y2])
                    surname_text = text
        
        for i in surname_coords:
            width = i[2] - i[0]
            surname_coordinates.append([i[0], i[1], i[0] + int(0.40 * width), i[3]])
        
        result = {
            "Surname": surname_text,
            "coordinates": surname_coordinates
        }

        return result
    
    """func: extract given name"""
    def extract_given_name(self):
        result = {}
        given_name_text = ""
        given_name_cords = []
        given_name_coordinates = []
        matching_text = 'Names'

        """split clean text"""
        clean_text = [i for i in self.text_data.splitlines() if len(i) != 0]

        """find the line that matches the text"""
        matching_line_index = self.__find_matching_line_index(clean_text, matching_text)
        if matching_line_index == 0:
            return result
        
        """get the next line in the text"""
        next_line_list = []
        for line in clean_text[matching_line_index + 1 :]:
            if line.lower() in 'fier /sex':
                break
            else:
                next_line_list.append(line)
        if not next_line_list:
            return result
        
        """get the coordinates"""
        for i in next_line_list:
            for k, (x1, y1, x2, y2, text) in enumerate(self.coordinates):
                if i == text:
                    given_name_cords.append([x1, y1, x2, y2])
                    given_name_text += " "+text
        
        for i in given_name_cords:
            width = i[2] - i[0]
            given_name_coordinates.append([i[0], i[1], i[0] + int(0.40 * width), i[3]])
        
        result = {
            "Given Name": given_name_text,
            "coordinates": given_name_coordinates
        }

        return result

    """func: extract father name"""
    def extract_father_name(self):
        result = {}
        father_name_text = ""
        matching_text = "Father"
        father_name_coords = []
        father_name_coordinates = []

        """split clean text"""
        clean_text = [i for i in self.text_data.splitlines() if len(i) != 0]

        """find the line that matches the text"""
        matching_line_index = self.__find_matching_line_index(clean_text, matching_text)
        if matching_line_index == 0:
            return result
        
        """get the next line in the text"""
        next_line_list = []
        for line in clean_text[matching_line_index + 1 :]:
            if "mother" in line.lower():
                break
            else:
                next_line_list.extend(line.split())
        if not next_line_list:
            return result
        
        """get the coordinates"""
        if len(next_line_list) > 1:
            next_line_list = next_line_list[:-1]

        for i in next_line_list:
            for k, (x1, y1, x2, y2, text) in enumerate(self.coordinates):
                if i == text:
                    father_name_coords.append([x1, y1, x2, y2])
                    father_name_text += " "+text
                if len(next_line_list) == len(father_name_coords):
                    break
        
        for i in father_name_coords:
            width = i[2] - i[0]
            father_name_coordinates.append([i[0], i[1], i[0] + int(0.40 * width), i[3]])
        
        result = {
            "Father Name": father_name_text,
            "coordinates": father_name_coordinates
        }

        return result

    """func: extract mother name"""
    def extract_mother_name(self):
        result = {}
        matching_text = "Mother"
        mother_coords = []
        mother_text = ""
        mother_coordinates = []

        """split clean text"""
        clean_text = [i for i in self.text_data.splitlines() if len(i) != 0]

        # find the line that matches search text
        matching_line_index = self.__find_matching_line_index(clean_text, matching_text)
        if matching_line_index == 0:
            return result
        
        """get the next line in the text"""
        next_line_list = []
        for line in clean_text[matching_line_index + 1 :]:
            if "af ar of a ora /name of spouse" in line.lower():
                break
            else:
                next_line_list.extend(line.split())
        if not next_line_list:
            return result
        
        """get the coordinates"""
        if len(next_line_list) > 1:
            next_line_list = next_line_list[:-1]

        for i in next_line_list:
            for k, (x1, y1, x2, y2, text) in enumerate(self.coordinates):
                if i == text:
                    mother_coords.append([x1, y1, x2, y2])
                    mother_text += " "+text
                if len(next_line_list) == len(mother_coords):
                    break
        
        for i in mother_coords:
            width = i[2] - i[0]
            mother_coordinates.append([i[0], i[1], i[0] + int(0.40 * width), i[3]])
        
        result = {
            "Mother Name": mother_text,
            "coordinates": mother_coordinates
        }

        return result
    
    """func: extract ind-name"""
    def extract_ind_name(self):
        result = {}
        ind_name_text = ""
        ind_name_cords = []
        ind_name_coordinates = []
        matching_text = 'IND'

        """get the coordinates"""
        for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates):
            if "IND" in text and '<' in text:
                ind_name_cords.append([x1, y1, x2, y2])
                ind_name_text += " "+text
                break
        if not ind_name_cords:
            return result
        if len(ind_name_cords) > 1:
            ind_name_cords = ind_name_cords[:-1]

        for i in ind_name_cords:
             width = i[2] - i[0]
             ind_name_coordinates.append([i[0], i[1], i[0] + int(0.40 * width), i[3]])
        
        result = {
            "IND Name": ind_name_text,
            "coordinates": ind_name_coordinates
        }
        return result

    """func: extract pincode"""
    def extract_pincode(self):
        result = {}
        pincode_number = ""
        pincode_coordinates = []
        pincode_coords = []

        """get the coordinates"""
        for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates):
            if len(text) == 6 and text.isdigit():
                pincode_coords.append([x1, y1, x2, y2])
                pincode_number += " "+text
                break
        
        for i in pincode_coords:
            width = i[2] - i[0]
            pincode_coordinates.append([i[0], i[1], i[0] + int(0.30 * width), i[3]])
        
        result = {
            "Pincode": pincode_number,
            "coordinates": pincode_coordinates
        }

        return result
    
    """func: extract state"""
    def extract_state(self):
        result = {}
        state_name = ""
        state_coordinates = []

        """get the coordinates"""
        for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates):
            if text.lower() in self.states:
                state_coordinates.append([x1, y1, x2, y2])
                state_name = text
        
        result = {
            "State": state_name,
            "coordinates": state_coordinates
        }

        return result
    
    def __find_matching_line_index(self, lines: list, matching_text: str ) -> int:
        # find the line that matches search text
        for i,line in enumerate(lines):
            if matching_text in line:
                return i
        return 0

    """func: collect passport info"""
    def collect_passport_info(self) -> dict:
        passport_doc_info_list = []

        """Check Document mode"""
        if self.DOCUMENT_MODE == 1:

            """Collect: Passport Number"""
            passport_number = self.extract_passport_number()
            if passport_number:
                passport_doc_info_list.append(passport_number)
            else:
                self.logger.error("| Passport number not found")
            
            """Collect: Dates"""
            passport_dates = self.extract_dates()
            if passport_dates:
                passport_doc_info_list.append(passport_dates)
            else:
                self.logger.error("| Passport dates not found")
            
            """Collect: Gender"""
            gender = self.extract_gender()
            if gender:
                passport_doc_info_list.append(gender)
            else:
                self.logger.error("| Passport gender not found")
            
            """Collect: Surname"""
            surname = self.extract_surname()
            if surname:
                passport_doc_info_list.append(surname)
            else:
                self.logger.error("| Passport surname not found")
            
            """Collect: Given name"""
            given_name = self.extract_given_name()
            if given_name:
                passport_doc_info_list.append(given_name)
            else:
                self.logger.error("| Passport given name not found")
            
            """Collect: Father's name"""
            father_name = self.extract_father_name()
            if father_name:
                passport_doc_info_list.append(father_name)
            else:
                self.logger.error("| Passport father's name not found")
            
            """Collect: Mother's name"""
            mother_name = self.extract_mother_name()
            if mother_name:
                passport_doc_info_list.append(mother_name)
            else:
                self.logger.error("| Passport mother name not found")
            
            """Collect: IND name"""
            ind_name = self.extract_ind_name()
            if ind_name:
                passport_doc_info_list.append(ind_name)
            else:
                self.logger.error("| Passport IND name not found")
            
            """Collect: Pincode"""
            pincode_number = self.extract_pincode()
            if pincode_number:
                passport_doc_info_list.append(pincode_number)
            else:
                self.logger.error("| Passport Pincode number not found")
            
            """Collect: State"""
            state = self.extract_state()
            if state:
                passport_doc_info_list.append(state)
            else:
                self.logger.error("| Passport State name not found")
            
            """check passport_doc_info_list"""
            if len(passport_doc_info_list) == 0:
                return {"message": "Unable to extract Passport information", "status": "REJECTED"}
            else:
                return {"message": "Successfully Redacted Passport Document", "status": "REDACTED", "data": passport_doc_info_list}

        else:

            """Collect: Passport Number"""
            passport_number = self.extract_passport_number()
            if not passport_number:
                self.logger.error("| Passport number not found")
                return {"message": "Unable to extract passport number", "status": "REJECTED"}
            passport_doc_info_list.append(passport_number)
 
            """Collect: Dates"""
            passport_dates = self.extract_dates()
            if not passport_dates:
                self.logger.error("| Passport dates not found")
                return {"message": "Unable to extract dates from passport document", "status": "REJECTED"}
            passport_doc_info_list.append(passport_dates)
        
            """Collect: Gender"""
            gender = self.extract_gender()
            if not gender:
                self.logger.error("| Passport gender not found")
                return {"message": "Unable to extract gender from passport", "status": "REJECTED"}
            passport_doc_info_list.append(gender)

            """Collect: Surname"""
            surname = self.extract_surname()
            if not surname:
                self.logger.error("| Passport surname not found")
                return {"message": "Unable to extract surname from passport document", "status": "REJECTED"}
            passport_doc_info_list.append(surname)

            """Collect: Given name"""
            given_name = self.extract_given_name()
            if not given_name:
                self.logger.error("| Passport given name not found")
                return {"message": "Unable to extract given name from passport", "status": "REJECTED"}
            passport_doc_info_list.append(given_name)

            """Collect: Father's name"""
            father_name = self.extract_father_name()
            if not father_name:
                self.logger.error("| Passport father's name not found")
                return {"message": "Unable to extract father's name from passport", "status": "REJECTED"}
            passport_doc_info_list.append(father_name)

            """Collect: Mother's name"""
            mother_name = self.extract_mother_name()
            if not mother_name:
                self.logger.error("| Passport mother name not found")
                return {"message": "Unable to extract mother name", "status": "REJECTED"}
            passport_doc_info_list.append(mother_name)

            """Collect: IND name"""
            ind_name = self.extract_ind_name()
            if not ind_name:
                self.logger.error("| Passport IND name not found")
                return {"message": "Unable to extract IND name from Passport", "status": "REJECTED"}
            passport_doc_info_list.append(ind_name)

            """Collect: Pincode"""
            pincode_number = self.extract_pincode()
            if pincode_number:
                passport_doc_info_list.append(pincode_number)

            """Collect: State"""
            state = self.extract_state()
            if state:
                passport_doc_info_list.append(state)

            return {"message": "Successfully Redacted Passport Document", "status": "REDACTED", "data": passport_doc_info_list}
