import os 
import firebase_admin
from firebase_admin import credentials, firestore, storage
import configparser
import pandas as pd

class Firebase_update():
    def __init__(self):
        self.cred = credentials.Certificate("/cert-issuer/serviceAccountKey.json")
        self.admin = firebase_admin.initialize_app(self.cred, {'storageBucket' : 'trusticate-a346c.appspot.com'})
        self.db = firestore.client()

    def upload_files_to_storage(self, uid="D6zAcainsELrBohRwmiV", batch_id="wtS192Jk9bo8lIavn6Vv"):
        # batch_name = batch_id
        bucket = storage.bucket()
        print(batch_id, type(batch_id))
        local_directory_path = '/cert-issuer/data/blockchain_certificates/'+batch_id

        for file_name in os.listdir(local_directory_path):
            local_file_path = os.path.join(local_directory_path, file_name)
            destination_blob_name = uid+'/'+batch_id+'/signed_certificates/'+file_name
            blob = bucket.blob(destination_blob_name) # Blob object for the file 
            with open(local_file_path, 'rb') as json_file:
                blob.upload_from_file(json_file, content_type='application/json')

    def get_issuer_info(self, uid="D6zAcainsELrBohRwmiV"):
        school_doc = self.db.collection('schools').where('uid', '==', uid).limit(1).get()
        data = school_doc[0].to_dict()
        return data

    def update_conf_certtools(self, uid="PpXTkHhD2vMG9C7NwqH9ljyHCa13", batch_id="wtS192Jk9bo8lIavn6Vv"):
        issuer_data = self.get_issuer_info(uid)
        
        # For cert-tools
        config = configparser.ConfigParser()
        conf_file_path = './conf_v2.ini'
        try:
            config.read(conf_file_path)
        except configparser.ParsingError as e:
            print("ParsingError:", e)

        config.set('IssuerInformation', 'issuer_url', issuer_data['website'])
        config.set('IssuerInformation', 'issuer_email', issuer_data['email'])
        config.set('IssuerInformation', 'issuer_name', issuer_data['name'])
        config.set('IssuerInformation', 'issuer_public_key', issuer_data['publicKey'])
        config.set('IssuerInformation', 'revocation_list', issuer_data['revocationList'])
        config.set('IssuerInformation', 'issuer_id', issuer_data['issuerJSONURL'])

        with open(conf_file_path, 'w') as configfile:
            config.write(configfile)

        # For cert-issuer
        conf_file_path = './conf.ini'
        try:
            config.read(conf_file_path)
        except configparser.ParsingError as e:
            print("ParsingError", e)
    
        config.set('IssuerInformation', 'issuing_address', issuer_data['publicKey'])
        signed_certificates_dir = 'data/blockchain_certificates/'+batch_id
        config.set('DataDir', 'blockchain_certificates_dir', signed_certificates_dir)
    
    def update_roster(self, uid="D6zAcainsELrBohRwmiV", batch_id="wtS192Jk9bo8lIavn6Vv"):
        # school_doc = self.db.collection('schools').where('uid', '==', uid).limit(1).get()
        # print(school_doc[0].id)
        # issuance_doc = self.db.collection('schools').document(school_doc[0].id).collection('issuance').where('batch_id','==', batch_id).limit(1).get()
        # print(issuance_doc[0].id)
        student_docs = self.db.collection('schools').document(uid).collection('issuance').document(batch_id).collection('students').get()
        df = pd.DataFrame(columns=['name', 'identity', 'publicKey', 'hasCredential', 'educationalCredentialAwarded'])

        for student in student_docs:
            df = df.append(student.to_dict(), ignore_index=True)
            df.to_csv('./data/rosters/roster_testnet.csv', index=False)
