### Module Imports ###

from django.shortcuts import render
from django.contrib.staticfiles import finders
from django.http import HttpResponseRedirect, FileResponse
from django.urls import reverse
from .models import Guest, SignIn
from .forms import GuestInput, SignInInput, SearchBar
import pandas as pd
from fuzzywuzzy import fuzz, process
from datetime import date
import io
import json
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from jsignature.utils import draw_signature

### Views ###

def index(request):
    '''
    Landing page for guestbook_sign_in app
    '''   
    return render(request, 'index.html')

def create_new_guest(request, language):
    '''
    Generate TEFAP form for new guests.
    '''
    if request.method == 'POST':
        
        form = GuestInput(request.POST)
        if form.is_valid():
            
            # Sanity check to ensure someone doesn't create the same guest twice.
            # If the submission is a duplicate, looks up the guest ID of the match and takes you to their sign-in page.
            # Designed for the use case of "someone hit the back arrow from the weekly sign-in page after creating a new guest."
            existing_guests_match = list(Guest.objects.filter(first_name = form.cleaned_data['first_name'],
                                                         last_name = form.cleaned_data['last_name'],
                                                         tefap_signature_date = date.today()).values())

            if len(existing_guests_match) > 0:
                guest_id = existing_guests_match[0]['guest_ID']
                return HttpResponseRedirect(reverse('weekly_signatures', args = (language, guest_id)))    
            
            # If the "return" statement above isn't thrown, we assume the guest is not a duplicate. 
            # Create a new guest ID if one is not provided manually. 
            # The manual guest ID should be used with caution, we currently do not have checks to ensure no duplicates.
            
            if form.cleaned_data['guest_ID'] == None:
                if len(Guest.objects.values_list('guest_ID', flat = True)) == 0: guest_id = 1
                else: guest_id = max(Guest.objects.values_list('guest_ID', flat = True)) + 1
            else:
                guest_id = form.cleaned_data['guest_ID']
            
            # Add new guest to database
            new_guest = Guest(guest_ID = guest_id,
                              active = 'Active',
                              first_name = form.cleaned_data['first_name'],
                              last_name = form.cleaned_data['last_name'],
                              address = form.cleaned_data['address'],
                              city = form.cleaned_data['city'],
                              county = form.cleaned_data['county'],
                              phone = form.cleaned_data['phone'],
                              email = form.cleaned_data['email'],
                              number_in_household = form.cleaned_data['number_in_household'],
                              authorized_representative_1 = form.cleaned_data['authorized_representative_1'],
                              authorized_representative_2 = form.cleaned_data['authorized_representative_2'],
                              tefap_signature_date = date.today(),
                              tefap_signature = form.cleaned_data['tefap_signature'],
                              language_preference = language) 
            new_guest.save()
            return HttpResponseRedirect(reverse('weekly_signatures', args = (language, guest_id)))
    else:
        form = GuestInput()
    
    income_table = pd.read_csv(finders.find('guestbook_sign_in/TEFAP_Income_Table.csv')).values.tolist()
    context = {'form' : form,
               'today' : date.today(),
               'income_table' : income_table}
    
    if language == 'English':
        html = 'create_new_english.html'
    else:
        html = 'create_new_spanish.html'
    
    return render(request, html, context = context)

