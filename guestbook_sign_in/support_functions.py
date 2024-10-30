import io
import json
from django.contrib.staticfiles import finders
from django.db.models import Max
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from .models import Guest, SignIn, LinkedProxy, UnlinkedProxy
from pypdf import PdfWriter, PdfReader
from django.http import FileResponse
from jsignature.utils import draw_signature
from datetime import date

OVERLAY_DIMS = {'2024-2025 English Front' : {'base_pdf' : 'guestbook_sign_in/tefap_pdfs/2024-2025 English Front.pdf',
                                             'name' : {'x' : 3.5*72.0, 'y' : 10.22*72.0},
                                             'address' : {'x' : 3.5*72.0, 'y' : 10.0*72.0},
                                             'city' : {'x' : 3.5*72.0, 'y' : 9.80*72.0},
                                             'county' : {'x' : 3.5*72.0, 'y' : 9.58*72.0},
                                             'number_in_household' : {'x' : 3.5*72.0, 'y' : 9.35*72.0},
                                             'authorized_representative_1' : {'x' : 3.5*72.0, 'y' : 3.53*72.0},
                                             'authorized_representative_2' : {'x' : 3.5*72.0, 'y' : 3.15*72.0},
                                             'front_signature' : {'x' : 1.0*72.0, 'y' : 2.78*72.0},
                                             'date' : {'x' : 3.2*72.0, 'y' : 2.78*72.0},
                                             'guest_ID' : {'x' : 6.0*72.0, 'y' : 0.7*72.0}},
                '2024-2025 English Proxy' : {'base_pdf' : 'guestbook_sign_in/tefap_pdfs/2024-2025 English Proxy.pdf',
                                             'care_center' : {'x' : 4.5*72.0, 'y' : 9.15*72.0},
                                             'name' : {'x' : 2.5*72.0, 'y' : 8.7*72.0},
                                             'address' : {'x' : 2.5*72.0, 'y' : 8.4*72.0},
                                             'city_county' : {'x' : 2.5*72.0, 'y' : 8.2*72.0},
                                             'number_in_household' : {'x' : 4.5*72.0, 'y' : 7.95*72.0},
                                             'fns_Yes' : {'x' : 3.4*72.0, 'y' : 7.42*72.0},
                                             'fns_No' : {'x' : 4.27*72.0, 'y' : 7.42*72.0},
                                             'income' : {'x' : 3.5*72.0, 'y' : 7.0*72.0},
                                             'authorized_representative_1' : {'x' : 2.5*72.0, 'y' : 6.3*72.0},
                                             'authorized_representative_2' : {'x' : 2.5*72.0, 'y' : 5.9*72.0},
                                             'guest_ID' : {'x' : 6.0*72.0, 'y' : 0.7*72.0},
                                             'proxy_signature_date' : {'x' : 6.7*72.0, 'y' : 5.4*72.0},
                                             'proxy_signature' : {'x' : 3.0*72.0, 'y' : 5.4*72.0}},
                '2024-2025 Spanish Front' : {'base_pdf' : 'guestbook_sign_in/tefap_pdfs/2024-2025 Spanish Front.pdf',
                                             'name' : {'x' : 3.0*72.0, 'y' : 10.22*72.0},
                                             'address' : {'x' : 3.0*72.0, 'y' : 10.0*72.0},
                                             'city' : {'x' : 3.0*72.0, 'y' : 9.76*72.0},
                                             'county' : {'x' : 3.0*72.0, 'y' : 9.54*72.0},
                                             'number_in_household' : {'x' : 3.0*72.0, 'y' : 9.32*72.0},
                                             'authorized_representative_1' : {'x' : 3.3*72.0, 'y' : 3.3*72.0},
                                             'authorized_representative_2' : {'x' : 3.3*72.0, 'y' : 2.95*72.0},
                                             'front_signature' : {'x' : 1.0*72.0, 'y' : 2.6*72.0},
                                             'date' : {'x' : 3.2*72.0, 'y' : 2.6*72.0},
                                             'guest_ID' : {'x' : 6.0*72.0, 'y' : 0.7*72.0}},
                '2024-2025 Spanish Proxy' : {'base_pdf' : 'guestbook_sign_in/tefap_pdfs/2024-2025 Spanish Proxy.pdf',
                                             'care_center' : {'x' : 5.8*72.0, 'y' : 9.4*72.0},
                                             'name' : {'x' : 2.5*72.0, 'y' : 9.1*72.0},
                                             'address' : {'x' : 2.5*72.0, 'y' : 8.8*72.0},
                                             'city_county' : {'x' : 5.5*72.0, 'y' : 8.8*72.0},
                                             'number_in_household' : {'x' : 4.8*72.0, 'y' : 8.5*72.0},
                                             'fns_Yes' : {'x' : 5.3*72.0, 'y' : 8.15*72.0},
                                             'fns_No' : {'x' : 5.3*72.0, 'y' : 8.15*72.0},
                                             'income' : {'x' : 3.5*72.0, 'y' : 7.85*72.0},
                                             'authorized_representative_1' : {'x' : 3.5*72.0, 'y' : 7.25*72.0},
                                             'authorized_representative_2' : {'x' : 3.5*72.0, 'y' : 6.95*72.0},
                                             'guest_ID' : {'x' : 6.0*72.0, 'y' : 1.0*72.0},
                                             'proxy_signature_date' : {'x' : 6.9*72.0, 'y' : 6.7*72.0},
                                             'proxy_signature' : {'x' : 2.0*72.0, 'y' : 6.5*72.0},
                                             }
}

