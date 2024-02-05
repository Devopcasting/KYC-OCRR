import re

class IdentifyAadhaarCard:
    def __init__(self, clean_text: list) -> None:
        self.clean_text = clean_text
         # Regular expression pattern for PAN card identifiers
        self.eaashaarcard_regex = r"\b(?:enrollment|enrolment|enroliment|/enrolment)\b"
    
    def check_e_aadhaar_card(self):
        for text in self.clean_text:
            if re.search(self.eaashaarcard_regex, text, flags=re.IGNORECASE):
                return True
        return False