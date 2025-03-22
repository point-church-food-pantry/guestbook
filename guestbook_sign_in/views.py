### Module Imports ###

from django.shortcuts import render
from django.contrib.staticfiles import finders
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, FileResponse, HttpResponse, JsonResponse
from django.urls import reverse
from .models import Guest, SignIn, LinkedProxy, UnlinkedProxy
from .forms import GuestInput, SignInInput, SearchBar, LinkedProxyInput, UnlinkedProxyInput
import pandas as pd
from fuzzywuzzy import fuzz, process
from datetime import date
import io
import json
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from jsignature.utils import draw_signature
from .support_functions import make_all_report_pdfs

### Support Functions ###

def guest_from_internal_ID(internal_ID):
    '''
    Looks up guest account based on internal_ID and today's date.
    '''
    guest = Guest.objects.filter(internal_ID = internal_ID).values("guest_ID", "tefap_signature_date", "language_preference").first()
    return guest

### Views ###

def index(request):
    '''
    Landing page for guestbook_sign_in app
    '''   
    return render(request, 'index.html')

@login_required
def lookup_guest(request, guest_ID):
    '''
    Look up guest data from previous year. Used to pre-populate (some) fields for convenience.
    '''
    if date.today().month < 10:
        last_year = f'{date.today().year - 2}-{date.today().year - 1}'
    else:
        last_year = f'{date.today().year - 1}-{date.today().year}'
    guest = Guest.objects.filter(guest_ID = guest_ID).filter(year = last_year).filter(valid = True).values(
        "guest_ID", "first_name", "last_name", "county", "state", "number_in_household")[0]
    guest_json = {'guests' : guest}
    return JsonResponse(guest_json, safe=True)

def create_new_guest(request, language):
    '''
    Generate TEFAP form for new guests.
    '''
    if request.method == 'POST':
        form = GuestInput(request.POST)
        if form.is_valid():
            # Sanity check to ensure someone doesn't create the same guest twice on the same day.
            # Designed for the use case of "someone hit the back arrow from the weekly sign-in page after creating a new guest."
            existing_guests_match = list(Guest.objects.filter(valid = True,
                                                              first_name = form.cleaned_data['first_name'],
                                                              last_name = form.cleaned_data['last_name'],
                                                              county = form.cleaned_data['county'],
                                                              state = form.cleaned_data['state'],
                                                              number_in_household = form.cleaned_data['number_in_household'],
                                                              tefap_signature_date = date.today()).values())

            if len(existing_guests_match) > 0:
                # Non-descript response to prevent someone identifying existing guests by submitting random information.
                return HttpResponse("This guest could not be processed. Please contact the web administrator for assistance.")

            # If the "return" statement above isn't thrown, we assume the guest is not a duplicate. 
            # Create a new guest ID if one is not provided manually.
            year = f'{date.today().year - 1}-{date.today().year}' if (date.today().month < 10) else f'{date.today().year}-{date.today().year + 1}'
            if form.cleaned_data['guest_ID'] == None:
                if len(Guest.objects.values_list('guest_ID', flat = True)) == 0: 
                    guest_id = 1
                else: 
                    guest_id = max(Guest.objects.values_list('guest_ID', flat = True)) + 1
            else:
                # If there is already a guest with the manually-selected ID in the system for this fiscal year, assign a new guest ID
                guest_id = form.cleaned_data['guest_ID']
                if len(Guest.objects.filter(guest_ID = guest_id).filter(year = year).filter(valid = True)) > 0:
                    guest_id = max(Guest.objects.values_list('guest_ID', flat = True)) + 1

            # Add new guest to database
            new_guest = Guest(valid = True,
                              guest_ID = guest_id,
                              first_name = form.cleaned_data['first_name'],
                              last_name = form.cleaned_data['last_name'],
                              city = form.cleaned_data['city'],
                              county = form.cleaned_data['county'],
                              state = form.cleaned_data['state'],
                              number_in_household = form.cleaned_data['number_in_household'],
                              authorized_representative_1 = form.cleaned_data['authorized_representative_1'],
                              authorized_representative_2 = form.cleaned_data['authorized_representative_2'],
                              tefap_signature_date = date.today(),
                              tefap_signature = form.cleaned_data['tefap_signature'],
                              language_preference = language,
                              year = year,
                              notes = None)
            new_guest.save()
            
            if (form.cleaned_data['authorized_representative_1'] == None) and (form.cleaned_data['authorized_representative_2'] == None):
                return HttpResponseRedirect(reverse('new_guest_created', kwargs = {'internal_ID' : new_guest.internal_ID}))
            else:
                return HttpResponseRedirect(reverse('linked_proxy_form', kwargs = {'language' : language, 'internal_ID' : new_guest.internal_ID}))
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