def weekly_signatures(request, language, guest_ID):
    '''
    Equivalent to signing the back of a TEFAP form.
    '''
    # Need to implement some kind of check for duplicate guest IDs.
    guest = Guest.objects.get(guest_ID = guest_ID)
    
    pickup_choices = [(f'{guest.first_name} {guest.last_name}', f'{guest.first_name} {guest.last_name}')]
    if guest.authorized_representative_1 not in ['', None]:
        pickup_choices.append((f'{guest.authorized_representative_1}', f'{guest.authorized_representative_1}'))
    if guest.authorized_representative_2 not in ['', None]:
        pickup_choices.append((f'{guest.authorized_representative_2}', f'{guest.authorized_representative_2}'))
    if guest.authorized_representative_3 not in ['', None]:
        pickup_choices.append((f'{guest.authorized_representative_3}',f'{guest.authorized_representative_3}'))
    if guest.authorized_representative_4 not in ['', None]:
        pickup_choices.append((f'{guest.authorized_representative_4}',f'{guest.authorized_representative_4}'))
    if guest.authorized_representative_5 not in ['', None]:
        pickup_choices.append((f'{guest.authorized_representative_5}',f'{guest.authorized_representative_5}'))
    
    if request.method == 'POST':
        form = SignInInput(request.POST)
        form.fields['who_performed_pickup'].choices = pickup_choices

        if form.is_valid():
            
            # Sanity check to ensure someone doesn't sign in the same guest twice. 
            # No one with the same {internal_ID_id} should sign in twice in one day.
            today_sign_ins_match = list(SignIn.objects.filter(date = date.today(), 
                                                              internal_ID_id = guest.internal_ID).values())
            if len(today_sign_ins_match) > 0:
                eligible = today_sign_ins_match[0]['tefap_eligible']
                return HttpResponseRedirect(reverse('submission_complete', kwargs = {'tefap_flag' : eligible, 'guest_ID' : guest_ID}))
            
            # If the HTTPResponseRedirect above is not thrown, we assume the guest has not been signed in yet.
            
            if form.cleaned_data['number_in_household'] == None:
                num_in_hh = guest.number_in_household
            else:
                num_in_hh = form.cleaned_data['number_in_household']
                guest.number_in_household = num_in_hh
                guest.save()
            
            yi = form.cleaned_data['yearly_income']
            mi = form.cleaned_data['monthly_income']
            wi = form.cleaned_data['weekly_income']            
            fns = form.cleaned_data['fns']
            
            # Test for TEFAP eligibility
            eligible = 'No'
            
            # If food stamps = yes, automatically eligible for TEFAP
            if fns == 'Yes':
                eligible = 'Yes'
                
            else:
                income_table = pd.read_csv(finders.find('guestbook_sign_in/TEFAP_Income_Table.csv'))
                income_table = income_table.replace(to_replace = '[^0-9]', value = '', regex = True)
                income_table = income_table.map(lambda x : float(x) if x != '' else pd.NA)
                            
                hh_max = income_table['Household Size'].max()
                if yi != None:
                    if num_in_hh <= hh_max:
                        threshold = income_table[income_table['Household Size'] == num_in_hh]['Per Year'].iloc[0]
                    else:
                        threshold = income_table[income_table['Household Size'] == hh_max]['Per Year'].iloc[0] + \
                            income_table[pd.isna(income_table['Household Size'])]['Per Year'].iloc[0] * (num_in_hh - hh_max)     
                    if yi <= threshold: eligible = 'Yes'
                elif mi != None:
                    if num_in_hh <= hh_max:
                        threshold = income_table[income_table['Household Size'] == num_in_hh]['Per Month'].iloc[0]
                    else:
                        threshold = income_table[income_table['Household Size'] == hh_max]['Per Month'].iloc[0] + \
                            income_table[pd.isna(income_table['Household Size'])]['Per Month'].iloc[0] * (num_in_hh - hh_max)    
                    if mi <= threshold: eligible = 'Yes'
                else:
                    if num_in_hh <= hh_max:
                        threshold = income_table[income_table['Household Size'] == num_in_hh]['Per Week'].iloc[0]
                    else:
                        threshold = income_table[income_table['Household Size'] == hh_max]['Per Week'].iloc[0] + \
                            income_table[pd.isna(income_table['Household Size'])]['Per Week'].iloc[0] * (num_in_hh - hh_max)
                    if wi <= threshold: eligible = 'Yes'              

            
            new_sign_in = SignIn(internal_ID = guest,
                                 date = date.today(),
                                 who_performed_pickup =form.cleaned_data['who_performed_pickup'],
                                 signature = form.cleaned_data['signature'],
                                 fns = fns,
                                 number_in_household = num_in_hh,
                                 yearly_income = yi,
                                 monthly_income = mi,
                                 weekly_income = wi,
                                 tefap_eligible = eligible,
                                 agency_representative_signature = form.cleaned_data['agency_representative_signature'])
            new_sign_in.save()

            return HttpResponseRedirect(reverse('submission_complete', kwargs = {'tefap_flag' : eligible, 'guest_ID' : guest_ID}))
        
    else:
        form = SignInInput(initial = {'previously_reported_number_in_household' : guest.number_in_household})
        form.fields['who_performed_pickup'].choices = pickup_choices
        
    context = {'form' : form,
               'today' : date.today(),
               'guest' : guest}
    
    if language == 'English':
        html = 'weekly_signatures_english.html'
    else:
        html = 'weekly_signatures_spanish.html'
    
    return render(request, html, context = context)
    