def TEFAP_back_page_dims(w):
    '''
    Locations for images and text boxes on the back page of the TEFAP form.
    '''
    overlay_dims = {
        '2024-2025 English Back' : {'base_pdf' : 'guestbook_sign_in/tefap_pdfs/2024-2025 English Back.pdf',
                                    'date' : {'x' : 0.97*72.0, 'y' : 9.05*72.0 - w*0.3427*72.0},
                                    'client_signature' : {'x' : 1.7*72.0, 'y' : 9.05*72.0 - w*0.3427*72.0},
                                    'fns_Yes' : {'x' : 3.34*72.0, 'y' : 9.05*72.0 - w*0.3427*72.0},
                                    'fns_No' :  {'x' : 3.72*72.0, 'y' : 9.05*72.0 - w*0.3427*72.0},
                                    'yearly_income' : {'x' : 4.0*72.0, 'y' : 9.05*72.0 - w*0.3427*72.0},
                                    'monthly_income' : {'x' : 5.1*72.0, 'y' : 9.05*72.0 - w*0.3427*72.0},
                                    'weekly_income' : {'x' : 5.86*72.0, 'y' : 9.05*72.0 - w*0.3427*72.0},
                                    'agency_representative_signature' : {'x' : 6.9*72.0, 'y' : 9.05*72.0 - w*0.3427*72.0}},
        '2024-2025 Spanish Back' : {'base_pdf' : 'guestbook_sign_in/tefap_pdfs/2024-2025 Spanish Back.pdf',
                                    'date' : {'x' : 0.82*72.0, 'y' : 8.8*72.0 - w*0.3427*72.0},
                                    'client_signature' : {'x' : 1.5*72.0, 'y' : 8.8*72.0 - w*0.3427*72.0},
                                    'fns_Yes' : {'x' : 3.2*72.0, 'y' : 8.8*72.0 - w*0.3427*72.0},
                                    'fns_No' : {'x' : 3.58*72.0, 'y' : 8.8*72.0 - w*0.3427*72.0},
                                    'yearly_income' : {'x' : 3.85*72.0, 'y' : 8.8*72.0 - w*0.3427*72.0},
                                    'monthly_income' : {'x' : 4.9*72.0, 'y' : 8.8*72.0 - w*0.3427*72.0},
                                    'weekly_income' : {'x' : 5.67*72.0, 'y' : 8.8*72.0 - w*0.3427*72.0},
                                    'agency_representative_signature' : {'x' : 6.5*72.0, 'y' : 8.8*72.0 - w*0.3427*72.0}}
    }
    return overlay_dims

