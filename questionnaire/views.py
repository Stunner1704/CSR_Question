import os
import uuid
from io import BytesIO
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, Http404, HttpResponseRedirect
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from .models import Respondent
from .forms import RespondentForm
from .constants import SECTION_B_QUESTIONS
from django.urls import reverse
from django.conf import settings
import tempfile
import shutil
from .forms import UploadVerificationForm, ResponseUploadForm
from .models import ResponsePDF
from django.contrib import messages
import random
import logging

logger = logging.getLogger(__name__)

def home(request):
    return render(request, 'questionnaire/home.html')

def set_language(request, language):
    request.session['language'] = language
    return redirect('home')


def section_a(request):
    if request.method == 'POST':
        form = RespondentForm(request.POST)
        if form.is_valid():
            respondent = form.save()
            messages.success(request, "Registration successful! You can now access the questionnaire.")
            return redirect('home')
    else:
        form = RespondentForm()
    return render(request, 'questionnaire/section_a.html', {'form': form})



def download_options(request, application_id):
    # Validate application ID format
    if not (application_id.isdigit() and len(application_id) == 8):
        raise Http404("Invalid application ID format")
    # Check mobile verification
    verified_mobile = request.session.get('verified_mobile')
    if not verified_mobile:
        messages.error(request, "Mobile verification required")
        return redirect('home')
    
    respondent = get_object_or_404(Respondent, application_id=application_id)
    
    # Verify mobile matches respondent
    if respondent.mobile_number != verified_mobile:
        messages.error(request, "Mobile number doesn't match registration")
        return redirect('home')
    
    return render(request, 'questionnaire/download_options.html', {
        'respondent': respondent
    })


def verify_mobile(request):
    if request.method == 'POST':
        mobile_number = request.POST.get('mobile_number')
        
        try:
            respondent = Respondent.objects.get(mobile_number=mobile_number)
            request.session['verified_mobile'] = mobile_number
            return redirect('download_options', application_id=respondent.application_id)
            
        except Respondent.DoesNotExist:
            messages.error(request, "No registration found with this mobile number. Please check your number or register first.")
    
    return redirect('home')

def section_b(request, application_id):
    respondent = get_object_or_404(Respondent, application_id=application_id)
    
    sections = [
        {'name': 'Legislative Relations', 'key': 'legislative'},
        {'name': 'Administrative Relations', 'key': 'administrative'},
        {'name': 'Financial Relations', 'key': 'financial'},
        {'name': 'Role of Commissions and Councils', 'key': 'commissions'},
        {'name': 'Constitutional and Judicial Influences', 'key': 'constitutional'},
        {'name': 'Challenges and Issues', 'key': 'challenges'},
        {'name': 'Specific Examples', 'key': 'examples'},
        {'name': 'Important Articles', 'key': 'articles'},
        {'name': 'Articles Related to Financial Relations', 'key': 'financial_articles'},
    ]
    
    # Add question count and download status to each section
    for section in sections:
        section_key = section['key']
        section['count'] = len(SECTION_B_QUESTIONS.get(section_key, []))
        section['downloaded'] = section_key in respondent.sections_downloaded
    
    return render(request, 'questionnaire/section_b.html', {
        'respondent': respondent,
        'sections': sections
    })

