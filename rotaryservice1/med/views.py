# Create your views here.
from django.shortcuts import render, redirect,get_object_or_404
from .models import *
from datetime import datetime
from django.contrib import messages
from django.http import JsonResponse
# Create your views here.
import random
import json
from .models import *
from django.contrib import messages
import pandas as pd



# -----------------------------
# Registration Step 1
# -----------------------------
def registration1(request):
    # return redirect("https://medicalcamp.rotarykodungallur.org/")
    """
    Initial registration: select user type and verify 4-digit code if required.
    """
    if request.method == "POST":
        usertype = request.POST.get("usertype")
        code = request.POST.get("code", "").strip()

        # --- ASHA WORKER LOGIN ---
        if usertype == "asha":
            try:
                worker = ashaworker.objects.get(code=code)
                request.session['usertype'] = 'asha'
                request.session['asha_name'] = worker.name
                request.session['asha_code'] = worker.code
                request.session['asha_id'] = worker.id
                request.session.modified = True
                return redirect('registration2')
            except ashaworker.DoesNotExist:
                return render(request, 'registration/registration1.html', {
                    'error': "Invalid Code. Please try again."  # Malayalam error message
                })

        # --- OFFICIAL USER LOGIN ---
        elif usertype == "official":
            try:
                user = officialuser.objects.get(code=code)
                request.session.flush()
                request.session['usertype'] = 'official'
                request.session['official_name'] = user.name
                request.session['official_code'] = user.code
                request.session['official_id'] = user.id
                request.session.modified = True
                return redirect('registration2')
            except officialuser.DoesNotExist:
                return render(request, 'registration/registration1.html', {
                    'error': "Invalid Code. Please try again."
                })

        # --- DEFAULT (Public) ---
        else:
            request.session['usertype'] = 'public'
            return redirect('registration2')

    return render(request, 'registration/registration1.html')


# -----------------------------
# Registration Step 2
# -----------------------------
def registration2(request):
    """
    Patient contact number entry.
    Accessible only if session exists from registration1.
    Works for both ASHA Workers and Official Users.
    """
    usertype = request.session.get('usertype')
    asha_name = request.session.get('asha_name')
    asha_code = request.session.get('asha_code')
    asha_id = request.session.get('asha_id')
    official_name = request.session.get('official_name')
    official_code = request.session.get('official_code')

    # Redirect if not logged in properly
    if usertype not in ['asha', 'official']:
        return redirect('registration1')

    # Display name for UI
    display_name = asha_name if usertype == 'asha' else official_name

    # Build department data and check limits
    dept_limits = []
    depts = department.objects.all()
    for dept in depts:

        if usertype == 'asha' and asha_id:
            added_count = patients.objects.filter(
                department=str(dept.id),
                added_by=str(asha_id),
                role='asha',
                isdeleted=0
            ).count()
            limit = int(dept.asha_limit) if dept.asha_limit and str(dept.asha_limit).isdigit() else 0

            dept_limits.append({
                'department': dept.department,
                'added': added_count,
                'limit': limit
            })

        elif usertype == 'official':
            total_registered = patients.objects.filter(
                department=str(dept.id),
                role='official',
                isdeleted=0
            ).count()
            total_limit = int(dept.rotary_limit) if dept.rotary_limit and str(dept.rotary_limit).isdigit() else 0

            dept_limits.append({
                'department': dept.department,
                'total_registered': total_registered,
                'total_limit': total_limit
            })

    # ✅ Check if all department limits are reached
    if usertype == 'asha':
        all_limits_reached = all(
            item['added'] >= item['limit'] for item in dept_limits if item['limit'] > 0
        )
    elif usertype == 'official':
        all_limits_reached = all(
            item['total_registered'] >= item['total_limit'] for item in dept_limits if item['total_limit'] > 0
        )
    else:
        all_limits_reached = False

    # POST request handling
    if request.method == "POST" and not all_limits_reached:
        contact = request.POST.get("contact", "").strip()

        # Validate contact number
        if not contact.isdigit() or len(contact) != 10:
            return render(request, 'medicalcamp/registration2.html', {
                'usertype': usertype,
                'display_name': display_name,
                'departments_data': dept_limits,
                'error': "Enter a valid 10-digit patient contact number.",
                'all_limits_reached': all_limits_reached,
            })

        # Save to session
        request.session['patient_contact'] = contact
        request.session.set_expiry(15 * 60)

        return redirect('registration3')

    return render(request, 'registration/registration2.html', {
        'usertype': usertype,
        'display_name': display_name,
        'departments_data': dept_limits,
        'all_limits_reached': all_limits_reached,
    })