def make_tefap_front_overlay(internal_id):
    '''
    Create overlay for TEFAP front page.
    '''
    buffer = io.BytesIO()
    guest = Guest.objects.filter(internal_ID = internal_id).values()[0]

    if guest['language_preference'] == 'English':
        lookup = '2024-2025 English Front'
    else:
        lookup = '2024-2025 Spanish Front'

    c = canvas.Canvas(buffer, pagesize = letter)
    c.setFont(psfontname = 'Courier', size = 11.0)
    c.drawString(OVERLAY_DIMS[lookup]['name']['x'], OVERLAY_DIMS[lookup]['name']['y'], f"{guest['first_name']} {guest['last_name']}")
    c.drawString(OVERLAY_DIMS[lookup]['address']['x'], OVERLAY_DIMS[lookup]['address']['y'], f"{guest['address']}")
    c.drawString(OVERLAY_DIMS[lookup]['city']['x'], OVERLAY_DIMS[lookup]['city']['y'], f"{guest['city']}")
    c.drawString(OVERLAY_DIMS[lookup]['county']['x'], OVERLAY_DIMS[lookup]['county']['y'], f"{guest['county']}")
    c.drawString(OVERLAY_DIMS[lookup]['number_in_household']['x'], OVERLAY_DIMS[lookup]['number_in_household']['y'], f"{guest['number_in_household']}")
    c.drawString(OVERLAY_DIMS[lookup]['authorized_representative_1']['x'], OVERLAY_DIMS[lookup]['authorized_representative_1']['y'], f"{guest['authorized_representative_1']}")
    c.drawString(OVERLAY_DIMS[lookup]['authorized_representative_2']['x'], OVERLAY_DIMS[lookup]['authorized_representative_2']['y'], f"{guest['authorized_representative_2']}")    
    if guest['tefap_signature'] not in [None, '']:
        front_signature = draw_signature(json.loads(guest['tefap_signature'].replace("'",'"')), as_file = True)
        c.drawImage(front_signature, 
                    x = OVERLAY_DIMS[lookup]['front_signature']['x'], 
                    y = OVERLAY_DIMS[lookup]['front_signature']['y'], 
                    height = 0.5*72.0, 
                    mask = 'auto')
    c.drawString(OVERLAY_DIMS[lookup]['date']['x'], OVERLAY_DIMS[lookup]['date']['y'], f"{guest['tefap_signature_date']}")
    c.setFont(psfontname = 'Courier', size = 30.0)
    c.drawString(OVERLAY_DIMS[lookup]['guest_ID']['x'], OVERLAY_DIMS[lookup]['guest_ID']['y'], f"{guest['guest_ID']}")    
    c.save()
    buffer.seek(0)
    return lookup, buffer

