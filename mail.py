import pandas as pd
import smtplib
import os
from dotenv import load_dotenv  # New Import
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# Load variables from .env file
load_dotenv()

def send_survey_reports(csv_path, pdf_folder):
    # --- Configuration from .env ---
    sender_email = os.getenv("EMAIL_USER")
    sender_password = os.getenv("EMAIL_PASS")
    
    if not sender_email or not sender_password:
        print("❌ Error: Email credentials not found in .env file.")
        return
    
    # HTML Template
    html_template = """
    <!DOCTYPE html>
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <p> <strong>Dear {name} Ji,</strong> </p>
        <p>
          Thank you for participating in today’s event and for completing the 
          School Evolution Questionnaire Survey.
        </p>
        <p>
          We are pleased to share your personalized <strong>School Evolution Score Report</strong> 
          in this email. The report provides key insights into your school’s present 
          growth stage, leadership readiness, and future development opportunities.
        </p>
        <p>
          We hope these findings will support your strategic planning and help 
          strengthen your institution’s journey towards excellence.
        </p>
        <p>
          Please find your report attached for your kind review.
        </p>
        <p>
          Thank you once again for your valuable participation.
        </p>
        <br>
        <p>
          Warm regards,<br>
          <strong>Team EDXSO</strong>
        </p>
      </body>
    </html>
    """

    # Load the CSV data
    # Note: Using the provided CSV structure
    df = pd.read_csv(csv_path)
    
    try:
        # Connect to the SMTP server once
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        
        # Loop through the rows
        # We use enumerate(df.iterrows(), start=1) to easily get 1, 2, 3, 4 for the PDFs
        for index, (row_idx, row) in enumerate(df.iterrows(), start=1):
            
            # Extract email and name from the CSV columns
            recipient_email = row['email'] 
            attendee_name = row['name']    
            
            # Match the row to the PDF (1.pdf, 2.pdf, etc.)
            filename = f"pdfs/{index}.pdf"
            pdf_path = os.path.join(pdf_folder, filename)

            if not os.path.exists(pdf_path):
                print(f"⚠️ File not found for {attendee_name}: {pdf_path}")
                continue

            # Create Email
            message = MIMEMultipart()
            message["From"] = sender_email
            message["To"] = recipient_email
            message["Subject"] = "Your School Evolution Score Report"
            
            # Format the HTML template with the attendee's name
            formatted_html = html_template.format(name=attendee_name)
            message.attach(MIMEText(formatted_html, "html"))

            # Attach the PDF
            with open(pdf_path, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename={filename}")
            message.attach(part)

            # Send the email
            server.send_message(message)
            print(f"✅ Sent report {filename} to {attendee_name} at {recipient_email}")

        # Close the server connection
        server.quit()
        print("\n✨ All reports successfully dispatched!")

    except Exception as e:
        print(f"❌ Critical Error: {e}")

# --- Execute the Script ---
# Replace with your actual file paths
csv_file_path = "survey_report_7258 - survey_report_7258.csv" 
pdf_directory = "" # Leave as "" if PDFs are in the exact same folder as the script

send_survey_reports(csv_file_path, pdf_directory)