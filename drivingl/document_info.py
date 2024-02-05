import pytesseract
import re
from ocrr_log_mgmt.ocrr_log import OCRREngineLogging
from helper.dl_text_coordinates import TextCoordinates

class DrivingLicenseDocumentInfo:
    def __init__(self, document_path) -> None:
        """Logger"""
        log_config = OCRREngineLogging()
        self.logger = log_config.configure_logger()

        """Get the coordinates of all the extracted text"""
        self.coordinates = TextCoordinates(document_path).generate_text_coordinates()

        """Get the text from document"""
        self.text_data = pytesseract.image_to_string(document_path, lang="eng")

        """List of states"""
        self.states = ['andhra pradesh', 'arunachal pradesh', 'assam', 'bihar', 'chandigarh (ut)', 
                       'chhattisgarh', 'dadra and nagar haveli (ut)', 'daman and diu (ut)', 'delhi (nct)', 
                       'goa', 'gujarat', 'haryana', 'himachal pradesh', 'jammu and kashmir', 'jharkhand', 
                       'karnataka', 'kerala', 'lakshadweep (ut)', 'madhya pradesh', 'maharashtra', 'manipur', 
                       'meghalaya', 'mizoram', 'nagaland', 'odisha', 'puducherry (ut)', 'punjab', 'rajasthan', 
                       'sikkim', 'tamil nadu', 'telangana', 'tripura', 'uttarakhand', 'uttar pradesh', 'mumbai', 'thane']
    

    """func: extract driving license number"""
    def extract_dl_number(self):
        result = {}
        dl_number = ""
        dl_number_coordinated = []

        """get the coordinates"""
        for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates):
            if len(text) == 11 and text.isdigit():
                dl_number = text
                dl_number_coordinated.append([x1, y1, x2, y2])
                break
        if not dl_number_coordinated:
            return result
        
        result = {
            "Driving License Number": dl_number,
            "coordinates": dl_number_coordinated
        }

        return result
    
    """func: extract dates"""
    def extract_dates(self):
        result = {}
        date_text = ""
        date_coords = []
        date_coordinates = []

        """date pattern"""
        date_pattern = r'\d{2}/\d{2}/\d{4}|\d{2}-\d{2}-\d{4}'

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
    
    """func: extract name"""
    def extract_name(self):
        result = {}
        name_text = ""
        name_coords = []
        matching_text = r"\b(?:name)\b"
        matching_text_index = 0

        """get matching text index"""
        for i,(x1, y1, x2, y2, text) in enumerate(self.coordinates):
            if re.search(matching_text, text.lower(), flags=re.IGNORECASE):
                matching_text_index = i
                break
        
        """get the coordinates"""
        for i in range(matching_text_index + 1, len(self.coordinates)):
            text = self.coordinates[i][4]
            if text.lower() in ['s/dmw', 'dmw', 's/']:
                break
            name_coords.append([x1, y1, x2, y2])
            name_text += " "+text
        
        if len(name_coords) > 1:
            result = {
                "Name": name_text,
                "coordinates": [[name_coords[0][0], name_coords[0][1], name_coords[-1][2], name_coords[-1][3]]]
            }
        else:
            result = {
                "Name": name_text,
                "coordinates": [[name_coords[0][0], name_coords[0][1], name_coords[0][2], name_coords[0][3]]]
            }
        
        return result
    
    """func: collect DL information"""
    def collect_dl_info(self):
        dl_card_info_list = []

        """Collect DL number"""
        dl_number = self.extract_dl_number()
        if not dl_number:
            self.logger.error("| Driving license number not found")
            return {"message": "Unable to extract driving license number", "status": "REJECTED"}
        dl_card_info_list.append(dl_number)

        """Collect DL dates"""
        dl_dates = self.extract_dates()
        if dl_dates:
            dl_card_info_list.append(dl_dates)
        
        """Collect DL pincode"""
        dl_pincode = self.extract_pincode()
        if dl_pincode:
            dl_card_info_list.append(dl_pincode)

        """Collect DL State"""
        dl_state = self.extract_state()
        if dl_state:
            dl_card_info_list.append(dl_state)

        """Collect DL name"""
        dl_name = self.extract_name()
        if dl_name:
            dl_card_info_list.append(dl_name)

        print(dl_card_info_list)
        return {"message": "Successfully Redacted Driving License Document", "status": "REDACTED", "data": dl_card_info_list}