def make_tefap_back_overlay(internal_id):
    '''
    Create overlap for TEFAP back page.
    '''
    buffer = io.BytesIO()
    guest = Guest.objects.filter(internal_ID = internal_id).values()[0]

    if guest['language_preference'] == 'English':
        lookup = '2024-2025 English Back'
    else:
        lookup = '2024-2025 Spanish Back'

    if date.today().month < 10:
        cutoff_date = date(year = date.today().year - 1, month = 10, day = 1)
    else:
        cutoff_date = date(year = date.today().year, month = 10, day = 1)
    sign_ins = SignIn.objects.filter(internal_ID_id = internal_id).filter(valid = True).filter(date__gt = cutoff_date)

    if len(sign_ins) == 0:
        return lookup, buffer
    else:
        sign_ins = sign_ins.values()
    
    c = canvas.Canvas(buffer, pagesize = letter)
    index = 0
    for week in sign_ins:
        w = index % 24
        overlay_dims = TEFAP_back_page_dims(w)                      
        c.drawString(overlay_dims[lookup]['date']['x'], overlay_dims[lookup]['date']['y'], f"{week['date']}")
        if week['signature'] not in [None, '']:
            client_signature = draw_signature(json.loads(week['signature'].replace("'",'"')), as_file = True)
            c.drawImage(client_signature, 
                        x = overlay_dims[lookup]['client_signature']['x'], 
                        y = overlay_dims[lookup]['client_signature']['y'],
                        width = 1.0*72.0, 
                        height = 0.2*72.0, 
                        mask = 'auto')
            c.drawString(overlay_dims[lookup]['fns_Yes']['x'], overlay_dims[lookup]['fns_Yes']['y'], f"{'X' if week['fns'] == 'Yes' else ''}")
            c.drawString(overlay_dims[lookup]['fns_No']['x'], overlay_dims[lookup]['fns_No']['y'], f"{'X' if week['fns'] == 'No' else ''}")
            if week['yearly_income'] not in [None, '']:
                c.drawString(overlay_dims[lookup]['yearly_income']['x'], overlay_dims[lookup]['yearly_income']['y'], f"${week['yearly_income']}")
            if week['monthly_income'] not in [None, '']:
                c.drawString(overlay_dims[lookup]['monthly_income']['x'], overlay_dims[lookup]['monthly_income']['y'], f"${week['monthly_income']}")
            if week['weekly_income'] not in [None, '']:
                c.drawString(overlay_dims[lookup]['weekly_income']['x'], overlay_dims[lookup]['weekly_income']['y'], f"${week['weekly_income']}")
            if week['agency_representative_signature'] not in [None, '']:
                agency_representative_signature = draw_signature(json.loads(week['agency_representative_signature'].replace("'",'"')), as_file = True)
                c.drawImage(agency_representative_signature, 
                            x = overlay_dims[lookup]['agency_representative_signature']['x'], 
                            y = overlay_dims[lookup]['agency_representative_signature']['y'], 
                            width = 1.0*72.0, 
                            height = 0.2*72.0, 
                            mask = 'auto')
            if w == 23:
                c.showPage()
                c.setFont(psfontname = 'Courier', size = 11.0)
            index = index + 1
    c.showPage()
    c.save()
    buffer.seek(0)
    return lookup, buffer