def submission_complete(request, tefap_flag, guest_ID): 
    if tefap_flag == 'Yes':
        flag_english = 'eligible'
        instructions_english = 'Please proceed through the line as normal.'
        flag_spanish = 'elegible'
        instructions_spanish = 'Continúe por la línea como de costumbre.'
    else:
        flag_english = 'not eligible'
        instructions_english = 'We will still make sure you get food! Please speak with one of our staff members and we will prepare a bag of food for you.'
        flag_spanish = 'no elegible'
        instructions_spanish = '¡Aún nos aseguraremos de que recibas comida! Hable con uno de los miembros de nuestro personal y le prepararemos una bolsa de comida.'
    
    context = {'flag_english' : flag_english,
               'instructions_english' : instructions_english,
               'flag_spanish' : flag_spanish,
               'instructions_spanish' : instructions_spanish,
               'guest_ID' : guest_ID}
    
    return render(request, 'submission_complete.html', context = context)

def sign_in(request):
    '''
    Sign in an existing guest.
    '''
    already_signed_in = list(SignIn.objects.filter(date = date.today()).values_list('internal_ID', flat = True))
    if request.method == 'POST':
        form = SearchBar(request.POST)
        if form.is_valid():
            search_string = form.cleaned_data['name_search']
     
            # If search string is a guest ID, just return that guest!
            try:
                search_string = int(search_string)
                candidates = pd.DataFrame(Guest.objects.exclude(internal_ID__in = already_signed_in).filter(guest_ID = search_string).values())
                if candidates.empty:
                    matches_iter = pd.DataFrame(None, columns = ['first_name', 'last_name', 'guest_ID']).itertuples()
                else:
                    matches_iter = candidates[['first_name', 'last_name', 'guest_ID']].itertuples()
                
            except:
                candidates = pd.DataFrame(Guest.objects.exclude(internal_ID__in = already_signed_in).values())
                names = candidates['first_name'] + ' ' + candidates['last_name']
                fuzzy_search = process.extract(search_string, 
                                               names.values.tolist(),
                                               scorer = fuzz.token_set_ratio, 
                                               limit = 10)          
                
                matches = candidates[names.isin(list(dict(fuzzy_search).keys()))]
                matches_iter = matches[['first_name', 'last_name', 'guest_ID']].itertuples()
                
            context = {'searchbar' : form,
                       'guests' : matches_iter}
            return render(request, 'sign_in.html', context = context)  
    else:
        form = SearchBar()
        context = {'searchbar' : form,
                   'guests' : Guest.objects.exclude(internal_ID__in = already_signed_in).values()}
    return render(request, 'sign_in.html', context = context)

def sign_out(request):
    '''
    Sign out a guest that was checked in within the last day.
    '''
    context = {}
    return render(request, 'sign_out.html', context = context)

def generate_report(request):
    '''
    Summary statistics and sign-in records from the last day.
    '''
    total_guests = pd.DataFrame(SignIn.objects.filter(date = date.today()).values())
    
    if total_guests.empty:
        
        context = {'tefap_guests_count' : 0,
                   'new_tefap_guests_count' : 0,
                   'tefap_guests_sum' : 0,
                   'non_tefap_guests_count' : 0,
                   'new_non_tefap_guests_count' : 0,
                   'non_tefap_guests_sum' : 0,
                   'total_guests_count' : 0,
                   'new_total_guests_count' : 0,
                   'total_guests_sum' : 0
                   }
    else:
    
        new_guests = pd.DataFrame(Guest.objects.filter(tefap_signature_date = date.today()).values())
        if not new_guests.empty: new_guests = new_guests.merge(right = total_guests, left_on = 'internal_ID', right_on = 'internal_ID_id', how = 'left')
        
        context = {'tefap_guests_count' : len(total_guests[total_guests['tefap_eligible'] == 'Yes']),
                   'new_tefap_guests_count' : 0 if new_guests.empty else len(new_guests[new_guests['tefap_eligible'] == 'Yes']),
                   'tefap_guests_sum' : total_guests[total_guests['tefap_eligible'] == 'Yes']['number_in_household'].sum(),
                   'non_tefap_guests_count' : len(total_guests[total_guests['tefap_eligible'] == 'No']),
                   'new_non_tefap_guests_count' : 0 if new_guests.empty else len(new_guests[new_guests['tefap_eligible'] == 'No']),
                   'non_tefap_guests_sum' : total_guests[total_guests['tefap_eligible'] == 'No']['number_in_household'].sum(),
                   'total_guests_count' : len(total_guests),
                   'new_total_guests_count' : len(new_guests),
                   'total_guests_sum' : total_guests['number_in_household'].sum()
                   }
        
    return render(request, 'generate_report.html', context = context)