# -----------------------------
# Registration Step 3
# -----------------------------
def registration3(request):
    """
    Patient registration form.
    Works for ASHA, Official, and Public users.
    Stores 'role' and 'added_by' accordingly.
    Handles agebelow1 checkbox.
    """
    usertype = request.session.get('usertype')  # 'asha', 'official', or None
    asha_id = request.session.get('asha_id')
    official_id = request.session.get('official_id')
    asha_name = request.session.get('asha_name')
    official_name = request.session.get('official_name')
    patient_contact = request.session.get('patient_contact')

    # Ensure proper session (must come via registration2)
    if not patient_contact:
        return redirect('registration2')

    # Display name based on usertype
    display_name = asha_name if usertype == 'asha' else official_name

    # --- Departments and available departments based on limits ---
    departments_qs = department.objects.all()
    available_departments = []

    for dept in departments_qs:
        dept_count = patients.objects.filter(department=str(dept.id), isdeleted=0).count()
        dept_limit = int(dept.setlimit) if dept.setlimit and dept.setlimit.isdigit() else 0
        if dept_limit > 0 and dept_count >= dept_limit:
            continue

        # User-specific counts
        user_count = 0
        user_limit = 0

        if usertype == 'asha' and asha_id:
            user_count = patients.objects.filter(
                department=str(dept.id),
                added_by=str(asha_id),
                role='asha',
                isdeleted=0
            ).count()
            user_limit = int(dept.asha_limit) if dept.asha_limit and dept.asha_limit.isdigit() else 0

        elif usertype == 'official' and official_id:
            total_official_count = patients.objects.filter(
                department=str(dept.id),
                role='official',
                isdeleted=0
            ).count()
            rotary_limit = int(dept.rotary_limit) if dept.rotary_limit and dept.rotary_limit.isdigit() else 0
            if rotary_limit > 0 and total_official_count >= rotary_limit:
                continue

        if user_limit > 0 and user_count >= user_limit:
            continue

        available_departments.append(dept)

    # --- Subdepartments ---
    subdepartments = subdepartment.objects.all()
    sub_map = {}
    for sub in subdepartments:
        sub_map.setdefault(sub.department_id, []).append(sub)

    if request.method == "POST":
        name = request.POST.get('name', '').strip()
        age = request.POST.get('age', '').strip()
        gender = request.POST.get('gender', '').strip()
        dept_id = request.POST.get('department')
        sub_id = request.POST.get('subdepartment')

        # --- Handle agebelow1 hidden input submitted via JS ---
        agebelow1 = 1 if request.POST.get('ageBelow1') == 'on' else 0
        if agebelow1:
            age = '0'

        # --- Validation ---
        errors = []
        if not name:
            errors.append("Patient name is required.")
        if not gender:
            errors.append("Gender is required.")
        if not patient_contact or not patient_contact.isdigit() or len(patient_contact) != 10:
            errors.append("Patient contact number is missing or invalid.")
        if not dept_id:
            errors.append("Select a department.")
        elif sub_map.get(int(dept_id)) and not sub_id:
            errors.append("Select a subdepartment.")

        # Department limit checks
        if dept_id:
            try:
                dept = department.objects.get(id=dept_id)
                current_count = patients.objects.filter(department=str(dept_id), isdeleted=0).count()
                dept_limit = int(dept.setlimit) if dept.setlimit and dept.setlimit.isdigit() else 0
                if dept_limit > 0 and current_count >= dept_limit:
                    errors.append(f"{dept.department} വിഭാഗത്തിൽ രജിസ്ട്രേഷൻ അവസാനിച്ചു. പരമാവധി {dept_limit} പേർ എത്തിയിരിക്കുന്നു.")

                if usertype == 'asha' and asha_id:
                    asha_count = patients.objects.filter(
                        department=str(dept_id),
                        added_by=str(asha_id),
                        role='asha',
                        isdeleted=0
                    ).count()
                    asha_limit = int(dept.asha_limit) if dept.asha_limit and dept.asha_limit.isdigit() else 0
                    if asha_limit > 0 and asha_count >= asha_limit:
                        errors.append(f"{dept.department} വിഭാഗത്തിൽ നിങ്ങളുടെ രജിസ്ട്രേഷൻ പരിധി ({asha_limit}) കഴിഞ്ഞിരിക്കുന്നു.")

                if usertype == 'official' and official_id:
                    total_official_count = patients.objects.filter(
                        department=str(dept_id),
                        role='official',
                        isdeleted=0
                    ).count()
                    rotary_limit = int(dept.rotary_limit) if dept.rotary_limit and dept.rotary_limit.isdigit() else 0
                    if rotary_limit > 0 and total_official_count >= rotary_limit:
                        errors.append(f"{dept.department} വിഭാഗത്തിൽ രജിസ്ട്രേഷൻ അവസാനിച്ചു. റോട്ടറി പരിധി ({rotary_limit}) എത്തിയിരിക്കുന്നു.")

            except department.DoesNotExist:
                errors.append("Invalid department selected.")

        if errors:
            error_message = " ".join(errors)
            return render(request, 'registration/registration3.html', {
                'departments': available_departments,
                'sub_map': sub_map,
                'display_name': display_name,
                'error': error_message,
                'alert_message': error_message,
            })

        # --- Duplicate check (exclude deleted) ---
        existing_patient = patients.objects.filter(
            name__iexact=name.strip(),
            contact=patient_contact.strip(),
            department=str(dept_id),
            isdeleted=0
        ).first()

        if existing_patient:
            error_message = "ഈ രോഗി ഈ ഡിപ്പാർട്ട്മെൻ്റിൽ നേരത്തെ രജിസ്റ്റർ ചെയ്തതാണ്!"
            return render(request, 'registration/registration3.html', {
                'departments': available_departments,
                'sub_map': sub_map,
                'display_name': display_name,
                'error': error_message,
                'alert_message': error_message,
            })

        # --- Generate code and security pin ---
        while True:
            code = f"{random.randint(1000, 9999)}"
            if not patients.objects.filter(code=code, isdeleted=0).exists():
                break
        securitypin = f"{random.randint(100, 999)}"

        # Determine added_by and role
        if usertype == 'asha' and asha_id:
            added_by = str(asha_id)
            role = 'asha'
        elif usertype == 'official' and official_id:
            added_by = str(official_id)
            role = 'official'
        else:
            added_by = 'Public'
            role = 'public'

        # Save patient
        patient = patients.objects.create(
            name=name,
            contact=patient_contact,
            age=age,
            gender=gender,
            code=code,
            securitypin=securitypin,
            department=str(dept_id),
            subdepartment=str(sub_id) if sub_id else "",
            added_by=added_by,
            role=role,
            followup=0,
            followupdate=None,
            remarks="",
            confirm_entry=0,
            agebelow1=agebelow1,
            isdeleted=0
        )

        # Store in session for success page
        request.session['patient_code'] = code
        request.session['patient_pin'] = securitypin
        request.session['patient_name'] = name
        request.session['patient_department'] = dept.department

        return redirect('registrationsuccess')

    # GET Load
    return render(request, 'registration/registration3.html', {
        'departments': available_departments,
        'sub_map': sub_map,
        'display_name': display_name,
    })



# -----------------------------
# Registration Success
# -----------------------------
def registrationsuccess(request):
    """
    Display generated patient code and security pin.
    """
    code = request.session.get('patient_code')
    pin = request.session.get('patient_pin')

    patient_name = request.session.get('patient_name')
    patient_department = request.session.get('patient_department')

    # Clear session values
    request.session.pop('patient_code', None)
    request.session.pop('patient_pin', None)

    return render(request, 'registration/registrationsuccess.html', {
        'code': code,
        'pin': pin,
        'patient_name': patient_name,
        'patient_department': patient_department,
    })



# -----------------------------
# Dashboard & Confirmation
# -----------------------------
# def dashboard(request):
#     return render(request,'med_admin/dashboard.html')



def confirmation(request):
    reg_id = request.session.get('registration_id')
    if not reg_id:
        # User not logged in, redirect to login page
        return redirect('confirmlogin')

    # Optional: fetch the registration record if you need it in the template
    reg = registration.objects.get(id=reg_id)
    return render(request, 'confirmation/confirmation.html',{'reg':reg})




def confirmationsuccess(request):
    state = request.GET.get("state")
    
    patient_data = request.session.get("patient_success", None)

    if not patient_data:
        patient_data = {
            "name": None,
            "dept": None,
            "token": None,
        }

    context = {
        "state": state,
        **patient_data
    }

    return render(request, "confirmation/confirmationsuccess.html", context)




def search_patients(request):
    code = request.GET.get('code', '').strip()
    contact = request.GET.get('contact', '').strip()
    name = request.GET.get('name', '').strip()

    qs = patients.objects.all().exclude(isdeleted=1)

    if code:
        qs = qs.filter(code=code)
    elif contact:
        qs = qs.filter(contact=contact)
    elif name:
        qs = qs.filter(name__icontains=name)

    results = []
    for p in qs:
        # Lookup department and subdepartment
        dept_name = None
        subdept_name = None
        dept_token = None

        if p.department:
            dept = department.objects.filter(id=p.department).first()
            if dept:
                dept_name = dept.department
                dept_token = dept.token

        if p.subdepartment:
            sub = subdepartment.objects.filter(id=p.subdepartment).first()
            subdept_name = sub.sub if sub else None

        results.append({
            "id": p.id,
            "code": p.code,
            "name": p.name,
            "contact": p.contact,
            "department": dept_name,
            "dept_token": dept_token,
            "subdepartment": subdept_name,
            "securitypin": p.securitypin,
            "confirm_entry": p.confirm_entry,
            "followup": p.followup,
            "consulted":p.consulted,
            "medicineissued":p.medicineissued
        })
        
    return JsonResponse({"results": results})