def generate_full_pdf(respondent):
    """Helper function to generate full PDF content"""
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Set up fonts
    try:
        font_path = os.path.join(os.path.dirname(__file__), 'fonts/Helvetica.ttf')
        pdfmetrics.registerFont(TTFont('Helvetica', font_path))
        pdfmetrics.registerFont(TTFont('Helvetica-Bold', font_path))
        title_font = "Helvetica-Bold"
        text_font = "Helvetica"
    except:
        title_font = "Helvetica-Bold"
        text_font = "Helvetica"
    
    # Title on first page
    p.setFont(title_font, 16)
    p.drawCentredString(width/2, height-50, "Centre-State Relations Questionnaire - Full")
    
    # Respondent info and Application ID
    p.setFont(text_font, 10)
    respondent_info = (
        f"Name: {respondent.name} | Profession: {respondent.get_profession_display()} | "
        f"Specialization: {respondent.get_specialization_display()} | "
        f"State: {respondent.state} | Date: {respondent.created_at.strftime('%d-%m-%Y')}"
    )
    p.drawString(50, height-80, respondent_info)
    
    app_id_text = f"Application ID: {respondent.application_id}"
    p.drawString(50, height-100, app_id_text)
    
    form = p.acroForm
    y_position = height - 130  # Start below header
    section_keys = list(SECTION_B_QUESTIONS.keys())
    
    for section_idx, section_key in enumerate(section_keys):
        section_number = section_idx + 1
        questions = SECTION_B_QUESTIONS[section_key]
        
        # Section header
        p.setFont(title_font, 14)
        section_title = section_key.replace('_', ' ').title()
        p.drawString(50, y_position, f"{section_number}. {section_title}")
        y_position -= 30
        
        for q_idx, question in enumerate(questions):
            # Question text
            p.setFont(title_font, 11)
            question_text = f"{q_idx+1}. {question}"
            
            # Wrap text
            max_width = width - 100
            words = question_text.split()
            lines = []
            current_line = []
            
            for word in words:
                test_line = ' '.join(current_line + [word])
                if p.stringWidth(test_line, title_font, 11) <= max_width:
                    current_line.append(word)
                else:
                    lines.append(' '.join(current_line))
                    current_line = [word]
            
            if current_line:
                lines.append(' '.join(current_line))
            
            # Draw question
            text_y = y_position
            for line in lines:
                p.drawString(50, text_y, line)
                text_y -= 15
            
            # Create fillable field
            field_name = f"answer_{section_key}_{q_idx}"
            field_height = 80
            form.textfield(
                name=field_name,
                tooltip=f"Answer for question {section_number}.{q_idx+1}",
                x=50,
                y=text_y - field_height - 10,
                width=width-100,
                height=field_height,
                borderColor=colors.black,
                fillColor=colors.white,
                textColor=colors.black,
                fontSize=10,
                borderWidth=1,
                fieldFlags=4096  # Multi-line flag
            )
            
            y_position = text_y - field_height - 40
            
            # Page break if needed
            if y_position < 100 and (section_idx < len(section_keys)-1 or q_idx < len(questions)-1):
                p.showPage()
                y_position = height - 50
                # Simplified header for subsequent pages
                p.setFont(title_font, 16)
                p.drawCentredString(width/2, y_position, "Centre-State Relations Questionnaire - Full (Continued)")
                y_position -= 50
                p.setFont(text_font, 10)
                p.drawString(50, y_position, app_id_text)
                y_position -= 30
    
    p.save()
    return buffer.getvalue()

