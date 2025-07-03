# questionnaire/middleware.py
from django.shortcuts import redirect
from django.urls import reverse

class DownloadRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Check if this is a PDF download response
        if (response.get('Content-Type') == 'application/pdf' and 
            'download_completed' in request.session and
            'completed_application_id' in request.session):
            
            application_id = request.session['completed_application_id']
            final_url = reverse('final_page', kwargs={'application_id': application_id})
            
            # Create a new response that redirects after download
            redirect_response = redirect(final_url)
            redirect_response['Refresh'] = f'0;url={final_url}'
            return redirect_response
            
        return response