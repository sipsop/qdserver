from flask import Flask

# app = Flask(__name__) #, static_url_path='')
domain = 'http://localhost'

env = {
    'AUTH0_DOMAIN':        'tuppu.eu.auth0.com',
    'AUTH0_CLIENT_ID':     'phA8QFWKknNtcDwVefccBf82sIp4bw6c',
    'AUTH0_CLIENT_SECRET': 'jXtBkWhMD-UEk16iXeS1jLwEw9fCBrPXFasX0EKHSZIhmt-JxeRdyw3ipvxz9I6V',
}

from .qdserver import setup_routes
from .testing import run_query, run_feed, run_test_query, run_test_queries