def linked_proxy_form(request, language, internal_ID):
    '''
    Abbreviated TEFAP proxy form; imports data from create_new_guest page.
    '''
    if request.method == 'POST':
        form = LinkedProxyInput(request.POST)
        if form.is_valid():
            new_linked_proxy = LinkedProxy(internal_ID = Guest(internal_ID = internal_ID),
                                           valid = True,
                                           fns = form.cleaned_data['fns'],
                                           monthly_income = form.cleaned_data['monthly_income'],
                                           proxy_signature_date = date.today(),
                                           proxy_signature = form.cleaned_data['proxy_signature'])
            new_linked_proxy.save()

            if request.user.is_authenticated:
                return HttpResponseRedirect(reverse('weekly_signatures', kwargs = {'language' : language, 'internal_ID' : internal_ID}))
            else:
                return HttpResponseRedirect(reverse('new_guest_created', kwargs = {'internal_ID' : internal_ID}))
    else:
        form = LinkedProxyInput()

    context = {'form' : form, 'today' : date.today()}

    if language == 'English':
        html = 'linked_proxy_english.html'
    else:
        html = 'linked_proxy_spanish.html'
    
    return render(request, html, context = context)

def new_guest_created(request, internal_ID):
    '''
    Landing page after a new guest is created and TEFAP form is built. Contains options to proceed to weekly sign-in if 
    user is logged in or return to home page if user is not signed in.
    '''
    guest_ID = guest_from_internal_ID(internal_ID)['guest_ID']
    context = {'guest_ID' : guest_ID}
    return render(request, 'new_guest_created.html', context = context)

@login_required
def sign_in(request):
    '''
    Sign in an existing guest.
    '''
    already_signed_in = list(SignIn.objects.filter(date = date.today()).values_list('internal_ID', flat = True))
    current_year = f'{date.today().year - 1}-{date.today().year}' if (date.today().month < 10) else f'{date.today().year}-{date.today().year + 1}'
    if request.method == 'POST':
        form = SearchBar(request.POST)
        if form.is_valid():
            search_string = form.cleaned_data['name_search']
    
            # If search string is a guest ID, just return that guest!
            try:
                search_string = int(search_string)
                candidates = pd.DataFrame(Guest.objects.exclude(internal_ID__in = already_signed_in).filter(
                    guest_ID = search_string).filter(year = current_year).filter(valid = True).values())
                if candidates.empty:
                    matches_iter = pd.DataFrame(None, columns = ['first_name', 'last_name', 'guest_ID', 'internal_ID']).itertuples()
                else:
                    matches_iter = candidates[['first_name', 'last_name', 'guest_ID', 'internal_ID']].itertuples()
                
            except:
                candidates = pd.DataFrame(Guest.objects.exclude(internal_ID__in = already_signed_in).filter(
                    year = current_year).filter(valid = True).values())
                names = candidates['first_name'] + ' ' + candidates['last_name']
                fuzzy_search = process.extract(search_string, 
                                               names.values.tolist(),
                                               scorer = fuzz.token_set_ratio, 
                                               limit = 20)          
                
                matches = candidates[names.isin(list(dict(fuzzy_search).keys()))]
                matches_iter = matches[['first_name', 'last_name', 'guest_ID', 'internal_ID']].itertuples()
                
            context = {'searchbar' : form,
                       'guests' : matches_iter}
            return render(request, 'sign_in.html', context = context)  
    else:
        form = SearchBar()
        context = {'searchbar' : form,
                   'guests' : Guest.objects.exclude(internal_ID__in = already_signed_in).filter(year = current_year).filter(valid = True).values()}
    return render(request, 'sign_in.html', context = context)

