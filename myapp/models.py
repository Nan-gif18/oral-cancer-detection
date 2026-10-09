from django.db import models
from django.contrib.auth.models import User



class UserProfile(models.Model):
    USER = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    address = models.CharField(max_length=255)
    gender = models.CharField(max_length=20)
    place = models.CharField(max_length=255)
    latitude = models.CharField(max_length=100,default="pending")
    longitude = models.CharField(max_length=100,default="pending")


class Hospital(models.Model):
    USER = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    email = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    place = models.CharField(max_length=255)
    post = models.CharField(max_length=255)
    pin = models.CharField(max_length=10)
    district = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    latitude = models.CharField(max_length=100)
    longitude = models.CharField(max_length=100)



class Complaint(models.Model):
    USER = models.ForeignKey(User, on_delete=models.CASCADE)
    complaint = models.CharField(max_length=255)
    reply = models.CharField(max_length=255, null=True, blank=True)
    date = models.CharField(max_length=255)


class EducationalMaterial(models.Model):
    title = models.CharField(max_length=255)
    content = models.CharField(max_length=255)
    type = models.CharField(max_length=100)


class ScreeningCamp(models.Model):
    HOSPITAL = models.ForeignKey(Hospital, on_delete=models.CASCADE)
    camp_name = models.CharField(max_length=255)
    place = models.CharField(max_length=255)
    latitude = models.CharField(max_length=100)
    longitude = models.CharField(max_length=100)
    start_date = models.CharField(max_length=100)
    end_date = models.CharField(max_length=100)
    start_time = models.CharField(max_length=100)
    end_time = models.CharField(max_length=100)
    description = models.CharField(max_length=255)



class Appointment(models.Model):
    HOSPITAL = models.ForeignKey(Hospital, on_delete=models.CASCADE)
    start_time = models.CharField(max_length=100)
    end_time = models.CharField(max_length=100)
    date = models.CharField(max_length=100)



class SendRequest(models.Model):
    USER_PROFILE = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    APPOINTMENT = models.ForeignKey(Appointment, on_delete=models.CASCADE)
    date = models.CharField(max_length=100)
    time = models.CharField(max_length=100)
    status = models.CharField(
        max_length=20,
        default='pending'
    )



class Chat(models.Model):
    FROM_USER = models.ForeignKey(User,on_delete=models.CASCADE,related_name='sent_messages')
    TO_USER = models.ForeignKey(User,on_delete=models.CASCADE,related_name='received_messages')
    message = models.TextField()
    date = models.DateField(auto_now_add=True)
    time = models.TimeField(auto_now_add=True)