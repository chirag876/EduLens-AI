from functools import wraps

import requests
from fastapi import HTTPException

import app.server.database.core_data as core_service
from app.server.handler.error_handler import CustomHTTPException
from app.server.static.collections import Collections
from app.server.utils import date_utils


# pylint: disable=too-many-locals
def get_location(ip_address):
    if ip_address == '127.0.0.1':
        return 'Localhost', 'Localhost Region', 'Localhost Country'
    try:
        response = requests.get(f'https://ipinfo.io/{ip_address}/json')
        if response.status_code == 200:
            data = response.json()
            return data.get('city', 'Unknown City'), data.get('region', 'Unknown Region'), data.get('country', 'Unknown Country')
        return 'Unknown City', 'Unknown Region', 'Unknown Country'
    except Exception:
        return 'Unknown City', 'Unknown Region', 'Unknown Country'


def handle_response_data(log_entry, response):
    """
    Update the log entry with response data (status and file details).
    """
    if not isinstance(response, dict):
        log_entry['status'] = 'SUCCESS'
    else:
        log_entry['status'] = response.get('status', 'No Status')

        response_data = response.get('data', {})
        eia_file_data = response_data.get('eia_file_data')
        cia_file_data = response_data.get('cia_file_data')
        request_id = response_data.get('request_id')
        program_ids = response_data.get('program_ids', [])

        if eia_file_data:
            log_entry['eia_file_data'] = eia_file_data
        if cia_file_data:
            log_entry['cia_file_data'] = cia_file_data
        if request_id:
            log_entry['request_id'] = request_id
        if program_ids:
            log_entry['program_ids'] = program_ids


# flake8: noqa: C901
# pylint: disable=too-many-statements
def audit_log(action_name):
    """
    A decorator for logging user actions, including IP address, browser, and location.
    Logs the data to a MongoDB collection.
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = kwargs.get('request')
            if not request:
                raise ValueError('Request object must be passed as a keyword argument.')
            user_data = kwargs.get('user', {}) if kwargs.get('user', {}) else kwargs.get('_user', {})
            user_id = user_data.get('user_id')
            org_id = user_data.get('org_id')
            api_name = func.__name__
            timestamp = date_utils.get_current_timestamp()

            # Extract IP address and User-Agent
            # client_host = request.client.host if request.client else 'Unknown IP'
            client_ip = request.headers.get('X-Forwarded-For', request.client.host).split(',')[0]
            user_agent = request.headers.get('user-agent', 'Unknown Browser')

            # Fetch location based on IP
            city, region, country = get_location(client_ip)
            user_details = await core_service.read_one(Collections.USERS, {'_id': user_id, 'is_deleted': False})

            # Create the initial log entry with a placeholder for status (to be updated later)
            log_entry = {
                'user_id': user_id,
                'email': user_details.get('email'),
                'org_id': org_id,
                'api_name': api_name,
                'action_name': action_name,
                'profile_image_data': user_details.get('profile_image_data'),
                'timestamp': timestamp,
                'ip_address': client_ip,
                'browser': user_agent,
                'location': {'city': city, 'region': region, 'country': country},
            }
            file_type = kwargs.get('file_type')
            program_id = kwargs.get('program_id')  # Look for file_type in kwargs
            tr_request_id = kwargs.get('request_id')
            params = kwargs.get('params', {})
            program_ids = params.__dict__.get('program_ids', []) if params else None
            gradation_ids = params.__dict__.get('gradation_ids', []) if params else None
            if file_type:
                log_entry['file_type'] = file_type.value
            if program_id:
                log_entry['program_id'] = program_id
            if program_ids:
                log_entry['program_ids'] = program_ids
            if gradation_ids:
                gradations = await core_service.read_many(collection_name=Collections.GRADATION_UPLOAD_FILES, data_filter={'_id': {'$in': gradation_ids}})
                log_entry['program_ids'] = [gradation['program_id'] for gradation in gradations]
            if tr_request_id:
                tr_request = await core_service.read_one(collection_name=Collections.TR_REQUESTS, data_filter={'_id': tr_request_id})
                log_entry['program_ids'] = tr_request['program_ids']
            is_exception = False
            try:
                response = await func(*args, **kwargs)
                handle_response_data(log_entry, response)
            except CustomHTTPException as error:
                # If an error occurs, update the status to "FAIL" and capture the error message
                is_exception = True
                log_entry['status'] = 'FAIL'
                log_entry['error_message'] = error.detail
                response = {'errorCode': error.status_code, 'message': error.detail, 'identifier': error.identifier}
            except HTTPException as error:
                # If an error occurs, update the status to "FAIL" and capture the error message
                is_exception = True
                log_entry['status'] = 'FAIL'
                log_entry['error_message'] = error.detail
                response = {'errorCode': error.status_code, 'message': error.detail}
            except Exception as error:
                # If an error occurs, update the status to "FAIL" and capture the error message
                is_exception = True
                log_entry['status'] = 'FAIL'
                log_entry['error_message'] = error.args
                response = {'errorCode': 500, 'message': error.args}

            # Store the log entry (success or failure)
            await core_service.create_one(Collections.AUDIT_LOGS, log_entry)
            if is_exception:
                raise CustomHTTPException(status_code=response.get('errorCode', 500), detail=response.get('message', None), identifier=response.get('identifier', None))
            return response

        return wrapper

    return decorator
