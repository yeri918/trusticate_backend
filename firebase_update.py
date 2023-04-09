import os 
import shutil
import json
import firebase_admin
from firebase_admin import credentials, firestore, storage
import configparser
import pandas as pd
import w3storage

class Firebase_update():
    def __init__(self):
        self.cred = credentials.Certificate("/cert-issuer/serviceAccountKey.json")
        self.admin = firebase_admin.initialize_app(self.cred, {'storageBucket' : 'trusticate-a346c.appspot.com'})
        self.db = firestore.client()

    
    def upload_files_to_storage(self, uid="D6zAcainsELrBohRwmiV", batch_id="wtS192Jk9bo8lIavn6Vv"):
        bucket = storage.bucket()
        local_directory_path = '/cert-issuer/data/blockchain_certificates/'+batch_id
        
        json_files = [f for f in os.listdir(local_directory_path) if f.endswith('.json')]

        for i in range(len(json_files)):
            local_file_path = os.path.join(local_directory_path, json_files[i])
            print(local_file_path)
            with open(local_file_path, 'r') as f:
                data = json.load(f)
            
            name = data['credentialSubject']['name']
            print("name:", name)
            new_file_path = os.path.join(local_directory_path, name+'.json')
            os.rename(local_file_path, new_file_path)
            
            destination_blob_name = uid+'/'+batch_id+'/signed_certificates/'+name+".json"
            blob = bucket.blob(destination_blob_name) # Blob object for the file 
            with open(new_file_path, 'rb') as json_file:
                blob.upload_from_file(json_file, content_type='application/json')

    def get_issuer_info(self, uid="D6zAcainsELrBohRwmiV"):
        school_doc = self.db.collection('schools').document(uid).get()
        data = school_doc.to_dict()
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
        # config.set('BatchConfig', 'unsigned_certificates_dir', "unsigned_certificates/"+batch_id)
        
        with open(conf_file_path, 'w') as configfile:
            config.write(configfile)
        
        # Remove the directory if exists
        # unsigned_dir_path = '/cert-issuer/data/unsigned_certificates/'+batch_id
        # if os.path.exists(unsigned_dir_path):
        #     shutil.rmtree(unsigned_dir_path)
        
        # For cert-issuer
        self.update_conf_certissuer(issuer_data, uid, batch_id)
        
    def update_conf_certissuer(self, issuer_data, uid, batch_id):
        
        config = configparser.ConfigParser()
        conf_file_path = './conf.ini'
        try:
            config.read(conf_file_path)
        except configparser.ParsingError as e:
            print("ParsingError", e)

        config.set('IssuerInformation', 'issuing_address', issuer_data['publicKey'])
        signed_certificates_dir = 'data/blockchain_certificates/'+batch_id
        # unsigned_certificates_dir = 'data/unsigned_certificates/'+batch_id
        # config.set('DataDir', 'unsigned_certificates_dir', unsigned_certificates_dir)
        config.set('DataDir', 'blockchain_certificates_dir', signed_certificates_dir)

        with open(conf_file_path, 'w') as configfile:
            config.write(configfile)
        
        # Remove the directory if exists
        # signed_dir_path = '/cert-issuer/data/blockchain_certificates/'+batch_id
        # if os.path.exists(signed_dir_path):
        #     shutil.rmtree(signed_dir_path)
    
    def update_roster(self, uid="D6zAcainsELrBohRwmiV", batch_id="wtS192Jk9bo8lIavn6Vv"):
        student_docs = self.db.collection('schools').document(uid).collection('issuance').document(batch_id).collection('students').get()
        df = pd.DataFrame(columns=['name', 'identity', 'publicKey', 'hasCredential', 'educationalCredentialAwarded'])
        print(student_docs)
        for student in student_docs:
            df = df.append(student.to_dict(), ignore_index=True)
        
        print(df.head())
        df.to_csv('./data/rosters/roster_testnet.csv', index=False)

    def update_cid(self, uid="D6zAcainsELrBohRwmiV", batch_id="wtS192Jk9bo8lIavn6Vv"):
        my_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkaWQ6ZXRocjoweEMwQUZmQzllMEZERWY3NjU0YTM1Y2FmMUU2OUMxNGRFNzM2MzYyREMiLCJpc3MiOiJ3ZWIzLXN0b3JhZ2UiLCJpYXQiOjE2ODAwOTkwMTgyNjUsIm5hbWUiOiJ0cnVzdGljYXRlIn0.B-hxjB8BnwBzIbIxjhy416QhWuqUMJzAPpO0cVUnQTE"

        w3 = w3storage.API(token=my_token)

        some_uploads = w3.user_uploads(size=25)
        dir_path = '/cert-issuer/data/blockchain_certificates/'+batch_id

        for file_name in os.listdir(dir_path):
            local_file_path = os.path.join(dir_path, file_name)
            
            doc_snapshot = self.db.collection('schools').document(uid).collection('issuance').document(batch_id).collection('students').where('name','==', file_name[:-5]).get()
            if doc_snapshot != []:
                cid = w3.post_upload((file_name, open(local_file_path, 'rb')))
                doc_ref = doc_snapshot[0].reference
                doc_ref.update({ 'ipfs':'https://{}.ipfs.w3s.link/'.format(cid) })
            else:
                continue

    def update_issuance_status(self, uid, batch_id):
        doc_ref = self.db.collection('schools').document(uid).collection('issuance').document(batch_id)
        doc_ref.update({'status':True})


