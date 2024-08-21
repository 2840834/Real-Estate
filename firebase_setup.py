import firebase_admin
from firebase_admin import credentials, firestore

street_cred = credentials.Certificate("C:\\Users\\Lucas Gemmell\\Downloads\\testing-6fa60-firebase-adminsdk-6ocwe-c3ca51ff3d.json")

firebase_admin.initialize_app(street_cred)

db = firestore.client()

def return_db():
    return db
    