def generate_report_file(request, file_type):
    
    guests = pd.DataFrame(Guest.objects.values())
    sign_ins = pd.DataFrame(SignIn.objects.values())
    
    if file_type == 'database':
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer) as writer:
            guests.to_excel(writer, sheet_name = 'guests', index = False)
            sign_ins.to_excel(writer, sheet_name = 'sign_ins', index = False)
        buffer.seek(0)
        response = FileResponse(buffer, as_attachment = True, filename = 'database.xlsx') 
        return response
    
    elif file_type == 'pdf':
        
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize = letter)
        
        for guest in guests.itertuples():
            
            if len(sign_ins) > 0:
                guest_sign_ins = sign_ins[(sign_ins['internal_ID_id'] == guest.internal_ID) & (sign_ins['tefap_eligible'] == 'Yes')].fillna(value = '')
            else:
                guest_sign_ins = pd.DataFrame(None)
                
            if guest.language_preference == 'English':
                
                front_image = finders.find('guestbook_sign_in/tefap_images/english_front.png')
                c.setFont(psfontname = 'Courier', size = 11.0)
                c.drawImage(front_image, x = 0, y = 0, width = 8.5*72.0, height = 11.0*72.0)
                c.drawString(3.5*72.0, 10.0*72.0, f"{guest.first_name} {guest.last_name}")
                c.drawString(3.5*72.0, 9.80*72.0, f"{guest.address}")
                c.drawString(3.5*72.0, 9.58*72.0, f"{guest.city}")
                c.drawString(3.5*72.0, 9.35*72.0, f"{guest.county}")
                c.drawString(3.5*72.0, 9.12*72.0, f"{guest.number_in_household}")
                c.drawString(3.5*72.0, 3.53*72.0, f"{guest.authorized_representative_1}")
                c.drawString(3.5*72.0, 3.15*72.0, f"{guest.authorized_representative_2}")
                if guest.tefap_signature not in [None, '']:
                    front_signature = draw_signature(json.loads(guest.tefap_signature.replace("'",'"')), as_file = True)
                    c.drawImage(front_signature, x = 1.0*72.0, y = 2.78*72.0, width = 2.0*72.0, height = 0.5*72.0, mask = 'auto')
                c.drawString(3.2*72.0, 2.78*72.0, f"{guest.tefap_signature_date}")
                c.setFont(psfontname = 'Courier', size = 30.0)
                c.drawString(6.0*72.0, 0.7*72.0, f"{guest.guest_ID}")    
                c.showPage()
            
                back_image = finders.find('guestbook_sign_in/tefap_images/english_back.png')
                c.setFont(psfontname = 'Courier', size = 11.0)
                c.drawImage(back_image, x = 0, y = 0, width = 8.5*72.0, height = 11.0*72.0)
                index = 0
                for week in guest_sign_ins.itertuples():
                    w = index % 24                        
                    c.drawString(0.97*72.0, 8.95*72.0 - w*0.3427*72.0, f"{week.date}")
                    if week.signature not in [None, '']:
                        client_signature = draw_signature(json.loads(week.signature.replace("'",'"')), as_file = True)
                        c.drawImage(client_signature, x = 1.4*72.0, y = 8.95*72.0 - w*0.3427*72.0, width = 1.0*72.0, height = 0.2*72.0, mask = 'auto')
                    c.drawString(3.34*72.0, 8.95*72.0 - w*0.3427*72.0, f"{'X' if week.fns == 'Yes' else ''}")
                    c.drawString(3.72*72.0, 8.95*72.0 - w*0.3427*72.0, f"{'X' if week.fns == 'No' else ''}")
                    c.drawString(4.0*72.0, 8.95*72.0 - w*0.3427*72.0, f"${week.yearly_income}")
                    c.drawString(5.0*72.0, 8.95*72.0 - w*0.3427*72.0, f"${week.monthly_income}")
                    c.drawString(5.86*72.0, 8.95*72.0 - w*0.3427*72.0, f"${week.weekly_income}")
                    if week.agency_representative_signature not in [None, '']:
                        agency_representative_signature = draw_signature(json.loads(week.agency_representative_signature.replace("'",'"')), as_file = True)
                        c.drawImage(agency_representative_signature, x = 6.3*72.0, y = 8.95*72.0 - w*0.3427*72.0, width = 1.0*72.0, height = 0.2*72.0, mask = 'auto')
                    if w == 23:
                        c.showPage()
                        c.setFont(psfontname = 'Courier', size = 11.0)
                        c.drawImage(back_image, x = 0, y = 0, width = 8.5*72.0, height = 11.0*72.0)
                    index = index + 1
                c.showPage()
                
            else:
                
                front_image = finders.find('guestbook_sign_in/tefap_images/spanish_front.png')
                c.setFont(psfontname = 'Courier', size = 11.0)
                c.drawImage(front_image, x = 0, y = 0, width = 8.5*72.0, height = 11.0*72.0)
                c.drawString(3.0*72.0, 10.0*72.0, f"{guest.first_name} {guest.last_name}")
                c.drawString(3.0*72.0, 9.76*72.0, f"{guest.address}")
                c.drawString(3.0*72.0, 9.54*72.0, f"{guest.city}")
                c.drawString(3.0*72.0, 9.32*72.0, f"{guest.county}")
                c.drawString(3.0*72.0, 9.10*72.0, f"{guest.number_in_household}")
                c.drawString(3.3*72.0, 3.3*72.0, f"{guest.authorized_representative_1}")
                c.drawString(3.3*72.0, 2.95*72.0, f"{guest.authorized_representative_2}")                
                if guest.tefap_signature not in [None, '']:
                    front_signature = draw_signature(json.loads(guest.tefap_signature.replace("'",'"')), as_file = True)
                    c.drawImage(front_signature, x = 1.0*72.0, y = 2.6*72.0, width = 2.0*72.0, height = 0.5*72.0, mask = 'auto')
                c.drawString(3.2*72.0, 2.6*72.0, f"{guest.tefap_signature_date}")
                c.setFont(psfontname = 'Courier', size = 30.0)
                c.drawString(6.0*72.0, 0.7*72.0, f"{guest.guest_ID}")    
                c.showPage()
                
                back_image = finders.find('guestbook_sign_in/tefap_images/spanish_back.png')
                c.setFont(psfontname = 'Courier', size = 11.0)                
                c.drawImage(back_image, x = 0, y = 0, width = 8.5*72.0, height = 11.0*72.0)
                index = 0
                for week in guest_sign_ins.itertuples():
                    w = index % 24                        
                    c.drawString(0.87*72.0, 8.58*72.0 - w*0.3427*72.0, f"{week.date}")
                    if week.signature not in [None, '']:
                        client_signature = draw_signature(json.loads(week.signature.replace("'",'"')), as_file = True)
                        c.drawImage(client_signature, x = 1.4*72.0, y = 8.58*72.0 - w*0.3427*72.0, width = 1.0*72.0, height = 0.2*72.0, mask = 'auto')
                    c.drawString(3.2*72.0, 8.58*72.0 - w*0.3427*72.0, f"{'X' if week.fns == 'Yes' else ''}")
                    c.drawString(3.58*72.0, 8.58*72.0 - w*0.3427*72.0, f"{'X' if week.fns == 'No' else ''}")
                    c.drawString(3.85*72.0, 8.58*72.0 - w*0.3427*72.0, f"${week.yearly_income}")
                    c.drawString(4.85*72.0, 8.58*72.0 - w*0.3427*72.0, f"${week.monthly_income}")
                    c.drawString(5.67*72.0, 8.58*72.0 - w*0.3427*72.0, f"${week.weekly_income}")
                    if week.agency_representative_signature not in [None, '']:
                        agency_representative_signature = draw_signature(json.loads(week.agency_representative_signature.replace("'",'"')), as_file = True)
                        c.drawImage(agency_representative_signature, x = 6.3*72.0, y = 8.58*72.0 - w*0.3427*72.0, width = 1.0*72.0, height = 0.2*72.0, mask = 'auto')
                    if w == 23:
                        c.showPage()
                        c.setFont(psfontname = 'Courier', size = 11.0)
                        c.drawImage(back_image, x = 0, y = 0, width = 8.5*72.0, height = 11.0*72.0)
                    index = index + 1
                c.showPage()                
                
        c.save()        
        buffer.seek(0)
        return FileResponse(buffer, as_attachment = True, filename = f"TEFAP PDF {date.today()}.pdf")


from .support_functions import print_to_pdf        
def generate_proxy_form(request, guest_ID):
    '''
    Generates a PDF of the TEFAP proxy form for the desired guest.
    '''
    guest = Guest.objects.filter(guest_ID = guest_ID).values()[0]
    sign_in = SignIn.objects.filter(internal_ID_id = guest['internal_ID'], date = date.today()).values()[0]
    for key, value in sign_in.items(): guest[key] = value 
    pdf = print_to_pdf(guest)
    return FileResponse(pdf, as_attachment = True, filename = f"Proxy Form - Guest {guest_ID}.pdf")
    

    
    
    
    
    