def make_tefap_proxy_overlay(internal_id):
    '''
    Create overlay for TEFAP proxy page.
    '''
    buffer = io.BytesIO()
    guest = Guest.objects.filter(internal_ID = internal_id).values()[0]

    if guest['language_preference'] == 'English':
        lookup = '2024-2025 English Proxy'
    else:
        lookup = '2024-2025 Spanish Proxy'

    # There should only be one valid proxy form at a time. If there are multiple, select the one with the most recent date.
    use_linked_proxy = None

    linked_proxy = LinkedProxy.objects.filter(internal_ID = internal_id).filter(valid = True)
    if len(linked_proxy) > 0:
        newest_date = linked_proxy.aggregate(nd=Max('proxy_signature_date'))
        linked_proxy = linked_proxy.filter(proxy_signature_date = newest_date['nd']).values()[0]

    unlinked_proxy = UnlinkedProxy.objects.filter(internal_ID = internal_id).filter(valid = True)
    if len(unlinked_proxy) > 0:
        newest_date = unlinked_proxy.aggregate(nd=Max('proxy_signature_date'))
        unlinked_proxy = unlinked_proxy.filter(proxy_signature_date = newest_date['nd']).values()[0]

    if (len(linked_proxy) > 0) and (len(unlinked_proxy) > 0):
        lp_date = linked_proxy['proxy_signature_date']
        ul_date = unlinked_proxy['proxy_signature_date']
        if lp_date >= ul_date: 
            use_linked_proxy = 1
        else: 
            use_linked_proxy = 0     
    elif (len(linked_proxy) > 0):
        use_linked_proxy = 1
    elif (len(unlinked_proxy) > 0):
        use_linked_proxy = 0
    else:
        return lookup, buffer # No matching proxies, return blank form
    
    params = {'first_name' : guest['first_name'] if use_linked_proxy == 1 else unlinked_proxy['first_name'],
              'last_name' : guest['last_name'] if use_linked_proxy == 1 else unlinked_proxy['last_name'],
              'address' : guest['address'] if use_linked_proxy == 1 else unlinked_proxy['address'],
              'city' : guest['city'] if use_linked_proxy == 1 else unlinked_proxy['city'],
              'county' : guest['county'] if use_linked_proxy == 1 else unlinked_proxy['county'],
              'number_in_household' : guest['number_in_household'] if use_linked_proxy == 1 else unlinked_proxy['number_in_household'],
              'fns' : linked_proxy['fns'] if use_linked_proxy == 1 else unlinked_proxy['fns'],
              'monthly_income' : linked_proxy['monthly_income'] if use_linked_proxy == 1 else unlinked_proxy['monthly_income'],
              'authorized_representative_1' : guest['authorized_representative_1'] if use_linked_proxy == 1 else unlinked_proxy['authorized_representative_1'],
              'authorized_representative_2' : guest['authorized_representative_2'] if use_linked_proxy == 1 else unlinked_proxy['authorized_representative_2'],
              'proxy_signature_date' : linked_proxy['proxy_signature_date'] if use_linked_proxy == 1 else unlinked_proxy['proxy_signature_date'],
              'proxy_signature' : linked_proxy['proxy_signature'] if use_linked_proxy == 1 else unlinked_proxy['proxy_signature'],
              'guest_ID' : guest['guest_ID']
    }
    
    c = canvas.Canvas(buffer, pagesize = letter)
    c.setFont(psfontname = 'Courier', size = 11.0)
    c.drawString(OVERLAY_DIMS[lookup]['care_center']['x'], OVERLAY_DIMS[lookup]['care_center']['y'], "Carolina Care Center")
    c.drawString(OVERLAY_DIMS[lookup]['name']['x'], OVERLAY_DIMS[lookup]['name']['y'], f"{params['first_name']} {params['last_name']}")
    c.drawString(OVERLAY_DIMS[lookup]['address']['x'], OVERLAY_DIMS[lookup]['address']['y'], f"Address: {params['address']}")
    c.drawString(OVERLAY_DIMS[lookup]['city_county']['x'], OVERLAY_DIMS[lookup]['city_county']['y'], f"City: {params['city']} | County: {params['county']}")
    c.drawString(OVERLAY_DIMS[lookup]['number_in_household']['x'], OVERLAY_DIMS[lookup]['number_in_household']['y'], f"{params['number_in_household']}")
    c.drawString(OVERLAY_DIMS[lookup]['fns_Yes']['x'], OVERLAY_DIMS[lookup]['fns_Yes']['y'], f"{'X (Yes)' if params['fns'] == 'Yes' else ''}")
    c.drawString(OVERLAY_DIMS[lookup]['fns_No']['x'], OVERLAY_DIMS[lookup]['fns_No']['y'], f"{'X (No)' if params['fns'] == 'No' else ''}")

    if params['monthly_income'] not in ['', None]:
        income = f"{params['monthly_income']} (Monthly)"
        c.drawString(OVERLAY_DIMS[lookup]['income']['x'], OVERLAY_DIMS[lookup]['income']['y'], income) 

    if params['authorized_representative_1'] not in ['', None]: c.drawString(OVERLAY_DIMS[lookup]['authorized_representative_1']['x'], 
                                                                            OVERLAY_DIMS[lookup]['authorized_representative_1']['y'], 
                                                                            f"{params['authorized_representative_1']}")
    if params['authorized_representative_2'] not in ['', None]: c.drawString(OVERLAY_DIMS[lookup]['authorized_representative_2']['x'], 
                                                                            OVERLAY_DIMS[lookup]['authorized_representative_2']['y'], 
                                                                            f"{params['authorized_representative_2']}")
    if params['proxy_signature'] not in [None, '']:
        proxy_signature = draw_signature(json.loads(params['proxy_signature'].replace("'",'"')), as_file = True)
        c.drawImage(proxy_signature, 
                    x = OVERLAY_DIMS[lookup]['proxy_signature']['x'], 
                    y = OVERLAY_DIMS[lookup]['proxy_signature']['y'], 
                    height = 0.5*72.0, 
                    mask = 'auto')
    c.drawString(OVERLAY_DIMS[lookup]['proxy_signature_date']['x'], OVERLAY_DIMS[lookup]['proxy_signature_date']['y'], f"{params['proxy_signature_date']}")

    c.setFont(psfontname = 'Courier', size = 30.0)
    c.drawString(OVERLAY_DIMS[lookup]['guest_ID']['x'], OVERLAY_DIMS[lookup]['guest_ID']['y'], f"{params['guest_ID']}")      
    c.save()        
    
    buffer.seek(0)
    return lookup, buffer