@login_required
def weekly_signatures(request, language, internal_ID):
    '''
    Equivalent to signing the back of a TEFAP form.
    '''
    current_year = f'{date.today().year - 1}-{date.today().year}' if (date.today().month < 10) else f'{date.today().year}-{date.today().year + 1}'
    guest = Guest.objects.get(internal_ID = internal_ID)
    unlinkedProxy = UnlinkedProxy.objects.filter(internal_ID = internal_ID)
    
    pickup_choices = [(f'{guest.first_name} {guest.last_name}', f'{guest.first_name} {guest.last_name}')]

    # If an unlinked proxy is available, add the proxy names
    if len(list(unlinkedProxy)) > 0:
        u = unlinkedProxy.first() # Due to internal ID matching, there will be only one
        if u.authorized_representative_1 not in ['', None]:
            pickup_choices.append((f"{u.authorized_representative_1}", f"{u.authorized_representative_1}"))
        if u.authorized_representative_2 not in ['', None]:
            pickup_choices.append((f"{u.authorized_representative_2}", f"{u.authorized_representative_2}"))

    # Continue adding proxy names from the original guest account, up to a total of (one account owner + two proxies)
    if len(pickup_choices) < 3:
        if guest.authorized_representative_1 not in ['', None]:
            pickup_choices.append((f'{guest.authorized_representative_1}', f'{guest.authorized_representative_1}'))
    if len(pickup_choices) < 3:
        if guest.authorized_representative_2 not in ['', None]:
            pickup_choices.append((f'{guest.authorized_representative_2}', f'{guest.authorized_representative_2}'))
    
    if request.method == 'POST':
        form = SignInInput(request.POST)
        form.fields['who_performed_pickup'].choices = pickup_choices

        if form.is_valid():
            
            # Sanity check to ensure someone doesn't sign in the same guest twice. 
            # No one with the same {internal_ID_id} should sign in twice in one day.
            today_sign_ins_match = list(SignIn.objects.filter(date = date.today(), 
                                                              internal_ID_id = internal_ID).values())
            if len(today_sign_ins_match) > 0:
                eligible = today_sign_ins_match[0]['tefap_eligible']
                return HttpResponseRedirect(reverse('submission_complete', kwargs = {'tefap_flag' : eligible, 'internal_ID' : internal_ID}))
            
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
                                 valid = True,
                                 date = date.today(), 
                                 who_performed_pickup = form.cleaned_data['who_performed_pickup'],
                                 signature = form.cleaned_data['signature'],
                                 fns = fns,
                                 number_in_household = num_in_hh,
                                 yearly_income = yi,
                                 monthly_income = mi,
                                 weekly_income = wi,
                                 tefap_eligible = eligible,
                                 agency_representative_signature = form.cleaned_data['agency_representative_signature'])
            new_sign_in.save()
            return HttpResponseRedirect(reverse('submission_complete', kwargs = {'tefap_flag' : eligible, 'internal_ID' : internal_ID}))
        
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

@login_required    
def submission_complete(request, tefap_flag, internal_ID): 
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
    
    guest_ID = guest_from_internal_ID(internal_ID)['guest_ID']
    context = {'flag_english' : flag_english,
               'instructions_english' : instructions_english,
               'flag_spanish' : flag_spanish,
               'instructions_spanish' : instructions_spanish,
               'guest_ID' : guest_ID}
    
    return render(request, 'submission_complete.html', context = context)

@login_required
def sign_out(request):
    '''
    Go to the Django admin page. Here, you can sign out guests and edit accounts' metadata.
    '''
    return HttpResponseRedirect(reverse('admin:index'))