from django.shortcuts import render
from django.db.models import Max
from .models import patients, department

def verify_pin(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            patient_id = data.get("patient_id")
            entered_pin = data.get("pin")

            if not patient_id or not entered_pin:
                return JsonResponse({"success": False, "error": "Missing patient_id or pin"})

            try:
                patient = patients.objects.get(id=patient_id)
            except patients.DoesNotExist:
                return JsonResponse({"success": False, "error": "Patient not found"})

            if patient.securitypin == entered_pin:
                # Assign token if not already confirmed
                if patient.confirm_entry == 0:
                    last_token = patients.objects.filter(
                        department=patient.department,
                        confirm_entry=1
                    ).aggregate(Max("token_no"))["token_no__max"]
                    next_token = (last_token or 0) + 1
                    patient.token_no = next_token
                    patient.confirm_entry = 1

                    # --- Save confirmed_by from logged-in session ---
                    reg_id = request.session.get("registration_id")
                    if reg_id:
                        patient.confirmed_by = reg_id  # Assuming FK or IntegerField
                    patient.save()

                # Get department info
                try:
                    dept_obj = department.objects.get(id=int(patient.department))
                    dept_name = dept_obj.department
                    dept_token = dept_obj.token
                except department.DoesNotExist:
                    dept_name = patient.department
                    dept_token = ""

                # Save in session for success page
                request.session["patient_success"] = {
                    "name": patient.name,
                    "dept": dept_name,
                    "dept_token": dept_token,
                    "token": patient.token_no
                }

                return JsonResponse({
                    "success": True,
                    "token_no": patient.token_no,
                    "name": patient.name,
                    "department": dept_name,
                    "department_token": dept_token,
                    "confirm_entry": patient.confirm_entry,
                    "followup": patient.followup
                })
            else:
                return JsonResponse({"success": False, "error": "Invalid PIN"})

        except Exception as e:
            return JsonResponse({"success": False, "error": "Server error: " + str(e)})

    return JsonResponse({"success": False, "error": "Invalid request"})



def verify_securitypin(request):
    print('verify_securitypin')
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Invalid request"})

    try:
        data = json.loads(request.body.decode("utf-8"))
        patient_id = data.get("patient_id")
        entered_pin = data.get("pin")

        if not patient_id or not entered_pin:
            return JsonResponse({"success": False, "error": "Missing patient_id or pin"})

        try:
            patient = patients.objects.get(id=patient_id)
        except patients.DoesNotExist:
            return JsonResponse({"success": False, "error": "Patient not found"})

        if patient.securitypin != entered_pin:
            return JsonResponse({"success": False, "error": "Invalid PIN"})

        # Get department info
        try:
            dept_obj = department.objects.get(id=int(patient.department))
            dept_name = dept_obj.department
            dept_token = dept_obj.token
        except department.DoesNotExist:
            dept_name = patient.department
            dept_token = ""

        request.session["patient_success"] = {
            "name": patient.name,
            "dept": dept_name,
            "dept_token": dept_token,
            "token": patient.token_no
        }

        # Return all patient data
        return JsonResponse({
            "success": True,
            "name": patient.name,
            "contact": patient.contact,
            "department": dept_name,
            "department_token": dept_token,
            "token": patient.token_no,
            "confirm_entry": patient.confirm_entry,
            "followup": patient.followup
        })

    except Exception as e:
        return JsonResponse({"success": False, "error": f"Server error: {str(e)}"})



from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def mark_followup(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Invalid request"})

    try:
        data = json.loads(request.body)
        patient_id = data.get("patient_id")
        followup_value = data.get("followup")  # "Yes" or "No"

        patient = patients.objects.get(id=patient_id)

        # Mark consulted if checkbox checked or followup is yes
        if followup_value == "Yes":
            patient.followup = 1
            patient.consulted = 1
        else:
            # Even if followup is "No", mark consulted if checkbox was checked
            patient.consulted = 1
        
        reg_id = request.session.get("registration_id")
        patient.consulted_by = reg_id
        patient.save()
        return JsonResponse({"success": True})

    except patients.DoesNotExist:
        return JsonResponse({"success": False, "error": "Patient not found"})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


@csrf_exempt
def mark_medicine(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Invalid request"})

    try:
        data = json.loads(request.body)
        patient_id = data.get("patient_id")
        medicine_issued = data.get("medicine_issued", False)
        medicine_amount = data.get("medicine_amount")

        # Convert empty string or invalid numbers to None
        if medicine_amount in [None, ""]:
            medicine_amount = None
        else:
            medicine_amount = int(medicine_amount)

        patient = patients.objects.get(id=patient_id)

        # Update the patient record
        patient.medicineissued = 1 if medicine_issued else 0
        patient.medicineamount = medicine_amount  # will store NULL if None
        reg_id = request.session.get("registration_id")
        patient.medicineissued_by = reg_id
        patient.save()

        return JsonResponse({"success": True})

    except patients.DoesNotExist:
        return JsonResponse({"success": False, "error": "Patient not found"})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})
    


from django.core.paginator import Paginator


def patients_list(request):
    usertype = request.session.get("usertype")
    user_id = None

    # Determine logged-in user
    if usertype == "asha":
        user_id = request.session.get("asha_id")
        role_filter = 'asha'
    elif usertype == "official":
        user_id = request.session.get("official_id")
        role_filter = 'official'
    elif usertype == "spot":
        user_id = request.session.get("spot_id")
        role_filter = 'spot'
    else:
        return redirect("registration1")  # redirect to home/login if no session

    if not user_id:
        return redirect("registration1")

    # Fetch patients added by this user and matching role
    patients_qs = patients.objects.filter(
        added_by=str(user_id),
        role=role_filter
    ).order_by('-added_on').exclude(isdeleted=1)  

    # Fetch department and subdepartment mapping
    dept_dict = {str(d.id): d.department for d in department.objects.all()}
    subdept_dict = {str(s.id): s.sub for s in subdepartment.objects.all()}

    # Prepare a list with actual names + serial number
    patients_list_with_names = []
    for idx, p in enumerate(patients_qs, start=1):
        patients_list_with_names.append({
            'slno': idx,  # ✅ Serial number added here
            'name': p.name,
            'contact': p.contact,
            'code': p.code,
            'securitypin': p.securitypin,
            'department': dept_dict.get(p.department, "N/A"),
            'subdepartment': subdept_dict.get(p.subdepartment, ""),
        })

    # Pagination
    paginator = Paginator(patients_list_with_names, 10)  # 10 patients per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Fetch user display name
    display_name = (
        request.session.get("asha_name") if usertype == "asha"
        else request.session.get("official_name")
    )

    return render(request, "registration/patients_list.html", {
        "patients": page_obj,
        "total_patients": len(patients_list_with_names),
        "display_name": display_name,
        "usertype": usertype,
    })


from django.http import JsonResponse

def check_department_limit(request):
    dept_id = request.GET.get('department_id')
    usertype = request.session.get('usertype')
    asha_id = request.session.get('asha_id')

    if not dept_id:
        return JsonResponse({'success': False, 'message': 'Invalid department.'})

    try:
        dept = department.objects.get(id=dept_id)
        current_count = patients.objects.filter(department=dept_id).count()
        dept_limit = int(dept.setlimit) if dept.setlimit and dept.setlimit.isdigit() else 0

        # Check overall limit
        if dept_limit > 0 and current_count >= dept_limit:
            return JsonResponse({
                'success': False,
                'message': f"{dept.department} വിഭാഗത്തിൽ രജിസ്ട്രേഷൻ അവസാനിച്ചു. പരമാവധി {dept_limit} പേർ എത്തിയിരിക്കുന്നു."
            })

        # Check ASHA-specific limit
        if usertype == 'asha' and asha_id:
            asha_count = patients.objects.filter(department=dept_id, added_by=asha_id).count()
            asha_limit = int(dept.asha_limit) if dept.asha_limit and dept.asha_limit.isdigit() else 0
            if asha_limit > 0 and asha_count >= asha_limit:
                return JsonResponse({
                    'success': False,
                    'message': f"{dept.department} വിഭാഗത്തിൽ നിങ്ങളുടെ രജിസ്ട്രേഷൻ പരിധി ({asha_limit}) കഴിഞ്ഞിരിക്കുന്നു."
                })

        return JsonResponse({'success': True, 'message': ''})

    except department.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Invalid department.'})

from django.contrib import messages
def confirmlogin(request):
    if request.method == "POST":
        code = request.POST.get('code')
        if code:
            try:
                reg = registration.objects.get(code=code)
                # Save id in session
                request.session.flush()
                request.session['registration_id'] = reg.id
                return redirect('confirmation')  # Replace with your URL name
            except registration.DoesNotExist:
                messages.error(request, "Invalid code. Please try again.")
        else:
            messages.error(request, "Please enter a 4-digit code.")

    return render(request, 'confirmation/confirmlogin.html')


# -----------------------------
# Spot Registration Step 1
# -----------------------------
def spotregistration1(request):
    if request.method == "POST":
        code = request.POST.get('code')
        if code:
            try:
                reg = officialuser.objects.get(code=code)
                # Save id in session
                request.session.flush()
                request.session['usertype'] = 'spot'
                request.session['spot_id'] = reg.id
                request.session['spot_name'] = reg.name
                return redirect('spotregistration2')  # Replace with your URL name
            except officialuser.DoesNotExist:
                messages.error(request, "Invalid code. Please try again.")
        else:
            messages.error(request, "Please enter a 4-digit code.")

    return render(request, 'spot/spotregistration1.html')




# -----------------------------
# Spot Registration Form
# -----------------------------
def spotregistration2(request):
    """
    Step 2: Patient registration for spot officials.
    No limit per department — unlimited registrations allowed.
    Each entry stores added_by = session spot_id and role = 'spot'.
    """

    official_id = request.session.get('spot_id')
    official_name = request.session.get('spot_name')

    if not official_id:
        messages.error(request, "Please log in first.")
        return redirect('spotregistration1')

    # --- Department and subdepartment setup ---
    departments_qs = department.objects.all()
    subdepartments = subdepartment.objects.all()

    sub_map = {}
    for sub in subdepartments:
        sub_map.setdefault(sub.department_id, []).append(sub)

    if request.method == "POST":
        name = request.POST.get('name', '').strip()
        contact = request.POST.get('contact', '').strip()
        age = request.POST.get('age', '').strip()
        gender = request.POST.get('gender', '').strip()
        dept_id = request.POST.get('department')
        sub_id = request.POST.get('subdepartment')
        agebelow1 = 1 if request.POST.get('ageBelow1') == 'on' else 0
        if agebelow1:
            age = '0'

        # --- Validation ---
        errors = []
        if not name:
            errors.append("Patient name is required.")
        if not contact or not contact.isdigit() or len(contact) != 10:
            errors.append("Enter a valid 10-digit contact number.")
        if not gender:
            errors.append("Select gender.")
        if not dept_id:
            errors.append("Select a department.")
        elif sub_map.get(int(dept_id)) and not sub_id:
            errors.append("Select a subdepartment.")

        if errors:
            return render(request, 'spot/spotregistration2.html', {
                'departments': departments_qs,
                'sub_map': sub_map,
                'display_name': official_name,
                'error': " ".join(errors),
            })

        # --- Duplicate check ---
        existing_patient = patients.objects.filter(
            name__iexact=name,
            contact=contact,
            department=dept_id,
            added_by=official_id,
            role='spot'
        ).first()

        if existing_patient:
            return render(request, 'spot/spotregistration2.html', {
                'departments': departments_qs,
                'sub_map': sub_map,
                'display_name': official_name,
                'error': "Patient with the same name, contact, and department is already registered.",
            })

        # --- Generate unique patient code and pin ---
        while True:
            code = str(random.randint(1000, 9999))
            if not patients.objects.filter(code=code).exists():
                break
        securitypin = str(random.randint(100, 999))

        # --- Save patient record ---
        patient = patients.objects.create(
            name=name,
            contact=contact,
            age=age,
            gender=gender,
            code=code,
            securitypin=securitypin,
            department=str(dept_id),
            subdepartment=str(sub_id) if sub_id else "",
            added_by=str(official_id),
            role='spot',
            followup=0,
            followupdate=None,
            remarks="",
            confirm_entry=0,
            agebelow1=agebelow1
        )
        patient.save()

        # --- Store for success screen ---
        request.session['patient_code'] = code
        request.session['patient_pin'] = securitypin
        request.session['patient_name'] = name
        request.session['patient_department'] = department.objects.get(id=dept_id).department

        return redirect('spotregistrationsuccess')

    # --- GET render ---
    return render(request, 'spot/spotregistration2.html', {
        'departments': departments_qs,
        'sub_map': sub_map,
        'display_name': official_name,
    })


# -----------------------------
# Spot Registration Success
# -----------------------------
def spotregistrationsuccess(request):
    """
    Display generated patient code and security pin.
    """
    code = request.session.get('patient_code')
    pin = request.session.get('patient_pin')

    patient_name = request.session.get('patient_name')
    patient_department = request.session.get('patient_department')

    # Clear session values
    request.session.pop('patient_code', None)
    request.session.pop('patient_pin', None)

    return render(request, 'spot/spotregistrationsuccess.html', {
        'code': code,
        'pin': pin,
        'patient_name': patient_name,
        'patient_department': patient_department,
    })



# -----------------------------
# Admin Module
# -----------------------------
def dashboard(request):
    if 'type' in request.session:
        departments = department.objects.all()
        dept_stats = []
        labels = []
        enrolled_counts = []

        # Short English names for charts
        abbr_names = {
            'ഇ. എൻ. ടി. വിഭാഗം (ENT)': 'ENT',
            'ജനറൽ സർജറി വിഭാഗം (General Surgery)': 'General Surgery',
            'ശിശുരോഗവിഭാഗം (Pediatrics)': 'Pediatrics',
            'നേത്രരോഗ വിഭാഗം (Ophthalmology)': 'Ophthalmology',
            'ദന്തരോഗ വിഭാഗം (Dentistry)': 'Dentistry',
            'ജനറൽ മെഡിസിൻ വിഭാഗം (General Medicine)': 'General Medicine',
            'ന്യൂറോ ടെസ്റ്റ് (Neuro Test)': 'Neuro Test',
            'പക്ഷാഘാത വിഭാഗം (Stroke Medicine)': 'Stroke Medicine'
        }

        for dept in departments:
            limit = int(dept.setlimit)
            enrolled_count = patients.objects.filter(department=dept.id, isdeleted=0).count()
            percent = int((enrolled_count / limit) * 100) if limit > 0 else 0
            percent = min(percent, 100)  # cap at 100

            dept_stats.append({
                'name': dept.department,
                'limit': limit,
                'enrolled': enrolled_count,
                'percent': percent
            })
            labels.append(abbr_names.get(dept.department, dept.department))
            enrolled_counts.append(enrolled_count)

        # ✅ Total registrations across all departments
        total_registrations = sum(d['enrolled'] for d in dept_stats)

        context = {
            'dept_stats': dept_stats,
            'labels': labels,
            'enrolled_counts': enrolled_counts,
            'total_registrations': total_registrations,
        }

        return render(request, 'med_admin/dashboard.html', context)
    else:
        return redirect('login')

def desksuccess(request):
    success_data = request.session.get('registration_success')
    if not success_data:
        return redirect('ashaworkers')  # If no session, redirect to form

    # Clear the session data after fetching
    del request.session['registration_success']
    return render(request,'med_admin/desksuccess.html', {'user': success_data})


def ashaworkers(request):
    if 'type' in request.session:
        departments = department.objects.all()
        if request.method == "POST":
            name = request.POST.get('name', '').strip()
            phone = request.POST.get('phone', '').strip()
            role = request.POST.get('role')

            if role == "ashaworker":
                code = phone[-4:]  # last 4 digits, duplicates allowed

            elif role == "registration":
                # Generate unique code for registration
                while True:
                    code = str(random.randint(1000, 9999))
                    if not registration.objects.filter(code=code).exists():
                        break

            elif role == "followup":
                # Generate unique code for followup
                while True:
                    code = str(random.randint(1000, 9999))
                    if not followup.objects.filter(code=code).exists():
                        break

            if role == "ashaworker":
                ward = request.POST.get('ward')
                if ashaworker.objects.filter(contact=phone).exists():
                    messages.error(request, "Phone already exists for an ASHA worker.")
                    return redirect('ashaworkers')

                ashaworker.objects.create(
                    code=code,
                    name=name,
                    contact=phone,
                    ward=ward,
                    added_by="admin"
                )

            elif role == "registration":
                dept_id = request.POST.get('department')
                desk = request.POST.get('desk')

                if not dept_id or not desk:
                    messages.error(request, "Please select both Department and Desk.")
                    return redirect('ashaworkers')

                # Save department name instead of ID
                try:
                    dept_obj = department.objects.get(id=dept_id)
                    dept_name = dept_obj.department
                except department.DoesNotExist:
                    dept_name = ""

                registration.objects.create(
                    code=code,
                    name=name,
                    contact=phone,
                    dept=dept_id,
                    desk=desk,
                    added_by="admin"
                )

                # Save registration info in session for success page
                request.session['registration_success'] = {
                    'name': name,
                    'dept': dept_name,
                    'desk': desk,
                    'code': code
                }

                return redirect('desksuccess')  # Redirect to your success page

            elif role == "followup":
                dept_id = request.POST.get('department')
                followup.objects.create(
                    code=code,
                    name=name,
                    contact=phone,
                    added_by="admin",
                    department=str(dept_id)
                )
            else:
                messages.error(request, "Invalid role selected.")
                return redirect('ashaworkers')

            messages.success(request, f"{role.capitalize()} added successfully with code {code}.")
            return redirect('ashaworkers')

        return render(request, 'med_admin/ashaworker.html', {'departments': departments})
    else:
        return redirect('login')



def upload_ashaworkers(request):
    if request.method == "POST":
        excel_file = request.FILES.get("excel_file")
        if not excel_file:
            messages.error(request, "Please select an Excel file to upload.")
            return redirect("ashaworkers")

        # ✅ Validate file type
        if not excel_file.name.endswith((".xlsx", ".xls")):
            messages.error(request, "Only Excel files (.xlsx, .xls) are allowed.")
            return redirect("ashaworkers")

        # ✅ Read file
        try:
            df = pd.read_excel(excel_file)
        except Exception as e:
            messages.error(request, f"Invalid file format: {e}")
            return redirect("ashaworkers")

        # ✅ Check for required columns and order
        expected_cols = ["name", "contact", "ward"]
        if list(df.columns[:3]) != expected_cols:
            messages.error(request, "Invalid column order. Must be: name, contact, ward.")
            return redirect("ashaworkers")

        added_count = 0
        duplicate_count = 0

        for _, row in df.iterrows():
            name = str(row["name"]).strip()
            contact = str(row["contact"]).strip()
            ward = str(row["ward"]).strip()

            if not (name and contact and ward):
                continue  # skip incomplete rows

            if ashaworker.objects.filter(contact=contact).exists():
                duplicate_count += 1
                continue

            code = contact[-4:]
            ashaworker.objects.create(
                name=name,
                contact=contact,
                ward=ward,
                code=code,
                added_by="admin"
            )
            added_count += 1

        messages.success(
            request,
            f"Upload completed — {added_count} added, {duplicate_count} duplicates skipped."
        )
        return redirect("ashaworkers")

    messages.error(request, "Invalid request.")
    return redirect("ashaworkers")



def patient_report(request):
    if 'type' in request.session:
        patient_list = patients.objects.filter(isdeleted=0).order_by('-id')

        # Map department names
        departments_map = {str(d.id): d.department for d in department.objects.all()}

        # Map added_by names and ward for both Asha and Official
        asha_map = {str(a.id): {"name": a.name, "ward": a.ward} for a in ashaworker.objects.all()}
        official_map = {str(o.id): o.name for o in officialuser.objects.all()}

        if request.method == "POST" and request.headers.get('x-requested-with') == 'XMLHttpRequest':
            dept_id = request.POST.get("department")
            followup = request.POST.get("followup")
            addedby = request.POST.get("addedby")
            rotorian_id = request.POST.get("rotorian")
            addedby_type = request.POST.get("addedby_type")
            spot = request.POST.get("spot")

            if dept_id:
                patient_list = patient_list.filter(department=dept_id)
            if followup in ["true", "True", True, "1"]:
                patient_list = patient_list.filter(followup=True)
            if spot in ["true", "True", True, "1", 1]:
                patient_list = patient_list.filter(role='spot')
            if addedby_type == "asha" and addedby:
                patient_list = patient_list.filter(added_by=addedby, role='asha')
            elif addedby_type == "rotarian" and rotorian_id:
                patient_list = patient_list.filter(added_by=rotorian_id, role='official')
            elif addedby_type == "asha":
                patient_list = patient_list.filter(role='asha')
            elif addedby_type == "rotarian":
                patient_list = patient_list.filter(role='official')

            # Set display names
            for p in patient_list:
                p.department_name = departments_map.get(str(p.department), p.department)
                if p.role == 'asha':
                    asha_info = asha_map.get(str(p.added_by), {})
                    ward = asha_info.get("ward", "")
                    name = asha_info.get("name", p.added_by)
                    p.added_by_name = f"{name}-{ward}" if ward else name
                elif p.role == 'official':
                    p.added_by_name = f"{official_map.get(str(p.added_by), p.added_by)}"
                elif p.role == 'spot':
                    p.added_by_name = f"{official_map.get(str(p.added_by), p.added_by)}"
                else:
                    p.added_by_name = p.added_by

            table_html = render(
                request, "med_admin/report_patients_rows.html",
                {"patients": patient_list}
            ).content.decode("utf-8")
            return JsonResponse({"table_html": table_html})

        # For initial page load
        for p in patient_list:
            p.department_name = departments_map.get(str(p.department), p.department)
            if p.role == 'asha':
                asha_info = asha_map.get(str(p.added_by), {})
                ward = asha_info.get("ward", "")
                name = asha_info.get("name", p.added_by)
                p.added_by_name = f"{name}-{ward}" if ward else name
            elif p.role == 'official':
                p.added_by_name = f"{official_map.get(str(p.added_by), p.added_by)}"
            elif p.role == 'spot':
                p.added_by_name = f"{official_map.get(str(p.added_by), p.added_by)}"
            else:
                p.added_by_name = p.added_by

        departments_all = department.objects.all()
        ashaworker_all = ashaworker.objects.all().values("id", "name", "ward")
        ashaworkers_json = list(ashaworker_all)
        rotarians_all = officialuser.objects.all().values("id", "name")
        rotarians_json = list(rotarians_all)

        return render(
            request, 
            "med_admin/report_patients.html", 
            {
                "patients": patient_list, 
                "departments": departments_all,
                "ashaworkers_json": ashaworkers_json,
                "rotarians_json": rotarians_json
            }
        )
    else:
        return redirect('login')
    


def spotregister_report(request):
    if 'type' in request.session:
        patient_list = patients.objects.filter(role='spot',isdeleted=0).order_by('-id')
        officialusers = officialuser.objects.all().values("id", "name")
        departments_all = department.objects.all()

        # Map department names
        departments_map = {str(d.id): d.department for d in department.objects.all()}

        if request.method == "POST" and request.headers.get('x-requested-with') == 'XMLHttpRequest':
            dept_id = request.POST.get("department")
            followup = request.POST.get("followup")
            addedby = request.POST.get("addedby")

            if dept_id:
                patient_list = patient_list.filter(department=dept_id)
            if followup in ["true", "True", True, "1"]:
                patient_list = patient_list.filter(followup=True)
            if addedby:
                patient_list = patient_list.filter(added_by=addedby,role='spot')

            for p in patient_list:
                p.department_name = departments_map.get(str(p.department), p.department)

            table_html = render(
                request, "med_admin/report_spotregister_rows.html",
                {"patients": patient_list,'officialusers': officialusers,"departments": departments_all,}
            ).content.decode("utf-8")
            return JsonResponse({"table_html": table_html})

        for p in patient_list:
            p.department_name = departments_map.get(str(p.department), p.department)

        officialusers = officialuser.objects.all().values("id", "name")
        officialusers_json = list(officialusers)


        return render(
            request, 
            "med_admin/report_spotregister.html", 
            {
                "patients": patient_list, 
                "departments": departments_all,
                "officialusers_json": officialusers_json,
                'officialusers': officialusers
            }
        )
    else:
        return redirect('login')



def token_report(request):
    if 'type' in request.session:
        patient_list = patients.objects.filter(confirm_entry=1,isdeleted=0).order_by('-id')
        departments_all = department.objects.all()

        # Department map
        departments_map = {str(d.id): d.department for d in department.objects.all()}

        # ✅ Confirmed by map (from registration)
        confirmed_by_map = {str(r.id): r.name for r in registration.objects.all()}

        if request.method == "POST" and request.headers.get('x-requested-with') == 'XMLHttpRequest':
            dept_id = request.POST.get("department")
            followup = request.POST.get("followup")
            confirmby = request.POST.get("confirmby")
            rotorian_id = request.POST.get("rotorian")

            if dept_id:
                patient_list = patient_list.filter(department=dept_id)
            if followup in ["true", "True", True, "1"]:
                patient_list = patient_list.filter(followup=True)
            if confirmby:
                patient_list = patient_list.filter(confirmed_by=confirmby)
            if rotorian_id:
                patient_list = patient_list.filter(added_by=rotorian_id, role='official')

            # Map display names
            for p in patient_list:
                p.department_name = departments_map.get(str(p.department), p.department)

                # ✅ confirmed_by display (from registration)
                p.confirmed_by_name = confirmed_by_map.get(str(p.confirmed_by), p.confirmed_by or "-")

            table_html = render(
                request, "med_admin/report_token_rows.html",
                {"patients": patient_list,"departments": departments_all,}
            ).content.decode("utf-8")
            return JsonResponse({"table_html": table_html})

        # For initial page load
        for p in patient_list:
            p.department_name = departments_map.get(str(p.department), p.department)

            p.confirmed_by_name = confirmed_by_map.get(str(p.confirmed_by), p.confirmed_by or "-")

        registration_all = registration.objects.all().values("id", "name")
        registration_json = list(registration_all)
        rotarians_all = officialuser.objects.all().values("id", "name")
        rotarians_json = list(rotarians_all)

        return render(
            request,
            "med_admin/report_token.html",
            {
                "patients": patient_list,
                "departments": departments_all,
                "registration_json": registration_json,
                "rotarians_json": rotarians_json
            }
        )
    else:
        return redirect('login')
    

def consulted_report(request):
    if 'type' in request.session:
        patient_list = patients.objects.filter(consulted=1,isdeleted=0).order_by('-id')
        registration_list = registration.objects.all()
        departments_all = department.objects.all()

        # Department map
        departments_map = {str(d.id): d.department for d in department.objects.all()}

        if request.method == "POST" and request.headers.get('x-requested-with') == 'XMLHttpRequest':
            dept_id = request.POST.get("department")
            follow_up = request.POST.get("followup")
            confirmby = request.POST.get("confirmby")
            rotorian_id = request.POST.get("rotorian")

            if dept_id:
                patient_list = patient_list.filter(department=dept_id)
            if follow_up in ["true", "True", True, "1"]:
                patient_list = patient_list.filter(followup=True)
            if confirmby:
                patient_list = patient_list.filter(consulted_by=confirmby)

            for p in patient_list:
                p.department_name = departments_map.get(str(p.department), p.department)

            table_html = render(
                request, "med_admin/report_consulted_rows.html",
                {"patients": patient_list,"registration":registration_list,"departments": departments_all}
            ).content.decode("utf-8")
            return JsonResponse({"table_html": table_html})

        registration_all = registration.objects.all().values("id", "name")
        registration_json = list(registration_all)
        rotarians_all = officialuser.objects.all().values("id", "name")
        rotarians_json = list(rotarians_all)

        for p in patient_list:
            p.department_name = departments_map.get(str(p.department), p.department)

        return render(
            request,
            "med_admin/report_consulted.html",
            {
                "patients": patient_list,
                "departments": departments_all,
                "registration_json": registration_json,
                "rotarians_json": rotarians_json,
                "registration":registration_list
            }
        )
    else:
        return redirect('login')
    

def medicine_report(request):
    if 'type' in request.session:
        patient_list = patients.objects.filter(medicineissued=1,isdeleted=0).order_by('-id')
        registration_list = registration.objects.all()
        departments_all = department.objects.all()

        # Department map
        departments_map = {str(d.id): d.department for d in department.objects.all()}

        if request.method == "POST" and request.headers.get('x-requested-with') == 'XMLHttpRequest':
            dept_id = request.POST.get("department")
            follow_up = request.POST.get("followup")
            confirmby = request.POST.get("confirmby")
            rotorian_id = request.POST.get("rotorian")

            if dept_id:
                patient_list = patient_list.filter(department=dept_id)
            if follow_up in ["true", "True", True, "1"]:
                patient_list = patient_list.filter(followup=True)
            if confirmby:
                patient_list = patient_list.filter(medicineissued_by=confirmby)

            for p in patient_list:
                p.department_name = departments_map.get(str(p.department), p.department)

            table_html = render(
                request, "med_admin/report_medicine_rows.html",
                {"patients": patient_list,"registration":registration_list,"departments": departments_all}
            ).content.decode("utf-8")
            return JsonResponse({"table_html": table_html})

        registration_all = registration.objects.all().values("id", "name")
        registration_json = list(registration_all)
        rotarians_all = officialuser.objects.all().values("id", "name")
        rotarians_json = list(rotarians_all)

        for p in patient_list:
            p.department_name = departments_map.get(str(p.department), p.department)

        return render(
            request,
            "med_admin/report_medicine.html",
            {
                "patients": patient_list,
                "departments": departments_all,
                "registration_json": registration_json,
                "rotarians_json": rotarians_json,
                "registration":registration_list
            }
        )
    else:
        return redirect('login')



def login(request):
    if request.method == "POST":
        email = request.POST.get("admin_email")
        password = request.POST.get("password")

        try:
            user = users.objects.get(email=email)

            if user.password == password:
                request.session['name'] = user.name
                request.session['type'] = user.type
                return redirect('dashboard')
            else:
                return render(request, "med_admin/login.html", {
                    'error': 'Invalid password. Please try again.'
                })
        except users.DoesNotExist:
            return render(request, "med_admin/login.html", {
                'error': 'No account found with this email.'
            })

    return render(request, "med_admin/login.html")



def logout(request):
    request.session.flush()
    return redirect('login')



from django.core.paginator import Paginator

def departments(request):
    # Fetch all departments and apply pagination
    departments_list = department.objects.all()
    paginator = Paginator(departments_list, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    total_pages = paginator.num_pages
    current_page = page_obj.number

    # Create custom page range (3 pages max shown at a time)
    if total_pages <= 3:
        start_page = 1
        end_page = total_pages
    else:
        if current_page == 1:
            start_page = 1
            end_page = 3
        elif current_page == total_pages:
            start_page = total_pages - 2
            end_page = total_pages
        else:
            start_page = current_page - 1
            end_page = current_page + 1

    page_range_custom = range(start_page, end_page + 1)

    # Calculate totals for the current page
    total_setlimit = sum(int(d.setlimit) for d in page_obj)
    total_rotary = sum(int(d.rotary_limit) for d in page_obj)
    total_asha = sum(int(d.asha_limit) for d in page_obj)

    # Handle form submission
    if request.method == 'POST':
        department_new = request.POST.get('department')
        asha_limit = request.POST.get('asha_limit')
        setlimit = request.POST.get('limit')
        token = request.POST.get('token')

        try:
            asha_limit = int(float(asha_limit))
            setlimit = int(float(setlimit))
        except (ValueError, TypeError):
            messages.error(request, "Please enter whole numbers only.")
            return redirect('department')

        ashaworker_count = ashaworker.objects.count()
        asha_total_calc = ashaworker_count * asha_limit
        rotary_limit = setlimit - asha_total_calc

        rotary_limit = str(int(rotary_limit))

        if department.objects.filter(department__iexact=department_new).exists():
            messages.error(request, "Department already exists.")
        else:
            department.objects.create(
                department=department_new,
                asha_limit=str(asha_limit),
                setlimit=str(setlimit),
                token=token,
                added_by=request.session.get('name', 'Unknown'),
                rotary_limit=rotary_limit
            )
            messages.success(request, "Fixed Credit added successfully.")

        return redirect('department')

    return render(
        request,
        'med_admin/department.html',
        {
            'departments': page_obj,
            'page_range_custom': page_range_custom,
            'total_setlimit': total_setlimit,
            'total_rotary': total_rotary,
            'total_asha': total_asha,
        }
    )




def editdepartment(request):
    # Get department ID from GET or POST
    department_id = request.GET.get('department_id') or request.POST.get('department_id')
    if not department_id:
        messages.error(request, "No department selected.")
        return redirect('department')

    # Fetch the department object or return 404
    edit_department = get_object_or_404(department, id=department_id)

    # Handle form submission
    if request.method == 'POST':
        edit_department.department = request.POST.get('department')
        edit_department.token = request.POST.get('token')

        # Convert limits to integers only
        try:
            asha_limit = int(float(request.POST.get('asha_limit')))
            setlimit = int(float(request.POST.get('limit')))
        except (ValueError, TypeError):
            messages.error(request, "Please enter valid whole numbers for limits.")
            return redirect('editdepartment')  # redirect back to edit page

        # Calculate rotary limit
        ashaworker_count = ashaworker.objects.count()
        rotary_limit = setlimit - (ashaworker_count * asha_limit)

        # Save values as strings (since model uses CharField)
        edit_department.asha_limit = str(asha_limit)
        edit_department.setlimit = str(setlimit)
        edit_department.rotary_limit = str(rotary_limit)

        edit_department.save()
        messages.success(request, "Department updated successfully.")
        return redirect('department')

    # GET request: show table and edit form
    departments_list = department.objects.all().order_by('id')
    page_number = request.GET.get('page', 1)
    paginator = Paginator(departments_list, 10)
    page_obj = paginator.get_page(page_number)

    # Custom pagination range (max 3 pages)
    total_pages = paginator.num_pages
    current_page = page_obj.number
    if total_pages <= 3:
        start_page = 1
        end_page = total_pages
    else:
        if current_page == 1:
            start_page = 1
            end_page = 3
        elif current_page == total_pages:
            start_page = total_pages - 2
            end_page = total_pages
        else:
            start_page = current_page - 1
            end_page = current_page + 1
    page_range_custom = range(start_page, end_page + 1)

    return render(request, 'med_admin/department_edit.html', {
        'edit_department': edit_department,
        'departments': page_obj,
        'page_range_custom': page_range_custom
    })



def home(request):
    return render(request, 'med_admin/home.html')

def managepatient(request):
    departments_qs = department.objects.all()
    departments_list = list(departments_qs.values('id', 'department'))

    if request.method == 'POST':
        code = request.POST.get('code')
        pin = request.POST.get('pin')

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            try:
                patient = patients.objects.get(code=code, securitypin=pin)
                dept=department.objects.get(id=int(patient.department))
                return JsonResponse({
                    'status': 'success',
                    'patient': {
                        'id': patient.id,
                        'pin':patient.securitypin,
                        'name': patient.name,
                        'code': patient.code,
                        'contact': patient.contact,
                        'age': patient.age if patient.age else '-',
                        'gender': patient.gender if patient.gender else '-',
                        'department': patient.department,
                        'dept':dept.department,
                        'subdepartment': patient.subdepartment,
                        'followup': patient.followup,
                        'consulted': patient.consulted,
                    }
                })
            except patients.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'No patient found.'})

    return render(request, 'med_admin/managepatient.html', {'departments': departments_list})