def generate_section_pdf(respondent, section_key):
    """Helper function to generate section PDF content"""
    questions = SECTION_B_QUESTIONS.get(section_key, [])
    
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Set up fonts
    try:
        font_path = os.path.join(os.path.dirname(__file__), 'fonts/Helvetica.ttf')
        pdfmetrics.registerFont(TTFont('Helvetica', font_path))
        pdfmetrics.registerFont(TTFont('Helvetica-Bold', font_path))
        title_font = "Helvetica-Bold"
        text_font = "Helvetica"
    except:
        title_font = "Helvetica-Bold"
        text_font = "Helvetica"
    
    # Title
    p.setFont(title_font, 16)
    p.drawCentredString(width/2, height-50, "Centre-State Relations Questionnaire")
    
    # Section info
    section_names = {
        'legislative': 'Legislative Relations',
        'administrative': 'Administrative Relations',
        'financial': 'Financial Relations',
        'commissions': 'Role of Commissions and Councils',
        'constitutional': 'Constitutional and Judicial Influences',
        'challenges': 'Challenges and Issues',
        'examples': 'Specific Examples',
        'articles': 'Important Articles',
        'financial_articles': 'Articles Related to Financial Relations',
    }
    section_title = section_names.get(section_key, section_key.replace('_', ' ').title())
    
    p.setFont(title_font, 14)
    p.drawString(40, height-80, section_title)
    
    # Respondent info and Application ID
    p.setFont(text_font, 9)
    respondent_info = (
        f"Name: {respondent.name} | Profession: {respondent.get_profession_display()} | "
        f"Specialization: {respondent.get_specialization_display()} | "
        f"State: {respondent.state} | Date: {respondent.created_at.strftime('%d-%m-%Y')}"
    )
    p.drawString(40, height-100, respondent_info)
    
    app_id_text = f"Application ID: {respondent.application_id}"
    p.drawString(40, height-120, app_id_text)
    
    # Initialize AcroForm
    form = p.acroForm
    
    # Questions and answer fields
    y_position = height - 150
    for i, question in enumerate(questions):
        # Question text
        p.setFont(title_font, 11)
        question_text = f"{i+1}. {question}"
        
        # Wrap text
        max_width = width - 100
        words = question_text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            if p.stringWidth(test_line, title_font, 11) <= max_width:
                current_line.append(word)
            else:
                lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        # Draw question
        text_y = y_position
        for line in lines:
            p.drawString(50, text_y, line)
            text_y -= 15
        
        # Create fillable field
        field_name = f"answer_{i}"
        field_height = 80
        form.textfield(
            name=field_name,
            tooltip=f"Answer for question {i+1}",
            x=50,
            y=text_y - field_height - 10,
            width=width-100,
            height=field_height,
            borderColor=colors.black,
            fillColor=colors.white,
            textColor=colors.black,
            fontSize=10,
            borderWidth=1,
            fieldFlags=4096  # Multi-line flag
        )
        
        y_position = text_y - field_height - 40
        
        # Page break if needed
        if y_position < 100 and i < len(questions)-1:
            p.showPage()
            y_position = height - 50
            p.setFont(title_font, 16)
            p.drawCentredString(width/2, y_position, f"{section_title} (Continued)")
            y_position -= 50
            p.setFont(text_font, 9)
            p.drawString(40, y_position, app_id_text)
            y_position -= 30
    
    p.save()
    return buffer.getvalue()


def download_full_pdf(request, application_id):
    respondent = get_object_or_404(Respondent, application_id=application_id)
    if respondent.full_downloaded:
        return HttpResponse("Full questionnaire has already been downloaded.", status=403)
    
    respondent.full_downloaded = True
    respondent.save()
    return redirect('download_trigger', application_id=application_id, download_type='full')

def download_section_pdf(request, application_id, section_key):
    respondent = get_object_or_404(Respondent, application_id=application_id)
    if section_key not in SECTION_B_QUESTIONS:
        raise Http404("Section not found")
    
    if section_key in respondent.sections_downloaded:
        return HttpResponse(f"Section '{section_key}' has already been downloaded.", status=403)
    
    downloaded_sections = respondent.sections_downloaded
    downloaded_sections[section_key] = True
    respondent.sections_downloaded = downloaded_sections
    respondent.save()
    return redirect('download_trigger_section', 
                   application_id=application_id, 
                   download_type='section',
                   section_key=section_key)


# def download_trigger(request, application_id, download_type, section_key=None):
#     respondent = get_object_or_404(Respondent, application_id=application_id)
#     final_url = reverse('final_page', args=[application_id])
    
#     if download_type == 'full':
#         download_url = reverse('serve_pdf', args=[application_id, 'full'])
#     else:
#         download_url = reverse('serve_pdf_section', 
#                               args=[application_id, 'section', section_key])
    
