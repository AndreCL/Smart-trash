import datetime
import time

from cloudant.account import Cloudant
from cloudant.document import Document


class Login:
    """This class deals with all login and logout
    Functions: log_in(username, password): Returns true for success, false for failure
    log_state: returns if you are logged in or not
    log_out: Logs out, returns true
    get_user: Returns username
    get_usergroup: Returns usergroup
    TODO: Implement log of attempts
    """

    def __init__(self):
        self.state = False  # Am I logged in?
        self.current_user = ""
        self.current_usergroup = 0

    def log_state(self):
        return self.state

    def get_user(self):
        return self.current_user

    def get_usergroup(self):
        """Usergroup 1: Admin
        Usergroup 2: User"""
        return self.usergroup

    # Todo: Save to files
    def log_of_attempts(self):
        return True

    def log_in(self, user, password):

        # Connect to database
        USERNAME = "" # ADD YOUR OWN
        PASSWORD = "" # ADD YOUR OWN
        URL="" # ADD YOUR OWN
        self.client = Cloudant(USERNAME, PASSWORD, url=URL)
        self.client.connect()

        # Get users database
        # print 'Databases: {0}'.format(self.client.all_dbs()) # Debugging
        login_db = self.client[u'users']
        # print type(login_db) # debugging

        # TODO: Get from own class
        ts = time.time()
        st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

        # if user in self.users:
        user_found = Document(login_db, user)

        if user_found.exists():

            # Get password from DB
            with Document(login_db,user) as document:
                temp_pass = document[u'password']
                temp_usergroup = document[u'usergroup']

            if password == temp_pass:
                self.log_of_attempts  # userlogins.append([user, password, st])
                self.state = True
                self.current_user = user
                self.current_usergroup = int(temp_usergroup)
                return True
            else:
                self.log_of_attempts  # userrequests.append([user, password, st])
                print "Wrong password"
                return False
        else:
            self.log_of_attempts  # userrequests.append([user, password, st])
            print "User not found"
            return False

    def log_out(self):
        self.current_usergroup = 0
        self.current_user = ""
        self.state = False
        self.client.disconnect()  # disconnect to DB
        return True