def editpatient(request):
    if request.method == "POST":
        patient_id = request.POST.get('patientId')
        name = request.POST.get('name', '').strip()
        contact = request.POST.get('contact', '').strip()
        age = request.POST.get('age', '').strip()
        ageBelow1 = request.POST.get('ageBelow1')
        gender = request.POST.get('gender', '').strip()
        dept_id = request.POST.get('department', '').strip()

        if ageBelow1 in ['1', 'on']:
            age = '0'

        # Basic validation
        errors = []
        if not name:
            errors.append("Name is required.")
        if not contact or len(contact) != 10 or not contact.isdigit():
            errors.append("Enter a valid 10-digit contact number.")
        if not gender:
            errors.append("Select gender.")
        if not dept_id:
            errors.append("Select department.")
        if not age:
            errors.append("Enter age.")

        if errors:
            for err in errors:
                messages.error(request, err)
            return redirect('managepatient')

        # Check for other patients with same name, contact, department, but exclude current patient
        existing_patient = patients.objects.filter(
            name__iexact=name,
            contact=contact,
            department=str(dept_id),
            isdeleted=0
        ).exclude(id=patient_id).first()

        if existing_patient:
            messages.error(request, "Patient already exists in this department.")
            return redirect('managepatient')

        try:
            patient = patients.objects.get(id=patient_id, isdeleted=0)
            patient.name = name
            patient.contact = contact
            patient.age = age
            patient.gender = gender
            patient.department = dept_id
            patient.save()
            messages.success(request, "Patient updated successfully")
        except patients.DoesNotExist:
            messages.error(request, "Patient not found")

        return redirect('managepatient')

    return redirect('managepatient')


