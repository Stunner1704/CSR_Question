import random
from django.db import models
from django.core.exceptions import ValidationError
from uuid import uuid4  # Add this import back

def generate_application_id():
    """Generate an 8-digit unique application ID"""
    while True:
        app_id = str(random.randint(10000000, 99999999))  # 8-digit number
        if not Respondent.objects.filter(application_id=app_id).exists():
            return app_id

class Respondent(models.Model):
    PROFESSION_CHOICES = [
        ('Politicians', 'Politicians'),
        ('Academician', 'Academician'),
        ('Scholars', 'Scholars'),
        ('Researchers', 'Researchers'),
        ('Journalists', 'Journalists'),
        ('Activists', 'Activists'),
        ('MP/MLA', 'MP/MLA'),
        ('Bureaucrat', 'Bureaucrat'),
        ('Government Official', 'Government Official'),
        ('Sitting / Retired Judges', 'Sitting / Retired Judges'),
        ('Others', 'Others'),
    ]
    
    SPECIALIZATION_CHOICES = [
        ('Constitutional Law', 'Constitutional Law'),
        ('Political Science', 'Political Science'),
        ('Public Administration', 'Public Administration'),
        ('Economics', 'Economics'),
        ('Other', 'Other'),
    ]
    
    name = models.CharField(max_length=100)
    gender = models.CharField(max_length=20, choices=[
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Transgender', 'Transgender')
    ])
    mobile_number = models.CharField(max_length=15)
    email = models.EmailField(blank=True, null=True)
    state = models.CharField(max_length=50)
    place_of_residence = models.TextField()
    profession = models.CharField(max_length=50, choices=PROFESSION_CHOICES)
    specialization = models.CharField(max_length=50, choices=SPECIALIZATION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    application_id = models.CharField(max_length=8, unique=True, default=generate_application_id, editable=False)
    full_downloaded = models.BooleanField(default=False)
    sections_downloaded = models.JSONField(default=dict, blank=True)
    download_option = models.CharField(
        max_length=10,
        choices=[('FULL', 'Full Questionnaire'), ('SECTION', 'Section-wise')],
        blank=True,
        null=True
    )

    def __str__(self):
        return f"{self.name} ({self.application_id})"

    def clean(self):
        # Validate application_id is exactly 8 digits
        if len(self.application_id) != 8 or not self.application_id.isdigit():
            raise ValidationError("Application ID must be an 8-digit number")

class ResponsePDF(models.Model):
    respondent = models.ForeignKey(Respondent, on_delete=models.CASCADE, related_name='responses')
    pdf_file = models.FileField(upload_to='response_pdfs/')
    upload_date = models.DateTimeField(auto_now_add=True)
    verification_code = models.UUIDField(default=uuid4, editable=False, unique=True)
    is_verified = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.respondent.name} - {self.upload_date.strftime('%Y-%m-%d')}"