#     return render(request, 'questionnaire/download_trigger.html', {
#         'download_url': download_url,
#         'redirect_url': final_url
#     })

def download_trigger(request, application_id, download_type, section_key=None):
    respondent = get_object_or_404(Respondent, application_id=application_id)
    final_url = reverse('final_page', kwargs={'application_id': application_id})
    
    if download_type == 'full':
        download_url = reverse('serve_pdf', kwargs={'application_id': application_id, 'pdf_type': 'full'})
    else:
        download_url = reverse('serve_pdf_section', 
                             kwargs={'application_id': application_id, 
                                    'pdf_type': 'section', 
                                    'section_key': section_key})
    
    return render(request, 'questionnaire/download_trigger.html', {
        'download_url': download_url,
        'redirect_url': final_url
    })


def serve_pdf(request, application_id, pdf_type, section_key=None):
    respondent = get_object_or_404(Respondent, application_id=application_id)
    
    if pdf_type == 'full':
        pdf_content = generate_full_pdf(respondent)
        filename = f"CSR_Full_Questionnaire_{respondent.application_id}.pdf"
    else:
        pdf_content = generate_section_pdf(respondent, section_key)
        filename = f"CSR_{section_key}_{respondent.application_id}.pdf"
    
    response = HttpResponse(pdf_content, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response





def final_page(request, application_id):
    respondent = get_object_or_404(Respondent, application_id=application_id)
    return render(request, 'questionnaire/final_page.html', {
        'respondent': respondent
    })





def upload_start(request):
    if request.method == 'POST':
        form = UploadVerificationForm(request.POST)
        if form.is_valid():
            application_id = form.cleaned_data['application_id']
            name = form.cleaned_data['name'].strip()
            
            # First check if application ID exists
            if not Respondent.objects.filter(application_id=application_id).exists():
                form.add_error('application_id', "This Application ID does not exist.")
                return render(request, 'questionnaire/upload_start.html', {'form': form})
            
            try:
                respondent = Respondent.objects.get(
                    application_id=application_id,
                    name__iexact=name
                )
                request.session['verified_respondent_id'] = str(respondent.id)
                return redirect('upload_pdf', application_id=application_id)
                
            except Respondent.DoesNotExist:
                logger.error(f"Name mismatch for ID {application_id}: Expected name not found")
                form.add_error('name', "Name does not match our records. Please ensure it matches exactly what you entered in Section A.")
    else:
        form = UploadVerificationForm()
    
    return render(request, 'questionnaire/upload_start.html', {'form': form})


def upload_pdf(request, application_id):
    # Check session verification
    respondent_id = request.session.get('verified_respondent_id')
    if not respondent_id:
        return redirect('upload_start')
    
    respondent = get_object_or_404(Respondent, id=respondent_id, application_id=application_id)
    
    if request.method == 'POST':
        form = ResponseUploadForm(request.POST, request.FILES)
        if form.is_valid():
            response_pdf = form.save(commit=False)
            response_pdf.respondent = respondent
            response_pdf.save()
            
            # Send verification email (would need email setup)
            # send_verification_email(response_pdf)
            
            messages.success(request, "Your response has been uploaded successfully!")
            return redirect('upload_success', application_id=application_id)
    else:
        form = ResponseUploadForm()
    
    return render(request, 'questionnaire/upload_pdf.html', {
        'form': form,
        'respondent': respondent
    })

def upload_success(request, application_id):
    respondent = get_object_or_404(Respondent, application_id=application_id)
    return render(request, 'questionnaire/upload_success.html', {'respondent': respondent})

def verify_response(request, verification_code):
    try:
        response_pdf = ResponsePDF.objects.get(verification_code=verification_code)
        response_pdf.is_verified = True
        response_pdf.save()
        messages.success(request, "Your response has been verified successfully!")
        return redirect('home')
    except ResponsePDF.DoesNotExist:
        messages.error(request, "Invalid verification code")
        return redirect('home')