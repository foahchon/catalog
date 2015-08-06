import random
import string
from flask import session, make_response
from sqlalchemy import func
from sqlalchemy.orm.exc import NoResultFound
from application import db_session
from database_setup import CatalogItem, Category, User
from user_profile import UserProfile


# Token-related helpers

def generate_token():
    """Generates and returns a 32-character token string.
    """

    return ''.join(
        random.choice(string.ascii_uppercase + string.digits) for _ in xrange(32))


def insert_signin_state():
    """Inserts Google sign-in token into active session.
    """

    session['state'] = generate_token()


def insert_csrf_token():
    """Inserts CSRF token into active session.
    """

    session['csrf_token'] = generate_token()


def get_signin_token():
    """Retrieves Google sign-in token from active session.
    """

    return session.get('state')


def get_csrf_token():
    """Retrieves CSRF token from active session.
    """

    return session.get('csrf_token')


# User-related helpers

def user_owns_item(item_id):
    """Checks to see if active user owns item with ID item_id.

    Args:
        item_id: ID of item to check ownership of.

    Returns:
        True if item with ID does belong to the active user;
        otherwise False.
    """

    if session.get('logged_in'):
        user = get_user(session.get('google_id'))
        item = db_session.query(CatalogItem).filter_by(id=item_id).one()

        return user.id == item.user_id

    return False


def create_user(login_session):
    """Creates new User instance and inserts it into the database.

    Args:
        login_session: Active session.

    Returns:
        Newly-created User instance.
    """

    new_user = User(name=login_session['username'],
                    picture=login_session['picture'],
                    email=login_session['email'],
                    google_id=login_session['google_id'])

    db_session.add(new_user)
    db_session.commit()

    return db_session.query(User).filter_by(google_id=login_session['google_id']).one()


def get_user(google_id):
    """Retrieves User instance from database based on Google ID.

    Args:
        google_id: Google ID of user.

    Returns:
        User instance associated with google_id.
    """
    try:
        user = db_session.query(User).filter_by(google_id=google_id).one()
        return user

    except NoResultFound:
        return None


def get_current_user_profile():
    """Builds and returns UserProfile instance based on information in
    current active session.
    """

    if session.get('logged_in'):
        return UserProfile(username=session.get('username'),
                           email=session.get('email'),
                           picture=session.get('picture'),
                           logged_in=True)

    return UserProfile(logged_in=False)


# Category helpers

def get_category_summary():
    """Retrieves list of summary information for categories in database.
    Fields include ID, name, and item count.

    Returns:
        List of summary category data.
    """

    categories = db_session \
        .query(Category.id, Category.name,
               func.count(CatalogItem.category_id).label('item_count')) \
        .outerjoin(CatalogItem) \
        .group_by(Category.id) \
        .all()
    return categories


# HTTP error helpers

def item_not_found():
    """Returns 404 HTTP response with message "Item not found."
    """

    return make_response('Item not found.', 404)


def bad_csrf_token():
    """Returns 400 HTTP response with message "Invalid form data submitted."
    """

    return make_response('Invalid form data submitted.', 401)


def not_signed_in():
    """Returns 401 HTTP response with message "User must be signed in."
    """

    return make_response('User must be signed in.', 401)


def not_authorized():
    """Returns 401 HTTP response with message "User is not authorized to perform this
    action."
    """

    return make_response('User is not authorized to perform this action.', 401)
