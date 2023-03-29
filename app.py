#!/usr/bin/python3
import json
from flask import Flask, jsonify, request, abort, send_file
from flask_cors import CORS
from subprocess import call
import os 
import firebase_update

# from .firebase_update import firebase_update

import cert_issuer.config
from cert_issuer.blockchain_handlers import bitcoin
import cert_issuer.issue_certificates


app = Flask(__name__)
CORS(app, resources=r'*', headers='Content-Type')
fb = firebase_update.Firebase_update()

def get_config():
    global config
    if config == None:
        config = cert_issuer.config.get_config()
    return config

@app.route('/trusticate/certtools/generate_issuer_json', methods=['GET'])
def generate_json():
    try:
        os.system('python3 cert-tools/cert_tools/create_v2_issuer.py -c cert-tools/cert_tools/conf_v2.ini')
    except Exception as e:
        return jsonify({'code':500, 'message': e})
    return send_file('/cert-issuer/data/issuer.json', as_attachment=True)

@app.route('/trusticate/certtools/generate_revocation_json',methods=['GET'])
def generate_revocation():
    try: 
        os.system('python3 cert-tools/cert_tools/create_revocation_list.py -c cert-tools/cert_tools/conf_v2.ini')
    except Exception as e:
        return jsonify({'code':500, 'message': e})
    return send_file('/cert-issuer/data/revocation-list.json', as_attachment=True)

@app.route('/trusticate/issue_batch', methods=['GET'])
def issue_batch():
    data = request.get_json()
    uid = data['uid']
    batch_id = data['batch_id']

    # Update the conf file
    fb.update_conf_certtools()
    fb.update_roster()

    try:
        os.system('python3 cert-tools/cert_tools/create_v3_certificate_template.py -c ./conf_v2.ini')
    except Exception as e:
        return jsonify({'code':500, 'message': e})
    try:
        os.system('python3 cert-tools/cert_tools/instantiate_v3_certificate_batch.py -c ./conf_v2.ini')
    except Exception as e: 
        return jsonify({'code':500, 'message': e})
    
    # Issue unsigned certificates
    # try:
    #     os.system('python3 -m cert_issuer -c ./conf.ini')
    # except Exception as e: 
    #     return jsonify({'code':500, 'message': e})
    
    # Upload signed ceritifcates to Firebase Storage
    try:
        fb.upload_files_to_storage(uid="D6zAcainsELrBohRwmiV")
    except Exception as e: 
        return jsonify({'code':500, 'message': e})
    
    return jsonify({'code':200})

@app.route('/test2', methods=['GET'])
def test2():
    fb.update_roster()
    return jsonify({'test2':'hi'})

@app.route('/test', methods=['GET'])
def test():
    return jsonify({"test":"hi"})

@app.route('/cert_issuer/api/v1.0/issue', methods=['POST'])
def issue():
    config = get_config()
    certificate_batch_handler, transaction_handler, connector = \
            bitcoin.instantiate_blockchain_handlers(config, False)
    certificate_batch_handler.set_certificates_in_batch(request.json)
    cert_issuer.issue_certificates.issue(config, certificate_batch_handler, transaction_handler)
    return json.dumps(certificate_batch_handler.proof)

if __name__ == '__main__':
    app.run(host='0.0.0.0')
