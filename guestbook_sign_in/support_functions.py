from .models import Guest, SignIn
import pandas as pd
from tkinter import filedialog

def upload_guests_and_sign_ins():
    
    filepath = filedialog.askopenfilename(title="Select database file to upload")
    guests = pd.read_excel(filepath, sheet_name = 'guests')
    sign_ins = pd.read_excel(filepath, sheet_name = 'sign_ins')
    
    for guest in guests.itertuples():
        
        new_guest = Guest(guest_ID = guest.guest_ID,
                          active = guest.active,
                          first_name = guest.first_name,
                          last_name = guest.last_name,
                          address = guest.address,
                          city = guest.city,
                          county = guest.county,
                          phone = guest.phone,
                          email = guest.email,
                          number_in_household = guest.number_in_household,
                          authorized_representative_1 = guest.authorized_representative_1,
                          authorized_representative_2 = guest.authorized_representative_2,
                          authorized_representative_3 = guest.authorized_representative_3,
                          authorized_representative_4 = guest.authorized_representative_4,
                          authorized_representative_5 = guest.authorized_representative_5,
                          tefap_signature_date = guest.tefap_signature_date,
                          tefap_signature = guest.tefap_signature,
                          language_preference = guest.language_preference)
        new_guest.save()
        
    for sign_in in sign_ins.itertuples():

            new_sign_in = SignIn(internal_ID_id = sign_in.internal_ID_id,
                                 date = sign_in.date,
                                 who_performed_pickup = sign_in.who_performed_pickup,
                                 signature = sign_in.signature,
                                 fns = sign_in.fns,
                                 number_in_household = sign_in.number_in_household,
                                 yearly_income = sign_in.yearly_income,
                                 monthly_income = sign_in.monthly_income,
                                 weekly_income = sign_in.weekly_income,
                                 tefap_eligible = sign_in.tefap_eligible,
                                 agency_representative_signature = sign_in.agency_representative_signature)
            new_sign_in.save()






