import json

import requests
from uritools import urijoin
from flask import request, redirect, url_for, session, make_response
from curry import URL

from qdserver import env, domain
from . import login

AUTH0_DOMAIN        = env['AUTH0_DOMAIN']
AUTH0_CLIENT_ID     = env['AUTH0_CLIENT_ID']
AUTH0_CLIENT_SECRET = env['AUTH0_CLIENT_SECRET']

def setup_routes(app):
    @app.route('/auth/callback')
    def authCallback():
        """
        Auth0 callback
        """
        code = request.args.get('code')
        redirect_url = get_redirect_url()

        json_header = {'content-type': 'application/json'}
        token_url = "https://%s/oauth/token" % AUTH0_DOMAIN
        token_payload = \
            { 'client_id':          AUTH0_CLIENT_ID
            , 'client_secret':      AUTH0_CLIENT_SECRET
            , 'redirect_uri':       redirect_url
            , 'code':               code
            , 'grant_type':         'authorization_code'
            }
        response = requests.post(
            token_url,
            data = json.dumps(token_payload),
            headers = json_header,
            )

        if response.status_code != 200:
            return redirect(url_for('auth', error=response.reason))

        token_info = response.json()
        access_token = token_info['access_token']

        user_url = 'https://%s/userinfo' % AUTH0_DOMAIN
        response = requests.get(user_url, params={'access_token': access_token})
        if response.status_code != 200:
            return redirect(url_for('auth', error=response.reason))

        user_info = response.json()
        import pprint
        pprint.pprint(user_info)

        email_verified = user_info['email_verified']
        if email_verified:
            user_profile = login.UserProfile(
                { 'user_id':    user_info['user_id']
                , 'email':      user_info['email']
                , 'picture':    user_info['picture']
                , 'nickname':   user_info['nickname']
                })
            login.user_login(user_profile)
        return redirect('/')
        # return redirect('/verifyEmail', email=user_info['email'])


    @app.route('/auth/logout')
    def logout():
        login.user_logout()
        return redirect('/bars.html')

    ###

    def get_redirect_url() -> URL:
        """
        Return the redirect URL given as a request arg (?redirect_url=...)
        """
        return urijoin(domain, request.args.get('redirect_url', '/'))
