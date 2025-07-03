from django import forms
from .models import Respondent, ResponsePDF

class RespondentForm(forms.ModelForm):
    class Meta:
        model = Respondent
        fields = '__all__'
        widgets = {
            'gender': forms.RadioSelect,
            'profession': forms.RadioSelect,
            'specialization': forms.RadioSelect,
            'place_of_residence': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].label = "Name (As in Aadhaar Card)"
        self.fields['mobile_number'].label = "Mobile Number (OTP Validation)"
        self.fields['email'].label = "Email ID (optional)"
        self.fields['state'].label = "State/UT"
        self.fields['place_of_residence'].label = "Place of Residence"
        self.fields['profession'].label = "Respondent Type (Profession)"
        self.fields['specialization'].label = "Area of Specialization/Interest"

class UploadVerificationForm(forms.Form):
    application_id = forms.UUIDField(
        label="Application ID",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your Application ID'
        })
    )
    name = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your full name'
        })
    )

class ResponseUploadForm(forms.ModelForm):
    class Meta:
        model = ResponsePDF
        fields = ['pdf_file']
        widgets = {
            'pdf_file': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf'
            })
        }