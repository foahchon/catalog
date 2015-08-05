class UserProfile:
    """Class for storing user-related information. Primarily to ease passing
    user information to Jinja views.
    """

    def __init__(self, username=None, email=None, picture=None, logged_in=False):
        self.username = username
        self.email = email
        self.picture = picture
        self.logged_in = logged_in