def unlinked_proxy_form(request):
    '''
    Submit a proxy form unattached to a new guest; intended to be used by individuals who need to remotely
    approve new proxy individuals to pick up for them.
    '''
    if request.method == 'POST':
        form = UnlinkedProxyInput(request.POST)
        if form.is_valid():
            
            new_unlinked_proxy = UnlinkedProxy(valid = True,
                                               first_name = form.cleaned_data['first_name'],
                                               last_name = form.cleaned_data['last_name'],
                                               city = form.cleaned_data['city'],
                                               county = form.cleaned_data['county'],
                                               state = form.cleaned_data['state'],
                                               number_in_household = form.cleaned_data['number_in_household'],
                                               fns = form.cleaned_data['fns'],
                                               monthly_income = form.cleaned_data['monthly_income'],
                                               authorized_representative_1 = form.cleaned_data['authorized_representative_1'],
                                               authorized_representative_2 = form.cleaned_data['authorized_representative_2'],
                                               proxy_signature_date = date.today(),
                                               proxy_signature = form.cleaned_data['proxy_signature'],
                                               guest_bestguess = form.cleaned_data['guest_bestguess'])
            new_unlinked_proxy.save()
            return HttpResponseRedirect(reverse('unlinked_proxy_successful'))

    else:
        form = UnlinkedProxyInput()

    context = {'form' : form,
               'today' : date.today(),
               }

    return render(request, 'unlinked_proxy_form.html', context = context)
    
def unlinked_proxy_successful(request):
    '''
    Information-only screen to tell guests their unlinked proxy form was uploaded.
    '''
    return render(request, 'unlinked_proxy_successful.html', context = {})

@login_required
def generate_report(request):
    '''
    Summary statistics and sign-in records from the last day.
    '''
    today_signins = pd.DataFrame(SignIn.objects.filter(date = date.today()).values())
    
    if today_signins.empty:
        
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
        if not new_guests.empty: new_guests = new_guests.merge(right = today_signins, left_on = 'internal_ID', right_on = 'internal_ID_id', how = 'left')
        
        context = {'tefap_guests_count' : len(today_signins[today_signins['tefap_eligible'] == 'Yes']),
                   'new_tefap_guests_count' : 0 if new_guests.empty else len(new_guests[new_guests['tefap_eligible'] == 'Yes']),
                   'tefap_guests_sum' : today_signins[today_signins['tefap_eligible'] == 'Yes']['number_in_household'].sum(),
                   'non_tefap_guests_count' : len(today_signins[today_signins['tefap_eligible'] == 'No']),
                   'new_non_tefap_guests_count' : 0 if new_guests.empty else len(new_guests[new_guests['tefap_eligible'] == 'No']),
                   'non_tefap_guests_sum' : today_signins[today_signins['tefap_eligible'] == 'No']['number_in_household'].sum(),
                   'total_guests_count' : len(today_signins),
                   'new_total_guests_count' : len(new_guests),
                   'total_guests_sum' : today_signins['number_in_household'].sum()
                   }
        
    return render(request, 'generate_report.html', context = context)

@login_required
def generate_report_database(request):
    '''
    Download the entire existing database as an Excel file.
    '''
    guests = pd.DataFrame(Guest.objects.values())
    sign_ins = pd.DataFrame(SignIn.objects.values())   
    linked_proxy = pd.DataFrame(LinkedProxy.objects.values())
    unlinked_proxy = pd.DataFrame(UnlinkedProxy.objects.values())

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer) as writer:
        guests.to_excel(writer, sheet_name = 'guests', index = False)
        sign_ins.to_excel(writer, sheet_name = 'sign_ins', index = False)
        linked_proxy.to_excel(writer, sheet_name = 'linked_proxy', index = False)
        unlinked_proxy.to_excel(writer, sheet_name = 'unlinked_proxy', index = False)
    buffer.seek(0)
    response = FileResponse(buffer, as_attachment = True, filename = 'database.xlsx') 
    return response

@login_required
def generate_report_pdf(request):
    '''
    Create TEFAP forms and proxy forms for all guests.
    '''
    return make_all_report_pdfs()

@login_required
def generate_alpha_list(request):
    '''
    Create list of all guests with guest ID, first name, and last name in PDF format.
    '''
    guests = pd.DataFrame(Guest.objects.values())
    guests = guests[['valid', 'guest_ID', 'first_name', 'last_name']].sort_values(
            by = ['valid', 'last_name', 'first_name', 'guest_ID'], 
            key = lambda col : col.str.lower() if col.name in ['last_name', 'first_name'] else col,
            ascending = [False, True, True, True]).to_dict(orient = 'records')
    context = {'guests' : guests}
    return render(request, 'generate_alpha_list.html', context = context)

