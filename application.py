import io

import httplib2
import requests

# Needed for Google negotiations.
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError

# Flask dependencies.
from flask import Flask, render_template, request, \
    json, redirect, url_for, send_from_directory, jsonify, flash, \
    send_file, get_flashed_messages

# Sql Alchemy dependencies.
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Application-specific helpers and libraries.
from catalog_helpers import *
from catalog_json_encoder import CatalogJSONEncoder
from database_setup import Base, Category, CatalogItem

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
ALLOWED_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif']

# Connect to Database and create database session
engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

# Create database session.
DBSession = sessionmaker(bind=engine)
db_session = DBSession()


@app.route('/catalog.json')
def get_json_catalog():
    """Returns current catalog formatted to JSON.
    """
    catalog = db_session.query(Category).all()

    # jsonify function will make use of CatalogJSONEncoder class
    # (specified in app startup).
    return jsonify(Catalog=catalog)


@app.route('/static/<path:path>')
def send_static(path):
    """Sends file from "static" directory.

        Args:
            path: Name of file to be sent.

        Returns:
            HTTP response containing file.
    """

    return send_from_directory('static', path)


@app.route('/')
def show_categories():
    insert_signin_state()

    # Retrieve list of items from database ordered by
    # most recent 'created_at' date/time.
    latest_items = db_session.query(CatalogItem) \
        .order_by(CatalogItem.created_at.desc()) \
        .limit(10)

    return render_template('categories.html',
                           STATE=session['state'],
                           user=get_current_user_profile(),
                           category_summary=get_category_summary(),
                           latest_items=latest_items)


@app.route('/category/<int:category_id>')
def show_category(category_id):
    insert_signin_state()
    try:
        category = db_session.query(Category).filter_by(id=category_id).one()
    except NoResultFound:
        return make_response('Category not found.', 404)

    # Calculate item count for category retrieved above.
    item_count = db_session.query(func.count(CatalogItem.id).label('item_count')) \
        .filter_by(category_id=category.id) \
        .one() \
        .item_count

    return render_template('category.html',
                           STATE=get_signin_token(),
                           user=get_current_user_profile(),
                           category=category,
                           item_count=item_count,
                           category_summary=get_category_summary())


@app.route('/category/<int:category_id>/create_item', methods=['GET', 'POST'])
def create_item(category_id):
    insert_signin_state()

    # Check if user is logged in. If not, user is not authorized to create new items.
    if not session['logged_in']:
        return not_authorized()

    if request.method == 'GET':
        # If user is logged in and is trying to access the "create item" form,
        # insert CSRF token for validation when the form is POST'ed.
        insert_csrf_token()

        return render_template('create_item.html',
                               STATE=get_signin_token(),
                               csrf_token=get_csrf_token(),
                               user=get_current_user_profile(),
                               item=CatalogItem(),
                               category_id=category_id,
                               category_summary=get_category_summary())

    # Name, description, and category fields are required, so make sure they're
    # present before inserting any new items into the database.
    elif request.method == 'POST':

        # If code reaches this far, form data was valid. First thing is to check
        # the CSRF token to ensure that the user who requested the item creation
        # form is the user who is submitting the data.
        if request.form['csrf_token'] != get_csrf_token():
            return bad_csrf_token()

        if not request.form['name']:
            flash('Name field is required', 'error')
        if not request.form['description']:
            flash('Description field is required', 'error')
        if not request.form['category']:
            flash('Description field is required', 'error')

        # If there are any flashed messages, then the submitted form contained
        # invalid data. User will be presented with the form again, including
        # an explanation as to why the previously submitted form was rejected.
        if len(get_flashed_messages()) > 0:
            item = CatalogItem(name=request.form['name'],
                               description=request.form['description'])

            return render_template('create_item.html',
                                   STATE=get_signin_token(),
                                   csrf_token=get_csrf_token(),
                                   user=get_current_user_profile(),
                                   item=item,
                                   category_id=category_id,
                                   category_summary=get_category_summary())

        user = get_user(session['google_id'])

        new_item = CatalogItem(name=request.form['name'],
                               description=request.form['description'],
                               category_id=request.form['category'],
                               user_id=user.id)

        image_file = request.files['image_file']

        # First check to see if form data contains image data.
        if image_file:
            # ... then check to see if submitted image has valid extension.
            file_extension = image_file.filename.lower().rsplit('.', 1)[1]
            if file_extension not in ALLOWED_EXTENSIONS:
                flash('Only image files (extensions jpg, jpeg, png, gif) are '
                      'allowed for item images.', 'error')

                # If extension was invalid, redirect user back to item creation
                # form.
                return redirect(url_for('create_item', category_id=category_id))
            else:
                new_item.image_blob = image_file.read()

        db_session.add(new_item)
        db_session.commit()

        flash('"' + new_item.name + '" was successfully created!', 'success')

        # Item was accepted; redirect user to newly-created item's page.
        return redirect(url_for('view_item', category_id=category_id,
                                item_id=new_item.id))