def deletepatient(request):
    if request.method == "POST" and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        patient_id = request.POST.get('patientId')

        try:
            patient = patients.objects.get(id=patient_id)
            patient.isdeleted = 1  # assuming 1 means deleted
            patient.save()

            messages.error(request, "Patient deleted successfully")
            return JsonResponse({'status': 'success'})
        except patients.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Patient not found'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

def all_volunteers(request):
    volunteer_list = registration.objects.all().order_by('name')

    for i in volunteer_list:
        d = department.objects.filter(id=i.dept).first()
        i.department = d.department
    
    # Pagination
    paginator = Paginator(volunteer_list, 8)  # 8 volunteers per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Calculate starting SL No for the current page
    start_sl = (page_obj.number - 1) * paginator.per_page

    return render(request, 'med_admin/all_volunteers.html', {
        'page_obj': page_obj,
        'start_sl': start_sl
    })


import re


def consolidated_report(request):
    import re
    departments_all = department.objects.all()
    
    # Extract only English names from department names
    departments = []
    for dept in departments_all:
        match = re.search(r'\((.*?)\)', dept.department)
        if match:
            departments.append(match.group(1))  # English name
        else:
            departments.append(dept.department)  # fallback

    asha_report = []
    rotarian_report = []

    # ASHA workers
    asha_workers = ashaworker.objects.all()
    total_per_dept = [0] * len(departments)  # Initialize column totals
    grand_total = 0

    for asha in asha_workers:
        counts = []
        total = 0
        for i, dept_name in enumerate(departments_all):
            count = patients.objects.filter(
                added_by=str(asha.id),
                role="asha",
                department=dept_name.id
            ).count()
            counts.append(count)
            total += count
            total_per_dept[i] += count  # add to column total
        grand_total += total
        asha_report.append({
            "name": asha.name,
            "ward": getattr(asha, "ward", ""),
            "counts": counts,
            "total": total
        })

    # Rotarians
    rotarians = officialuser.objects.all()
    total_per_dept_rotarian = [0] * len(departments)
    grand_total_rotarian = 0

    for user in rotarians:
        counts = []
        total = 0
        for i, dept_name in enumerate(departments_all):
            count = patients.objects.filter(
                added_by=str(user.id),
                role="official",
                department=dept_name.id
            ).count()
            counts.append(count)
            total += count
            total_per_dept_rotarian[i] += count
        grand_total_rotarian += total
        rotarian_report.append({
            "name": user.name,
            "counts": counts,
            "total": total
        })

    # Sort reports by total descending
    asha_report = sorted(asha_report, key=lambda x: x["total"], reverse=True)
    rotarian_report = sorted(rotarian_report, key=lambda x: x["total"], reverse=True)

    # Pass totals to template
    return render(request, "med_admin/consolidated_report.html", {
        "departments": departments,  # English names only
        "asha_data": asha_report,
        "rotarian_data": rotarian_report,
        "total_per_dept": total_per_dept,
        "grand_total": grand_total,
        "total_per_dept_rotarian": total_per_dept_rotarian,
        "grand_total_rotarian": grand_total_rotarian,
    })


