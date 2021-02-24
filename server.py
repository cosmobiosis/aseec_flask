from flask import Flask, request
import deepeye
import cv2
import numpy as np
import base64
import services
from msbl_reader import *

app = Flask(__name__)
eye_tracker = deepeye.DeepEye()
bootloader = MaximBootloader("files/MAX32664C_HSP2_WHRM_AEC_SCD_WSPO2_C_30.13.0.msbl")

@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/process', methods=['POST'])
def process():
    ret_json = {}
    try:
        ret_json = services.processSingleImage(eye_tracker, request.json["base64"])
    except Exception as e:
        ret_json = { "ERR" : str(e) }
    return ret_json

@app.route('/msblflashing', methods=['GET'])
def msblflashing():
    ret_json = {}
    try:
        ret_json = bootloader.get_response_data()
    except Exception as e:
        ret_json = { "ERR" : str(e) }
    return ret_json

if __name__ == '__main__':
    app.run(host="localhost", port=7070)