@app.route('/view_item/<int:item_id>', methods=['GET'])
def view_item(item_id):
    insert_signin_state()

    try:
        item = db_session.query(CatalogItem).filter_by(id=item_id).one()
    except NoResultFound:
        return item_not_found()

    return render_template('view_item.html',
                           STATE=get_signin_token(),
                           user=get_current_user_profile(),
                           user_owns_item=user_owns_item(item_id),
                           item=item,
                           category_summary=get_category_summary())


@app.route('/edit_item/<int:item_id>', methods=['GET', 'POST'])
def edit_item(item_id):
    insert_signin_state()

    try:
        item = db_session.query(CatalogItem).filter_by(id=item_id).one()
    except NoResultFound:
        return item_not_found()

    # Check user ownership of item.
    if not user_owns_item(item.id):
        return not_authorized()

    if request.method == 'GET':
        # If user is requesting form, insert new CSRF token.
        insert_csrf_token()

        return render_template('edit_item.html',
                               STATE=get_signin_token(),
                               csrf_token=get_csrf_token(),
                               user=get_current_user_profile(),
                               user_owns_item=user_owns_item(item_id),
                               item=item,
                               category_summary=get_category_summary())

    if request.method == 'POST':

        # If code reaches this far, form data was valid. First thing is to check
        # the CSRF token to ensure that the user who requested the item creation
        # form is the user who is submitting the data.
        if session['csrf_token'] != get_csrf_token():
            return bad_csrf_token()

        item.name = request.form['name']
        item.description = request.form['description']
        item.category_id = request.form['category']

        # Name, description, and category fields are required, so make sure they're
        # present before inserting any new items into the database.
        if not item.name:
            flash('Name field is required', 'error')
        if not item.description:
            flash('Description field is required', 'error')
        if not item.category_id:
            flash('Description field is required', 'error')

        # If there are any flashed messages, then the submitted form contained
        # invalid data. User will be presented with the form again, including
        # an explanation as to why the previously submitted form was rejected.
        if len(get_flashed_messages()) > 0:
            return render_template('edit_item.html',
                                   STATE=get_signin_token(),
                                   csrf_token=get_csrf_token(),
                                   user=get_current_user_profile(),
                                   user_owns_item=user_owns_item(item_id),
                                   item=item,
                                   category_summary=get_category_summary())

        image_file = request.files['image_file']

        # First check to see if form data contains image data.
        if image_file:
            # ... then check to see if submitted image has valid extension.
            file_extension = image_file.filename.lower().rsplit('.', 1)[1]
            if file_extension not in ALLOWED_EXTENSIONS:
                flash('Only image files (extensions jpg, jpeg, png, gif) are '
                      'allowed for item images.', 'error')

                # If extension was invalid, redirect user back to item creation
                # form.
                return redirect(url_for('edit_item', item_id=item.id))
            else:
                item.image_blob = image_file.read()

        # Check to see if "Delete image" checkbox was checked.
        if request.form.get('delete_image', False):
            item.image_blob = None

        db_session.add(item)
        db_session.commit()

        # User edit form was accepted.
        flash('"' + item.name + '" was successfully updated!', 'success')
        return redirect(url_for('view_item', item_id=item_id))


