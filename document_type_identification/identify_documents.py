import pytesseract
from pancard.identify_pancard import IdentifyPanCard
from aadhaarcard.identify_aadhaarcard import IdentifyAadhaarCard
from passport.identify_passport import IdentifyPassport
from drivingl.identify_dl import IdentifyDrivingLicense
from check_img_rgb.image_rgb import CheckImageRGB
from helper.clean_text import CleanText

class DocumentTypeIdentification:
    def __init__(self, document_path: str) -> None:

        if CheckImageRGB(document_path).check_rgb_image():
            """Tesseract configuration"""
            tesseract_config = r'-l eng --oem 3'
            """Extract text from document in dictionary format"""
            data_text = pytesseract.image_to_string(document_path, output_type=pytesseract.Output.DICT, config=tesseract_config)
        else:
            tesseract_config = r'-l eng --oem 3 --psm 11'
            """Extract text from document in dictionary format"""
            data_text = pytesseract.image_to_string(document_path, output_type=pytesseract.Output.DICT, config=tesseract_config)
            
        
        """Clean the extracted text"""
        clean_text_data = CleanText(data_text).clean_text()

        """Pancard identification object"""
        self.pancard_obj = IdentifyPanCard(clean_text_data)

        """E-Aadhaarcard identification object"""
        self.aadhaarcard_obj = IdentifyAadhaarCard(clean_text_data)

        """Passport identification object"""
        self.passport_obj = IdentifyPassport(clean_text_data)

        """Driving License Object"""
        self.driving_license_obj = IdentifyDrivingLicense(clean_text_data)
    
    def identify_pancard(self) -> bool:
        if self.pancard_obj.check_pan_card():
            return True
        return False
    
    def identify_eaadhaarcard(self) -> bool:
        if self.aadhaarcard_obj.check_e_aadhaar_card():
            return True
        return False
    
    def identify_aadhaarcard_format(self) -> bool:
        if self.aadhaarcard_obj.check_aadhaar_card_format():
            return True
        return False
    
    def identify_aadhaar_card(self) -> bool:
        if self.aadhaarcard_obj.check_aadhaarcard():
            return True
        return False
    
    def identify_passport(self) -> bool:
        if self.passport_obj.check_passport():
            return True
        return False
    
    def identify_dl(self) -> bool:
        if self.driving_license_obj.check_dl():
            return True
        return False