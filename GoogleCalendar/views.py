from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
import os
from django.http import JsonResponse
from django.views import View
from django.shortcuts import redirect




# This is set to true to enable OAuthlibs verification when you run your program locally
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'




class GoogleCalendarInitView(View):

    #Start the OAuth2 authorization
    

    def get(self, request, *args, **kwargs):
        # Creating an instance to manage the flow.
        flow = InstalledAppFlow.from_client_secrets_file(
            'client_secret.json',
            scopes=['https://www.googleapis.com/auth/calendar.events']
        )

        # This should match one of the authorized redirect URIs otherwise you will get an mismatch error.
        
        flow.redirect_uri = 'http://localhost:8000/rest/v1/calendar/redirect'

        authorization_url, state = flow.authorization_url(
            # Enable offline access so that you can refresh an access token without
            # re-prompting the user for permission. Recommended for web server apps.
            access_type='offline',
            # Enable incremental authorization. Recommended as a best practice.
            include_granted_scopes='true',
        )

        # Store the state so the callback can verify the auth server response.
        request.session['state'] = state

        # Redirect the user to the authorization URL.
        return redirect(authorization_url)



class GoogleCalendarEventsView(View):
    #Fetching events from Google Calendar View

    def get(self, request, *args, **kwargs):
        credentials = Credentials(
            **request.session['credentials']
        )

        service = build('calendar', 'v3', credentials=credentials)

        

        # Calling the Calendar API
        events_result = service.events().list(calendarId='primary', timeMin= '2022-01-01T00:00:00-07:00',
                                              maxResults=10, singleEvents=True, orderBy='startTime').execute()
        events = events_result.get('items', [])

        return JsonResponse({'status': 'success',
                             'message': 'Events have been fetched.',
                             'data': events
                             })





class GoogleCalendarRedirectView(View):
    """
    This view is registered as the redirect_uri in the Google OAuth2 client
    configuration. The authorization server will redirect the user to this view
    after the user has granted or denied permission to the client.
    """

    def get(self, request, *args, **kwargs):
        # Specify the state when creating the flow in the callback so that it can
        # verified in the authorization server response.
        state = request.GET.get('state')

        flow = InstalledAppFlow.from_client_secrets_file(
            'client_secret.json',
            scopes=['https://www.googleapis.com/auth/calendar.events'],
            state=state
        )
        flow.redirect_uri = 'http://localhost:8000/rest/v1/calendar/redirect'

        # Use the authorization server's response to fetch the OAuth 2.0 tokens.
        authorization_response = request.build_absolute_uri()
        flow.fetch_token(authorization_response=authorization_response)

        # Store the credentials in the session.
        credentials = flow.credentials

        request.session['credentials'] = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }

        # Fetching of events is done in a separate view.
        # Here we just redirect to the events view.
        return redirect('http://localhost:8000/rest/v1/calendar/events')