@login_required
def generate_attendance_report(request):
	'''
	Generate table of weekly attendance across all weeks in database.
	'''
	# Retrieve sign-in data, filter to valid entries
	all_attendance = pd.DataFrame(SignIn.objects.values())
	a = all_attendance[all_attendance['valid'] == True][['date', 'tefap_eligible', 'number_in_household']]
	
	# If TEFAP eligibility unknown, assume "No"
	a['tefap_eligible'] = a['tefap_eligible'].fillna("No")
	
	# Insert month data
	d = pd.to_datetime(all_attendance['date']).apply(lambda x : pd.Timestamp(year = x.year, month = x.month, day = 1))
	a.insert(loc = 0, column = 'month', value = d)
		
	# Group by week and month
	week_attendance = a.groupby(by = ['date', 'tefap_eligible']).agg({'number_in_household' : ['count', 'sum']}).reset_index()
	week_attendance.columns = 'date', 'tefap_eligible', 'count', 'sum'
	week_attendance = week_attendance.sort_values(by = 'date')
	
	month_attendance = a.groupby(by = ['month', 'tefap_eligible']).agg({'number_in_household' : ['count', 'sum']}).reset_index()
	month_attendance.columns = 'month', 'tefap_eligible', 'count', 'sum'
	month_attendance = month_attendance.sort_values(by = 'month')
	
	# Helper function to either extract data if it exists from a Pandas dataframe, or return zero if it doesn't
	def extract(df):
		if len(df) == 0: return 0
		else: return int(df.iloc[0])
	
	# Helper function to convert a given week or month slice of a dataframe into TEFAP "Not Eligible", "Eligible", and "Total" components
	def df_slice(df):
		no_count = extract(df[df['tefap_eligible'] == 'No']['count'])
		no_sum = extract(df[df['tefap_eligible'] == 'No']['sum'])
		yes_count = extract(df[df['tefap_eligible'] == 'Yes']['count'])
		yes_sum = extract(df[df['tefap_eligible'] == 'Yes']['sum'])
		return {'no_count' : no_count, 'no_sum' : no_sum, 'yes_count' : yes_count, 'yes_sum' : yes_sum, 'total_count' : no_count + yes_count, 'total_sum' : no_sum + yes_sum}
		
	# Assemble HTML table. This code needs to be optimized!
	html_data = []
	current_month = month_attendance['month'].iloc[0]
	
	for week in sorted(week_attendance['date'].unique()):
		
		# Check month. If month has changed, print previous month's total before starting new month's weekly data
		new_month = pd.Timestamp(year = week.year, month = week.month, day = 1)
				
		if new_month > current_month:
			current_month = new_month # Update month counter
			m = month_attendance[month_attendance['month'] == new_month]
			s = df_slice(m)
			html_data.append({'date' : f'{new_month.month_name()} {new_month.year}', 'category' : 'TEFAP Eligible', 'head_count' : s['yes_count'], 'total_people_served' : s['yes_sum']})
			html_data.append({'date' : f'{new_month.month_name()} {new_month.year}', 'category' : 'Not TEFAP Eligible', 'head_count' : s['no_count'], 'total_people_served' : s['no_sum']})
			html_data.append({'date' : f'{new_month.month_name()} {new_month.year}', 'category' : 'Total', 'head_count' : s['total_count'], 'total_people_served' : s['total_sum']})
		
		# Proceed with extracting week data and sending to HTML table
		w = week_attendance[week_attendance['date'] == week]
		s = df_slice(w)
		html_data.append({'date' : f'{week.strftime("%m-%d-%Y")}', 'category' : 'TEFAP Eligible', 'head_count' : s['yes_count'], 'total_people_served' : s['yes_sum']})
		html_data.append({'date' : f'{week.strftime("%m-%d-%Y")}', 'category' : 'Not TEFAP Eligible', 'head_count' : s['no_count'], 'total_people_served' : s['no_sum']})
		html_data.append({'date' : f'{week.strftime("%m-%d-%Y")}', 'category' : 'Total', 'head_count' : s['total_count'], 'total_people_served' : s['total_sum']})

	return render(request, 'generate_attendance_report.html', context = {'html_data' : html_data})

