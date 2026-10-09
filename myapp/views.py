from django.shortcuts import render,redirect
from django.contrib import messages
from django.contrib.auth import authenticate,login as auth_login,logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import Group,User
from datetime import date
import math
import re
import json
from django.db.models import Q
from django.http import JsonResponse
from myapp.models import *
from . import new_code_detect_new as oral_cancer_predictor




def home(request):
    return render(request,'home.html')



def adminhome(request):
    return render(request,'adminhome.html')

def user_home(request):
    return render(request,'user_home.html')


def hospital_home(request):
    return render(request,'hospital_home.html')


@login_required(login_url='login')
@never_cache
def logout_user(request):
    logout(request)
    request.session.flush()
    messages.success(request, "Logged out successfully.")
    return redirect('login')


@csrf_exempt
@never_cache
def login(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        print("USER : ", user)

        if user is not None:
            auth_login(request, user)
            request.session['user_id'] = user.id

            if user.groups.filter(name='admin').exists():
                return redirect('adminhome')


            elif user.groups.filter(name='user').exists():
                user = UserProfile.objects.get(USER=user)
                request.session['user'] = user.id
                return redirect('user_home')


            elif user.groups.filter(name='hospital').exists():
                hospital = Hospital.objects.get(USER=user)
                request.session['hospital'] = hospital.id
                return redirect('hospital_home')

            else:
                messages.error(request, 'Invalid username or password')
                return redirect('login')

        else:
            messages.error(request, 'Username or password incorrect')
    return render(request, 'login.html')



@never_cache
@csrf_exempt
def user_register(request):
    if request.method == "POST":
        fname = request.POST['fname']
        lname = request.POST['lname']
        email = request.POST['email']
        phone = request.POST['phone']
        address = request.POST['address']
        gender = request.POST['gender']
        place = request.POST['place']
        latitude = request.POST['latitude']
        longitude = request.POST['longitude']
        username = request.POST['username']
        password = request.POST['password']

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
            return redirect('user_register')


        user = User.objects.create_user(
            username=username,
            password=password,
            email=email
        )
        user.save()


        try:
            group = Group.objects.get(name='user')
        except Group.DoesNotExist:
            group = Group.objects.create(name='user')
        user.groups.add(group)


        UserProfile.objects.create(
            USER=user,
            first_name=fname,
            last_name=lname,
            email=email,
            phone=phone,
            address=address,
            gender=gender,
            place=place,
            latitude=latitude,
            longitude=longitude
        )

        messages.success(request, 'Registration completed successfully')
        return redirect('login')

    return render(request, 'user_register.html')


@login_required(login_url='login')
@never_cache
@csrf_exempt
def admin_manage_hospital(request):
    if request.method == "POST":
        name = request.POST['name']
        email = request.POST['email']
        phone = request.POST['phone']
        place = request.POST['place']
        post = request.POST['post']
        pin = request.POST['pin']
        district = request.POST['district']
        state = request.POST['state']
        latitude = request.POST['latitude']
        longitude = request.POST['longitude']
        username = request.POST['username']
        password = request.POST['password']

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
            return redirect('admin_manage_hospital')


        user = User.objects.create_user(
            username=username,
            password=password,
            email=email
        )
        user.save()


        try:
            group = Group.objects.get(name='hospital')
        except Group.DoesNotExist:
            group = Group.objects.create(name='hospital')
        user.groups.add(group)


        Hospital.objects.create(
            USER=user,
            name=name,
            email=email,
            phone=phone,
            place=place,
            post=post,
            pin=pin,
            district=district,
            state=state,
            latitude=latitude,
            longitude=longitude
        )

        messages.success(request, 'Hospital registration completed.')
        return redirect('adminhome')

    hospitals = Hospital.objects.all().order_by('-id')
    return render(request, 'admin_manage_hospital.html', {'hospitals': hospitals})

@login_required(login_url='login')
def admin_delete_hospital(request, id):
    hospital = Hospital.objects.get(id=id)
    hospital.USER.delete()
    hospital.delete()
    messages.success(request, 'Hospital deleted successfully')
    return redirect('admin_manage_hospital')


@login_required(login_url='login')
def admin_edit_hospital(request, id):
    hospital = Hospital.objects.get(id=id)

    if request.method == "POST":
        hospital.name = request.POST['name']
        hospital.email = request.POST['email']
        hospital.phone = request.POST['phone']
        hospital.place = request.POST['place']
        hospital.post = request.POST['post']
        hospital.pin = request.POST['pin']
        hospital.district = request.POST['district']
        hospital.state = request.POST['state']
        hospital.latitude = request.POST['latitude']
        hospital.longitude = request.POST['longitude']
        hospital.save()

        messages.success(request, 'Hospital updated successfully')
        return redirect('admin_manage_hospital')

    return render(request, 'admin_edit_hospital.html', {'hospital': hospital})


@login_required(login_url='login')
@never_cache
def admin_view_users(request):
    a = UserProfile.objects.all()
    return render(request, 'admin_view_users.html', {'a': a})



@login_required(login_url='login')
@never_cache
def user_view_profile(request):
    a = UserProfile.objects.get(USER=request.user)
    return render(request, 'user_view_profile.html', {'a': a})



@login_required(login_url='login')
@never_cache
@csrf_exempt
def user_update_profile(request, id):
    a = UserProfile.objects.get(id=id)

    if request.method == "POST":
        fname = request.POST['fname']
        lname = request.POST['lname']
        email = request.POST['email']
        phone = request.POST['phone']
        address = request.POST['address']
        gender = request.POST['gender']
        place = request.POST['place']

        a.first_name = fname
        a.last_name = lname
        a.email = email
        a.phone = phone
        a.address = address
        a.gender = gender
        a.place = place

        a.save()

        messages.success(request, 'Profile updated successfully')
        return redirect('user_view_profile')

    return render(request, 'user_update_profile.html', {'a': a})





@login_required(login_url='login')
@never_cache
@csrf_exempt
def user_send_complaint(request):
    if request.method == "POST":
        complaint = request.POST['complaint']

        Complaint.objects.create(
            USER=request.user,
            complaint=complaint,
            reply='pending',
            date=date.today()
        )

        messages.success(request, 'Complaint sent successfully')

    a = Complaint.objects.filter(USER=request.user).order_by('-id')

    return render(request, 'user_send_complaint.html', {'a': a})




@login_required(login_url='login')
@never_cache
@csrf_exempt
def admin_view_complaints(request):
    a = Complaint.objects.all()

    if request.method == "POST":
        id = request.POST['id']
        reply = request.POST['reply']

        b = Complaint.objects.get(id=id)
        b.reply = reply
        b.save()

        messages.success(request, 'Reply sent successfully')

    return render(request, 'admin_view_complaints.html', {'a': a})



@login_required(login_url='login')
@never_cache
def hospital_view_profile(request):
    a = Hospital.objects.get(id=request.session['hospital'])
    return render(request, 'hospital_view_profile.html', {'a': a})



@login_required(login_url='login')
@never_cache
@csrf_exempt
def hospital_update_profile(request, id):
    a = Hospital.objects.get(id=id)

    if request.method == "POST":
        a.name = request.POST['name']
        a.email = request.POST['email']
        a.phone = request.POST['phone']
        a.place = request.POST['place']
        a.post = request.POST['post']
        a.pin = request.POST['pin']
        a.district = request.POST['district']
        a.state = request.POST['state']
        a.latitude = request.POST['latitude']
        a.longitude = request.POST['longitude']

        a.save()
        messages.success(request, 'Profile updated successfully')
        return redirect('hospital_view_profile')

    return render(request, 'hospital_update_profile.html', {'a': a})




@login_required(login_url='login')
@never_cache
@csrf_exempt
def hospital_manage_appointment(request):

    hospital = Hospital.objects.get(USER=request.user)

    if request.method == "POST":
        start_time = request.POST['start_time']
        end_time = request.POST['end_time']
        app_date = request.POST['date']


        Appointment.objects.create(
            HOSPITAL=hospital,
            start_time=start_time,
            end_time=end_time,
            date=app_date,
        )

        messages.success(request, 'Appointment slot added successfully')

    a = Appointment.objects.filter(HOSPITAL=hospital)

    return render(request, 'hospital_manage_appointment.html', {'a': a})


@login_required(login_url='login')
@never_cache
@csrf_exempt
def hospital_update_appointment(request, id):

    a = Appointment.objects.get(id=id)

    if request.method == "POST":
        a.start_time = request.POST['start_time']
        a.end_time = request.POST['end_time']
        a.date = request.POST['date']

        a.save()
        messages.success(request, 'Appointment updated successfully')
        return redirect('hospital_manage_appointment')

    return render(request, 'hospital_update_appointment.html', {'a': a})


@login_required(login_url='login')
@never_cache
def hospital_delete_appointment(request, id):

    a = Appointment.objects.get(id=id)
    a.delete()

    messages.success(request, 'Appointment deleted successfully')
    return redirect('hospital_manage_appointment')



@login_required(login_url='login')
@never_cache
@csrf_exempt
def admin_manage_educational_material(request):

    if request.method == "POST":
        title = request.POST['title']
        content = request.POST['content']
        type = request.POST['type']

        EducationalMaterial.objects.create(
            title=title,
            content=content,
            type=type
        )

        messages.success(request, 'Educational material added successfully')

    a = EducationalMaterial.objects.all().order_by('-id')

    return render(request, 'admin_manage_educational_material.html', {'a': a})



@login_required(login_url='login')
@never_cache
@csrf_exempt
def admin_edit_educational_material(request, id):
    a = EducationalMaterial.objects.get(id=id)

    if request.method == "POST":
        title = request.POST['title']
        content = request.POST['content']
        type = request.POST['type']

        a.title = title
        a.content = content
        a.type = type
        a.save()

        messages.success(request, 'Educational material updated successfully')
        return redirect('admin_manage_educational_material')

    return render(request, 'admin_edit_educational_material.html', {'a': a})



@login_required(login_url='login')
@never_cache
def admin_delete_educational_material(request, id):
    a = EducationalMaterial.objects.get(id=id)
    a.delete()
    messages.success(request, 'Educational material deleted')
    return redirect('admin_manage_educational_material')



def public_home(request):
    materials = EducationalMaterial.objects.all()
    return render(request, 'public_home.html', {'materials': materials})





@login_required(login_url='login')
@never_cache
@csrf_exempt
def hospital_manage_camps(request):

    hospital_id = request.session.get('hospital')

    if request.method == "POST":
        ScreeningCamp.objects.create(
            HOSPITAL_id=hospital_id,
            camp_name=request.POST['camp_name'],
            place=request.POST['place'],
            latitude=request.POST['latitude'],
            longitude=request.POST['longitude'],
            start_date=request.POST['start_date'],
            end_date=request.POST['end_date'],
            start_time=request.POST['start_time'],
            end_time=request.POST['end_time'],
            description=request.POST['description']
        )
        messages.success(request, 'Screening camp added successfully.')

    a = ScreeningCamp.objects.filter(HOSPITAL_id=hospital_id).order_by('-id')

    return render(request, 'hospital_manage_camps.html', {'a': a})


@login_required(login_url='login')
@never_cache
@csrf_exempt
def hospital_update_camp(request, id):
    a = ScreeningCamp.objects.get(id=id)

    if request.method == "POST":
        a.camp_name = request.POST['camp_name']
        a.place = request.POST['place']
        a.latitude = request.POST['latitude']
        a.longitude = request.POST['longitude']
        a.start_date = request.POST['start_date']
        a.end_date = request.POST['end_date']
        a.start_time = request.POST['start_time']
        a.end_time = request.POST['end_time']
        a.description = request.POST['description']

        a.save()
        messages.success(request, 'Screening camp updated successfully')
        return redirect('hospital_manage_camps')

    return render(request, 'hospital_update_camp.html', {'a': a})


@login_required(login_url='login')
@never_cache
def hospital_delete_camp(request, id):
    a = ScreeningCamp.objects.get(id=id)
    a.delete()
    messages.success(request, 'Screening camp deleted successfully')
    return redirect('hospital_manage_camps')



@login_required(login_url='login')
@never_cache
def admin_view_camps(request):
    a = ScreeningCamp.objects.all()
    return render(request, 'admin_view_camps.html', {'a': a})


def public_view_screening_camps(request):

    camps = ScreeningCamp.objects.all().order_by('-id')

    return render(request, 'public_view_screening_camps.html', {'camps': camps})



def clean_float(value):
    if not value:
        return None
    match = re.search(r'[-+]?\d*\.\d+|\d+', str(value))
    return float(match.group()) if match else None


def calculate_distance(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(clean_float, [lat1, lon1, lat2, lon2])

    if None in [lat1, lon1, lat2, lon2]:
        return None

    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat / 2) ** 2 + \
        math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2

    c = 2 * math.asin(math.sqrt(a))
    return 6371 * c


@login_required(login_url='login')
@never_cache
def user_view_nearby_hospitals(request):

    hospitals = Hospital.objects.all()

    return render(request, 'user_view_nearby_hospitals.html', {
        'data': hospitals
    })





# @login_required(login_url='login')
# @never_cache
# def user_view_nearby_hospitals(request):
#
#
#     profile = UserProfile.objects.get(USER=request.user)
#
#     user_lat = profile.latitude
#     user_lon = profile.longitude
#
#     print("USER LOCATION:", user_lat, user_lon)
#
#     hospitals = Hospital.objects.all()
#
#     hospital_list = []
#
#     for hospital in hospitals:
#         distance = calculate_distance(
#             user_lat,
#             user_lon,
#             hospital.latitude,
#             hospital.longitude
#         )
#
#         print(
#             hospital.name,
#             "=>",
#             hospital.latitude,
#             hospital.longitude
#         )
#
#         if distance is not None and distance <= 10:
#             hospital_list.append({
#                 'hospital': hospital,
#                 'distance': round(distance, 2)
#             })
#
#     hospital_list.sort(key=lambda x: x['distance'])
#
#     return render(request, 'user_view_nearby_hospitals.html', {
#         'data': hospital_list
#     })



@login_required(login_url='login')
@never_cache
def user_view_hospital_appointments(request, id):
    hospital = Hospital.objects.get(id=id)


    appointments = Appointment.objects.filter(HOSPITAL=hospital)

    return render(request, 'user_view_hospital_appointments.html', {'appointments': appointments,'hospital': hospital})


@login_required(login_url='login')
@never_cache
def user_book_appointment(request, appointment_id):
    appointment = Appointment.objects.get(id=appointment_id)
    user_profile = UserProfile.objects.get(USER=request.user)

    if request.method == 'POST':
        time = request.POST['time']

        SendRequest.objects.create(
            USER_PROFILE=user_profile,
            APPOINTMENT=appointment,
            date=date.today(),
            time=time,
            status='pending'
        )

        return redirect('user_view_hospital_appointments', appointment.HOSPITAL.id)

    return render(
        request,
        'user_book_appointment.html',
        {'appointment': appointment}
    )



@login_required(login_url='login')
@never_cache
def user_view_appointment_status(request):

    profile = UserProfile.objects.get(USER=request.user)

    requests = SendRequest.objects.filter(USER_PROFILE=profile).select_related('APPOINTMENT', 'APPOINTMENT__HOSPITAL').order_by('-id')

    return render(request,'user_view_appointment_status.html',{'requests': requests})




@login_required(login_url='login')
@never_cache
def hospital_view_appointment_requests(request):

    hospital = Hospital.objects.get(USER=request.user)

    a = SendRequest.objects.filter(APPOINTMENT__HOSPITAL=hospital).select_related('USER_PROFILE','APPOINTMENT')

    return render(request,'hospital_view_appointment_requests.html',{'a': a})


@login_required(login_url='login')
@never_cache
def hospital_accept_appointment(request, id):

    a = SendRequest.objects.get(id=id)
    a.status = 'accepted'
    a.save()

    messages.success(request, 'Appointment request accepted.')

    return redirect('hospital_view_appointment_requests')


@login_required(login_url='login')
@never_cache
def hospital_reject_appointment(request, id):

    a = SendRequest.objects.get(id=id)
    a.status = 'rejected'
    a.save()

    messages.success(request, 'Appointment request rejected.')

    return redirect('hospital_view_appointment_requests')




def clean_float(value):
    if not value:
        return None
    match = re.search(r'[-+]?\d*\.\d+|\d+', str(value))
    return float(match.group()) if match else None


def calculate_distance(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(clean_float, [lat1, lon1, lat2, lon2])

    if None in [lat1, lon1, lat2, lon2]:
        return None

    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat / 2) ** 2 + \
        math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2

    c = 2 * math.asin(math.sqrt(a))
    return 6371 * c   # KM


@login_required(login_url='login')
@never_cache
def user_view_nearby_screening_camps(request):

    profile = UserProfile.objects.get(USER=request.user)

    user_lat = profile.latitude
    user_lon = profile.longitude

    print("USER LOCATION:", user_lat, user_lon)

    # only camps from APPROVED hospitals
    camps = ScreeningCamp.objects.all()

    camp_list = []

    for camp in camps:
        distance = calculate_distance(
            user_lat,
            user_lon,
            camp.latitude,
            camp.longitude
        )

        print(
            camp.camp_name,
            "=>",
            camp.latitude,
            camp.longitude,
            "DIST:",
            distance
        )

        if distance is not None and distance <= 10:
            camp_list.append({
                'camp': camp,
                'distance': round(distance, 2)
            })

    camp_list.sort(key=lambda x: x['distance'])

    return render(request, 'user_view_nearby_screening_camps.html', {
        'data': camp_list
    })




@login_required(login_url='login')
@never_cache
def user_chat_with_hospital(request, id):
    hospital_user = User.objects.get(id=id)
    logged_user = request.user

    return render(request, 'user_chat.html', {
        'hospital_user': hospital_user,
        'user_obj': logged_user
    })



@csrf_exempt
@login_required(login_url='login')
def user_view_chat(request):
    if request.method == 'POST':
        data = json.loads(request.body)

        user_id = int(data.get('user_id'))
        hospital_user_id = int(data.get('hospital_user_id'))

        chats = Chat.objects.filter(
            Q(FROM_USER_id=user_id, TO_USER_id=hospital_user_id) |
            Q(FROM_USER_id=hospital_user_id, TO_USER_id=user_id)
        ).order_by('id')

        messages = [{
            'from': c.FROM_USER_id,
            'to': c.TO_USER_id,
            'message': c.message,
            'timestamp': f"{c.date} {c.time}"
        } for c in chats]

        return JsonResponse({'status': 'ok', 'messages': messages})

    return JsonResponse({'status': 'error'})





@csrf_exempt
@login_required(login_url='login')
def user_send_chat(request):
    data = json.loads(request.body)

    user_id = int(data.get('user_id'))
    hospital_user_id = int(data.get('hospital_user_id'))
    message = data.get('message')

    chat = Chat.objects.create(
        FROM_USER_id=user_id,
        TO_USER_id=hospital_user_id,
        message=message
    )

    return JsonResponse({'status': 'ok'})


@login_required(login_url='login')
@never_cache
def hospital_chat_with_user(request, id):
    user_obj = User.objects.get(id=id)
    hospital_user = request.user

    return render(request, 'hospital_chat.html', {
        'user_obj': user_obj,
        'hospital_user': hospital_user
    })



@csrf_exempt
@login_required(login_url='login')
def hospital_view_chat(request):
    if request.method == 'POST':
        data = json.loads(request.body)

        hospital_user_id = int(data.get('hospital_user_id'))
        user_id = int(data.get('user_id'))

        chats = Chat.objects.filter(
            Q(FROM_USER_id=hospital_user_id, TO_USER_id=user_id) |
            Q(FROM_USER_id=user_id, TO_USER_id=hospital_user_id)
        ).order_by('id')

        messages = [{
            'from': c.FROM_USER_id,
            'to': c.TO_USER_id,
            'message': c.message,
            'timestamp': f"{c.date} {c.time}"
        } for c in chats]

        return JsonResponse({'status': 'ok', 'messages': messages})

    return JsonResponse({'status': 'error'})



@csrf_exempt
@login_required(login_url='login')
def hospital_send_chat(request):
    data = json.loads(request.body)

    hospital_user_id = int(data.get('hospital_user_id'))
    user_id = int(data.get('user_id'))
    message = data.get('message')

    Chat.objects.create(
        FROM_USER_id=hospital_user_id,
        TO_USER_id=user_id,
        message=message
    )

    return JsonResponse({'status': 'ok'})






# views.py
import os
from datetime import datetime

from django.shortcuts import render
from django.conf import settings

import torch
from myapp import new_code_detect_new as oral_cancer_predictor

# ===============================
# PATH CONFIGURATION
# ===============================

# MEDIA (uploaded input image)
UPLOAD_DIR = settings.MEDIA_ROOT
os.makedirs(UPLOAD_DIR, exist_ok=True)

# DETECTION RESULT DIRECTORY
OUTPUT_DIR = settings.DETECTION_RESULTS_DIR
os.makedirs(OUTPUT_DIR, exist_ok=True)




def detect_oral_cancer(request):
    result = None
    image_url = None
    result_image_url = None

    if request.method == "POST":
        option = request.POST.get("option")
        uploaded_file = request.FILES.get("image")

        if option and uploaded_file:
            # ===============================
            # SAVE UPLOADED IMAGE
            # ===============================
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = f"{timestamp}_{os.path.splitext(uploaded_file.name)[0]}"
            input_filename = base_name + ".jpg"

            img_path = os.path.join(UPLOAD_DIR, input_filename)

            with open(img_path, "wb") as f:
                for chunk in uploaded_file.chunks():
                    f.write(chunk)

            # ===============================
            # DEVICE
            # ===============================
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            option = int(option)

            # ===============================
            # ENSEMBLE OPTIONS (10, 11, 12)
            # ===============================
            if option in [10, 11, 12]:

                output_dir = OUTPUT_DIR
                base_path = oral_cancer_predictor.CONFIG["models_base_dir"]

                if option == 10:
                    model_configs = [
                        ("InceptionResNetV2", os.path.join(base_path, oral_cancer_predictor.MODEL_PATHS["InceptionResNetV2"]), None),
                        ("XceptionNet", os.path.join(base_path, oral_cancer_predictor.MODEL_PATHS["XceptionNet"]), None),
                        ("EfficientNetB3", os.path.join(base_path, oral_cancer_predictor.MODEL_PATHS["EfficientNetB3"]), None)
                    ]

                elif option == 11:
                    model_configs = [
                        ("InceptionResNetV2", os.path.join(base_path, oral_cancer_predictor.MODEL_PATHS["InceptionResNetV2"]), "gradcam"),
                        ("XceptionNet", os.path.join(base_path, oral_cancer_predictor.MODEL_PATHS["XceptionNet"]), "gradcam"),
                        ("EfficientNetB3", os.path.join(base_path, oral_cancer_predictor.MODEL_PATHS["EfficientNetB3"]), "gradcam")
                    ]

                else:  # option == 12
                    model_configs = [
                        ("InceptionResNetV2", os.path.join(base_path, oral_cancer_predictor.MODEL_PATHS["InceptionResNetV2"]), "occlusion"),
                        ("XceptionNet", os.path.join(base_path, oral_cancer_predictor.MODEL_PATHS["XceptionNet"]), "occlusion"),
                        ("EfficientNetB3", os.path.join(base_path, oral_cancer_predictor.MODEL_PATHS["EfficientNetB3"]), "occlusion")
                    ]

                ensemble_pred, ensemble_conf = oral_cancer_predictor.detect_ensemble(
                    img_path,
                    model_configs,
                    device,
                    output_dir,
                    "Web Ensemble"
                )

                result = {
                    "prediction": oral_cancer_predictor.CONFIG["class_names"][ensemble_pred],
                    "confidence": f"{ensemble_conf:.2%}"
                }

                image_url = settings.MEDIA_URL + input_filename
                result_filename = f"{base_name}_ensemble_result.png"
                result_image_url = settings.DETECTION_RESULTS_URL + result_filename

            # ===============================
            # SINGLE MODEL OPTIONS (1–9)
            # ===============================
            else:

                # MODEL SELECTION
                if option in [1, 4, 5]:
                    model_name = "InceptionResNetV2"
                elif option in [2, 6, 7]:
                    model_name = "XceptionNet"
                else:
                    model_name = "EfficientNetB3"

                # VISUALIZATION MODE
                vis_mode = None
                suffix = "prediction"

                if option in [4, 6, 8]:
                    vis_mode = "gradcam"
                    suffix = "gradcam"
                elif option in [5, 7, 9]:
                    vis_mode = "occlusion"
                    suffix = "occlusion"

                # MODEL PATH
                model_path = os.path.join(
                    oral_cancer_predictor.CONFIG["models_base_dir"],
                    oral_cancer_predictor.MODEL_PATHS[model_name]
                )

                # RUN PREDICTION
                pred_class, confidence, _ = oral_cancer_predictor.detect_single_model(
                    img_path,
                    model_path,
                    model_name,
                    device,
                    OUTPUT_DIR,
                    visualization_mode=vis_mode
                )

                result = {
                    "prediction": oral_cancer_predictor.CONFIG["class_names"][pred_class],
                    "confidence": f"{confidence:.2%}"
                }

                image_url = settings.MEDIA_URL + input_filename
                result_filename = f"{base_name}_{suffix}.png"
                result_image_url = settings.DETECTION_RESULTS_URL + result_filename

    return render(request, "detect.html", {
        "result": result,
        "image_url": image_url,
        "result_image_url": result_image_url
    })








def forgot_password(request):
    message = None
    error = None
    step = 1

    if request.method == "POST":

        # ================= VERIFY USER =================
        if "verify" in request.POST:
            username = request.POST.get("username")
            email = request.POST.get("email")

            if User.objects.filter(username=username, email=email).exists():
                message = "User verified. You can now reset your password."
                step = 2
                return render(request, "forgot_password.html", {
                    "message": message,
                    "step": step,
                    "username": username
                })
            else:
                error = "Invalid username or email"

        # ================= RESET PASSWORD =================
        elif "reset" in request.POST:
            username = request.POST.get("username")
            new_password = request.POST.get("new_password")
            confirm_password = request.POST.get("confirm_password")

            if new_password != confirm_password:
                error = "Passwords do not match"
                step = 2
            else:
                try:
                    user = User.objects.get(username=username)
                    user.set_password(new_password)
                    user.save()

                    message = "Password changed successfully. Please login."
                    step = 1

                except User.DoesNotExist:
                    error = "User not found"

    return render(request, "forgot_password.html", {
        "message": message,
        "error": error,
        "step": step
    })