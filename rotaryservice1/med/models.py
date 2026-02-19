from django.db import models

# Create your models here.


class users(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100, unique=True)
    added_on = models.DateTimeField(auto_now_add=True)
    password = models.CharField(max_length=100)
    type = models.CharField(max_length=100)


class ashaworker(models.Model):
    code=models.CharField(max_length=100)
    name=models.CharField(max_length=100)
    contact=models.CharField(max_length=100)
    ward=models.CharField(max_length=100)
    added_by=models.CharField(max_length=100)
    added_on = models.DateTimeField(auto_now_add=True)


class officialuser(models.Model):
    code=models.CharField(max_length=100,unique=True)
    name=models.CharField(max_length=100)
    contact=models.CharField(max_length=100)
    added_by=models.CharField(max_length=100)
    added_on = models.DateTimeField(auto_now_add=True)


class registration(models.Model):
    code=models.CharField(max_length=100,unique=True)
    name=models.CharField(max_length=100)
    contact=models.CharField(max_length=100)
    dept=models.CharField(max_length=100)
    desk=models.CharField(max_length=100)
    added_by=models.CharField(max_length=100)
    added_on = models.DateTimeField(auto_now_add=True)


class followup(models.Model):
    code=models.CharField(max_length=100,unique=True)
    name=models.CharField(max_length=100)
    contact=models.CharField(max_length=100)
    added_by=models.CharField(max_length=100)
    added_on = models.DateTimeField(auto_now_add=True)
    department=models.CharField(max_length=100)


class department(models.Model):
    department=models.CharField(max_length=100)
    setlimit=models.CharField(max_length=100)
    asha_limit=models.CharField(max_length=100)
    token=models.CharField(max_length=100)
    added_by=models.CharField(max_length=100)
    added_on = models.DateTimeField(auto_now_add=True)
    rotary_limit=models.CharField(max_length=100,null=True)


class subdepartment(models.Model):
    department_id=models.CharField(max_length=100)
    sub=models.CharField(max_length=100)
    setlimit=models.CharField(max_length=100)
    added_by=models.CharField(max_length=100)
    added_on = models.DateTimeField(auto_now_add=True)


class patients(models.Model):
    name=models.CharField(max_length=100)
    contact=models.CharField(max_length=100)
    age=models.CharField(max_length=100,null=True)
    gender=models.CharField(max_length=100,null=True)
    code=models.CharField(max_length=100)
    securitypin=models.CharField(max_length=100)
    department=models.CharField(max_length=100)
    subdepartment=models.CharField(max_length=100)
    followup=models.IntegerField(default=0)
    followupdate=models.DateField(null=True)
    remarks=models.CharField(max_length=1000)
    consulted=models.IntegerField(default=0)
    confirm_entry=models.IntegerField(default=0)
    added_by=models.CharField(max_length=100)
    role=models.CharField(max_length=100,null=True)
    added_on = models.DateTimeField(auto_now_add=True)
    token_no=models.IntegerField(default=0)
    confirmed_by=models.CharField(max_length=100,null=True)
    agebelow1=models.IntegerField(default=0)
    consulted_by=models.CharField(max_length=100,null=True)
    medicineissued_by=models.CharField(max_length=100,null=True)
    medicineissued = models.IntegerField(default=0)
    medicineamount = models.BigIntegerField(null=True, blank=True)
    isdeleted = models.IntegerField(default=0)