@app.route('/delete_item/<int:item_id>', methods=['GET', 'POST'])
def delete_item(item_id):
    insert_signin_state()

    # Check user ownership of item.
    if not user_owns_item(item_id):
        return not_authorized()

    try:
        item = db_session.query(CatalogItem).filter_by(id=item_id).one()
    except NoResultFound:
        return item_not_found()

    if request.method == 'GET':
        # If user wants to delete item, insert new CSRF token.
        insert_csrf_token()

        return render_template('delete_item.html',
                               STATE=get_signin_token(),
                               csrf_token=get_csrf_token(),
                               user=get_current_user_profile(),
                               category_id=item.category_id,
                               item=item,
                               category_summary=get_category_summary())

    elif request.method == 'POST':
        # User is confirming item deletion, so check CSRF token
        if request.form['csrf_token'] != get_csrf_token():
            return bad_csrf_token()

        db_session.query(CatalogItem).filter_by(id=item.id).delete()
        db_session.commit()

        flash('"' + item.name + '" was successfully deleted!', 'success')

        # Token accepted, item deleted. Redirect user to category view.
        return redirect(url_for('show_category', category_id=item.category_id))


@app.route('/item_image/<int:item_id>')
def get_item_image(item_id):
    """Retrieve image for item with id item_id from database blob.

    Args:
        item_id: ID of item

    Returns:
        HTTP response containing item's image.
    """

    try:
        item = db_session.query(CatalogItem).filter_by(id=item_id).one()
    except NoResultFound:
        return item_not_found()

    return send_file(io.BytesIO(item.image_blob))


@app.route('/gconnect', methods=['POST'])
def gconnect():
    """Goes through the process of authorizing web application to make requests from
    Google on user's behalf using OAuth2; enables application to access basic user
    profile information, such as e-mail, username, Google ID, and picture.

    For more information, see:
    https://developers.google.com/identity/protocols/OAuth2WebServer
    """

    if request.args.get('state') != session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'

        return response

    code = request.data

    try:
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(json.dumps('Failed to upgrade authorization code.'),
                                 401)
        response.headers['Content-Type'] = 'application/json'

        return response

    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])

    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'

        return response

    gplus_id = credentials.id_token['sub']
    session['access_token'] = credentials.access_token
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'

        return response

    if result['issued_to'] != CLIENT_ID:
        response = make_response(json.dumps("Token's client ID doesn't match app's."),
                                 401)
        response.headers['Content-Type'] = 'application/json'

        return response

    stored_gplus_id = session.get('gplus_id')

    if gplus_id == stored_gplus_id:
        response = make_response(json.dumps("User is already connected."), 200)
        response.headers['Content-Type'] = 'application/json'

        return response

    session['gplus_id'] = gplus_id

    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    session['username'] = data['name']
    session['picture'] = data['picture']
    session['email'] = data['email']
    session['google_id'] = data['id']
    session['logged_in'] = True

    if not get_user(session['gplus_id']):
        create_user(session)

    return "Logged in as {0}".format(session.get('username'))


def gdisconnect():
    """Logs out of user's Google account; revokes permission to make requests
    on user's behalf.
    """
    if not session.get('access_token'):
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'

        return response

    access_token = session['access_token']
    url = 'https://accounts.google.com/o/oauth2/revoke?token={0}'.format(access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] != '200':
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.'), 400)
        response.headers['Content-Type'] = 'application/json'

        return response


@app.route('/logout')
def logout():
    """Log out of Google, delete associated session keys.
    """
    gdisconnect()

    del session['access_token']
    del session['username']
    del session['picture']
    del session['gplus_id']
    del session['email']
    del session['google_id']

    session['logged_in'] = False

    return redirect(url_for('show_categories'))


# Application startup
if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.json_encoder = CatalogJSONEncoder
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