# def consolidated_report(request):
#     # Get all departments
#     departments_all = department.objects.all()
    
#     # Extract English names
#     departments = []
#     for dept in departments_all:
#         match = re.search(r'\((.*?)\)', dept.department)
#         if match:
#             departments.append(match.group(1))
#         else:
#             departments.append(dept.department)

#     asha_report = []
#     rotarian_report = []

#     # ASHA workers
#     asha_workers = ashaworker.objects.all()
#     for asha in asha_workers:
#         counts = []
#         total = 0
#         for dept_obj in departments_all:
#             count = patients.objects.filter(
#                 added_by=str(asha.id),
#                 role="asha",
#                 department=dept_obj.id
#             ).count()
#             counts.append(count)
#             total += count
#         asha_report.append({
#             "name": asha.name,
#             "ward": getattr(asha, "ward", ""),
#             "counts": counts,
#             "total": total
#         })

#     # Rotarians
#     rotarians = officialuser.objects.all()
#     for user in rotarians:
#         counts = []
#         total = 0
#         for dept_obj in departments_all:
#             count = patients.objects.filter(
#                 added_by=str(user.id),
#                 role="official",
#                 department=dept_obj.id
#             ).count()
#             counts.append(count)
#             total += count
#         rotarian_report.append({
#             "name": user.name,
#             "counts": counts,
#             "total": total
#         })

#     # Sort reports by total descending
#     asha_report = sorted(asha_report, key=lambda x: x["total"], reverse=True)
#     rotarian_report = sorted(rotarian_report, key=lambda x: x["total"], reverse=True)

#     # Totals per department (ASHAs)
#     total_per_dept = []
#     for i in range(len(departments)):
#         dept_total = sum(a["counts"][i] for a in asha_report)
#         total_per_dept.append(dept_total)

#     grand_total = sum(total_per_dept)

#     return render(request, "med_admin/consolidated_report.html", {
#         "departments": departments,
#         "asha_data": asha_report,
#         "rotarian_data": rotarian_report,
#         "total_per_dept": total_per_dept,
#         "grand_total": grand_total
#     })