def make_pdf(lookup, buffer):
    '''
    Overlay custom text in buffer on appropriate PDF background.
    '''
    output = io.BytesIO()
    try: 
        base_pdf = finders.find(OVERLAY_DIMS[lookup]['base_pdf'])
    except: 
        base_pdf = finders.find(TEFAP_back_page_dims(0)[lookup]['base_pdf'])

    writer = PdfWriter()
    base_input = PdfReader(base_pdf)

    if buffer.getvalue() == b'':
        which_lookup = lookup.split(" ")[-1:][0].strip()
        if which_lookup == 'Back': # Always print back of TEFAP form.
            writer.add_page(base_input.pages[0])
        else: # Only print proxy form if there is proxy data.
            return output
    else:
        overlay = PdfReader(buffer)
        for overlay_page in overlay.pages:
            b = base_input.pages[0] # There should only be one base image to reuse as many times as needed.
            b.merge_page(overlay_page)
            writer.add_page(b)
        
    writer.write(output)
    output.seek(0)
    return output

def make_single_report_pdf(internal_id):
    '''
    Create TEFAP form and proxy form for a single guest.
    '''
    lookup, buffer = make_tefap_front_overlay(internal_id)
    front = make_pdf(lookup, buffer)

    lookup, buffer = make_tefap_back_overlay(internal_id)
    back = make_pdf(lookup, buffer)

    lookup, buffer = make_tefap_proxy_overlay(internal_id)
    proxy = make_pdf(lookup, buffer)

    writer = PdfWriter()
    for pdf_bytestream in [front, back, proxy]:
        if pdf_bytestream.getvalue() == b'':
            continue
        reader = PdfReader(pdf_bytestream)
        for page in reader.pages: writer.add_page(page)
    
    output = io.BytesIO()
    writer.write(output)
    output.seek(0)
    return output

def make_all_report_pdfs():
    '''
    Create TEFAP forms and proxy forms for all guests.
    '''
    guests = list(Guest.objects.values_list('internal_ID', flat=True))

    writer = PdfWriter()
    for guest in guests:
        guest_pdf = make_single_report_pdf(guest)
        g = PdfReader(guest_pdf)
        for page in g.pages: writer.add_page(page)
    
    output = io.BytesIO()
    writer.write(output)
    output.seek(0)
    return FileResponse(output, as_attachment = True, filename = f"TEFAP PDF {date.today()}.pdf")


