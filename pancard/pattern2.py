import re

class PanCardPattern2:
    def __init__(self,  coordinates, text, index_num) -> None:
        self.coordinates = coordinates
        self.text = text
        self.index_num = index_num
        if self.index_num == 1:
            self.LABEL_NAME = "Name"
        else:
            self.LABEL_NAME = "Father's Name"

    """func: extract username"""
    def extract_username_p2(self):
        result = {}
        matching_text_coords = []

        matching_text_keyword = ["GOVT. OF INDIA"," GOVT.", "INDIA", "INCOME", "TAX", "DEPARTMENT"]

        """split the text into lines"""
        lines = [i for i in self.text.splitlines() if len(i) != 0]

        """find the matching text index"""
        matching_text_index = self.__find_matching_text_index_username(lines, matching_text_keyword)
        if matching_text_index == 404:
            return result
        
        """get the next line of matching index"""
        pattern = r"\b(?:department|income|tax|govt|are|an)\b(?=\s|\W|$)|[-=\d]+"
        for line in lines[matching_text_index:]:
            match = re.search(pattern, line.lower(), flags=re.IGNORECASE)
            if match:
                continue
            next_line_list = line.split()
            break

        """remove special characters and white spaces"""
        clean_next_line = [element for element in next_line_list if re.search(r'[a-zA-Z0-9]', element)]
        user_name = " ".join(clean_next_line)
        if len(clean_next_line) > 1:
            clean_next_line = clean_next_line[:-1]
        
        """get the coordinates"""
        for i,(x1,y1,x2,y2,text) in enumerate(self.coordinates):
            if text in clean_next_line:
              matching_text_coords.append([x1, y1, x2, y2])
            if len(matching_text_coords) == len(clean_next_line):
                break
        
        if len(matching_text_coords) > 1:
            result = {
                f"{self.LABEL_NAME}": user_name,
                "coordinates": [[matching_text_coords[0][0], matching_text_coords[0][1], matching_text_coords[-1][2], matching_text_coords[-1][3]]]
            }
        else:
            result = {
                f"{self.LABEL_NAME}": user_name,
                "coordinates": [[matching_text_coords[0][0], matching_text_coords[0][1], matching_text_coords[0][2], matching_text_coords[0][3]]]
            }

        return result

    def __find_matching_text_index_username(self, lines: list, matching_text: list) -> int:
        for i,line in enumerate(lines):
            for k in matching_text:
                if k in line:
                    return i
        return 404

    """func: extract father's name"""
    def extract_fathername_p2(self):
        result = {}
        dob_text = None
        matching_text_coords = []

        """Data patterns: DD/MM/YYY, DD-MM-YYY"""
        date_pattern = r'\d{2}/\d{2}/\d{4}|\d{2}-\d{2}-\d{4}'
        for i, (x1, y1, x2, y2, text) in enumerate(self.coordinates):
            match = re.search(date_pattern, text)
            if match:
                dob_text = text
                break
        if not dob_text:
            return result
        
        """split the text into lines"""
        lines = [i for i in self.text.splitlines() if len(i) != 0]

        """find the matching text index"""
        matching_text_index = self.__find_matching_text_index_father_name(lines, dob_text)
        if matching_text_index == 404:
            return result
        
        father_name_text = lines[matching_text_index]
        father_name_list = father_name_text.split()
        if len(father_name_list) > 1:
            father_name_list = father_name_list[:-1]

        """get the coordinates"""
        target_index = next((i for i, item in enumerate(self.coordinates) if item[4] == dob_text), None)
        for item in reversed(self.coordinates[:target_index + 1]):
            text = item[4]
            if text in father_name_list:
                matching_text_coords.append([item[0], item[1], item[2], item[3]])
            if len(matching_text_coords) == len(father_name_list):
                break
            
        if len(matching_text_coords) > 1:
            result = {
                f"{self.LABEL_NAME}": father_name_text,
                "coordinates": [[matching_text_coords[-1][0], matching_text_coords[-1][1], matching_text_coords[0][2], matching_text_coords[0][3]]]
            }
        else:
            result = {
                f"{self.LABEL_NAME}": father_name_text,
                "coordinates": [[matching_text_coords[0][0], matching_text_coords[0][1], matching_text_coords[0][2], matching_text_coords[0][3]]]
            }
        return result

    def __find_matching_text_index_father_name(self, lines, matching_text) -> int:
        for i,line in enumerate(lines):
            if len(line) != 1 and line == matching_text:
                return i -1
        return 404