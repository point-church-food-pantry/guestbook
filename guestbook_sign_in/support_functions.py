import io
import pandas as pd
from django.contrib.staticfiles import finders
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

def print_to_pdf(params):
    '''
    Prints a single new guest's information to a TEFAP PDF (wrapped in a io.BytesIO object.)
    Imports an image of the English or Spanish PDF, as appropriate, and superimposes text above it in the appropriate locations.
    '''
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize = letter)
    c.setFont(psfontname = 'Courier', size = 11.0)
    
    if params['language_preference'] == 'English':
        filename = finders.find('guestbook_sign_in/tefap_images/english_auth_rep.png')
        c.drawImage(filename, x = 0, y = 0, width = 8.5*72.0, height = 11.0*72.0)
        c.drawString(4.5*72.0, 9.0*72.0, "Carolina Care Center")
        c.drawString(2.5*72.0, 8.6*72.0, f"{params['first_name']} {params['last_name']}")
        c.drawString(2.5*72.0, 8.2*72.0, f"Address: {params['address']}")
        c.drawString(2.5*72.0, 8.0*72.0, f"City: {params['city']} | County: {params['county']}")
        c.drawString(4.5*72.0, 7.7*72.0, f"{params['number_in_household']}")
        c.drawString(3.4*72.0, 7.42*72.0, f"{'X' if params['fns'] == 'Yes' else ''}")
        c.drawString(4.27*72.0, 7.42*72.0, f"{'X' if params['fns'] == 'No' else ''}")
        if params['fns'] == 'No':
            if pd.notna(params['monthly_income']):
                income = f"{params['monthly_income']} (Monthly)"
            elif pd.notna(params['yearly_income']):
                income = f"{params['yearly_income']} (Annual)"
            else:
                income = f"{params['weekly_income']} (Weekly)"
            c.drawString(3.5*72.0, 7.0*72.0, income)     
        if pd.notna(params['authorized_representative_1']): c.drawString(2.5*72.0, 6.2*72.0, f"{params['authorized_representative_1']}")
        if pd.notna(params['authorized_representative_2']): c.drawString(2.5*72.0, 5.8*72.0, f"{params['authorized_representative_2']}")
        c.setFont(psfontname = 'Courier', size = 30.0)
        c.drawString(6.0*72.0, 0.7*72.0, f"{params['guest_ID']}")      
        c.save()
    else:
        filename = finders.find('guestbook_sign_in/tefap_images/spanish_auth_rep.png')
        c.drawImage(filename, x = 0, y = 0, width = 8.5*72.0, height = 11.0*72.0)
        c.drawString(5.8*72.0, 9.2*72.0, "Carolina Care Center")
        c.drawString(2.5*72.0, 8.9*72.0, f"{params['first_name']} {params['last_name']}")
        c.drawString(2.5*72.0, 8.6*72.0, f"Address: {params['address']} | City: {params['city']} | County: {params['county']}")
        c.drawString(4.8*72.0, 8.3*72.0, f"{params['number_in_household']}")
        c.drawString(5.3*72.0, 8.05*72.0, f"{'FNS: Yes/Si' if params['fns'] == 'Yes' else 'FNS: No'}")
        if params['fns'] == 'No':
            if pd.notna(params['monthly_income']):
                income = f"{params['monthly_income']} (Monthly)"
            elif pd.notna(params['yearly_income']):
                income = f"{params['yearly_income']} (Annual)"
            else:
                income = f"{params['weekly_income']} (Weekly)"
            c.drawString(3.5*72.0, 7.75*72.0, income) 
        if pd.notna(params['authorized_representative_1']): c.drawString(3.5*72.0, 7.2*72.0, f"{params['authorized_representative_1']}")
        if pd.notna(params['authorized_representative_2']): c.drawString(3.5*72.0, 6.9*72.0, f"{params['authorized_representative_2']}")
        c.setFont(psfontname = 'Courier', size = 30.0)
        c.drawString(6.0*72.0, 1.0*72.0, f"{params['guest_ID']}")      
        c.save()        
    
    buffer.seek(0)
    return buffer
    
    
    
    
    
    
    