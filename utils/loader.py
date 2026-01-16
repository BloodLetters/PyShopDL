import base64

class loader:
    def __init__(self):
        self.account = {
            'ruiiixx': 'UzY3R0JUQjgzRDNZ',
            'premexilmenledgconis': 'M3BYYkhaSmxEYg==',
            'vAbuDy': 'Qm9vbHE4dmlw',
            'adgjl1182': 'UUVUVU85OTk5OQ==',
            'gobjj16182': 'enVvYmlhbzgyMjI=',
            '787109690': 'SHVjVXhZTVFpZzE1'
        }
        
    def getPassword(self, usn):
        PASSWORDS = {user: base64.b64decode(pw).decode('utf-8') for user, pw in self.account.items()}
        return PASSWORDS.get(usn, None)
