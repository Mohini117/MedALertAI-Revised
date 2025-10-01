import base64
import json
import re
import os
import datetime
from together import Together
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
  

class ImageAnalyzer:
    def __init__(self):
        self.api_key = os.getenv("TOGETHER_API_KEY")
        if not self.api_key:
            raise ValueError("API key not found. Please check your .env file.")
        self.client = Together(api_key=self.api_key)

    async def encode_image(self, image_file):
        try:
            if isinstance(image_file, bytes):
                # If it's already bytes, encode directly
                return base64.b64encode(image_file).decode("utf-8")
            elif hasattr(image_file, 'read'):
                # If it's a file-like object, await the read operation
                image_bytes = await image_file.read()
                return base64.b64encode(image_bytes).decode("utf-8")
            else:
                raise ValueError("Invalid image data type")
        except Exception as e:
            raise ValueError(f"Error encoding image: {str(e)}")

    async def analyze_prescription(self, image_file):
        prompt = """You are a highly accurate AI specialized in extracting structured information from medical prescriptions.  
Your task is to analyze the provided prescription image and return the details in the following strict JSON format:  

{  
    "Date": "<Extracted Date>",  
    "Patient": {  
        "Name": "<Extracted Name>",  
        "Age": "<Extracted Age>"  
    },  
    "Medicines": [  
        {  
            "Type": "<Tablet/Capsule/Syrup/etc.>",  
            "Medicine": "<Medicine Name>",  
            "Dosage": "<Dosage Instructions>",  
            "Timings": ["<time1>", "<time2>", "<time3>"]  
        }  
    ]  
}  

SMART TIMINGS EXTRACTION RULES:
Analyze the dosage pattern and convert it to realistic, patient-friendly timings based on these guidelines:

1. **For "1-0-1" or "Twice Daily" patterns:**
   - Morning: "8:00 AM" (ideal breakfast time)
   - Evening: "8:00 PM" (ideal dinner time)
   - Example: ["8:00 AM", "8:00 PM"]

2. **For "1-1-1" or "Three Times Daily" patterns:**
   - Morning: "8:00 AM" (with/after breakfast)
   - Afternoon: "2:00 PM" (after lunch)
   - Night: "9:00 PM" (after dinner)
   - Example: ["8:00 AM", "2:00 PM", "9:00 PM"]

3. **For "1-0-0" or "Once Daily" patterns:**
   - Morning: "8:00 AM" (unless specified as bedtime, then "10:00 PM")
   - Example: ["8:00 AM"] or ["10:00 PM"]

4. **For "0-1-0" or "Afternoon Only" patterns:**
   - Afternoon: "2:00 PM"
   - Example: ["2:00 PM"]

5. **For "0-0-1" or "Bedtime/Night Only" patterns:**
   - Night: "10:00 PM"
   - Example: ["10:00 PM"]

6. **For "1-1-0" patterns:**
   - Morning: "8:00 AM"
   - Afternoon: "2:00 PM"
   - Example: ["8:00 AM", "2:00 PM"]

7. **For "0-1-1" patterns:**
   - Afternoon: "2:00 PM"
   - Night: "9:00 PM"
   - Example: ["2:00 PM", "9:00 PM"]

8. **For "2-0-1" or higher frequency patterns:**
   - Space doses evenly: ["7:00 AM", "12:00 PM", "9:00 PM"]

9. **Medicine-Specific Timing Rules:**
   - **Antibiotics**: Space evenly (8-12 hours apart)
   - **Pain relievers**: "8:00 AM", "2:00 PM", "8:00 PM"
   - **Blood pressure meds**: Usually "8:00 AM"
   - **Diabetes meds**: "8:00 AM" (before breakfast), "7:00 PM" (before dinner)
   - **Sleep aids**: "10:00 PM"
   - **Antacids**: "2:00 PM", "9:00 PM" (after meals)

10. **Special Instructions:**
    - "Before meals": 30 minutes before standard meal times
    - "After meals": Standard meal completion times
    - "With food": Standard meal times
    - "Empty stomach": Early morning (6:00 AM) or bedtime (10:00 PM)

**IMPORTANT**: 
- Always provide realistic clock times (like "8:00 AM", "2:00 PM", "9:00 PM")
- Never use numbers like "1-0-1" in the timings array
- Consider meal times and daily routine for optimal patient compliance
- If frequency is unclear, default to safe, well-spaced timings

Return only the JSON output, without additional text or explanations."""  
 
        base64_image = await self.encode_image(image_file)  # Added await here
        if not base64_image:
            return None

        try:
            response = self.client.chat.completions.create(
                model="meta-llama/Llama-4-Scout-17B-16E-Instruct",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}} 
                        ],
                    }
                ],
                stream=False
            )

            full_response = response.choices[0].message.content
            json_match = re.search(r"\{.*\}", full_response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            return None

        except Exception as e:
            raise RuntimeError(f"Error analyzing prescription: {str(e)}")

    async def analyze_diagnostic_image(self, image_file):
        prompt = """Analyze the provided medical image and provide analysis in this JSON format:
        {
            "Predicted_Disease": "<Disease/Condition Name>",
            "Confidence_Score": "<Confidence Level (0-100%)>",
            "Description": "<Brief explanation>",
            "Possible_Causes": ["<Cause 1>", "<Cause 2>", "<Cause 3>"],
            "Recommended_Actions": ["<Action 1>", "<Action 2>", "<Action 3>"]
        }
If the image is unclear, specify that in the Description field."""

        base64_image = await self.encode_image(image_file)  # Added await here
        if not base64_image:
            return None

        try:
            response = self.client.chat.completions.create(
                model="meta-llama/Llama-4-Scout-17B-16E-Instruct",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                        ],
                    }
                ],
                stream=False
            )

            full_response = response.choices[0].message.content
            json_match = re.search(r"\{.*\}", full_response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            return None

        except Exception as e:
            raise RuntimeError(f"Error analyzing diagnostic image: {str(e)}") 