# Catalog App

Small app that displays categories and items within those categories. Users who are logged in can create, edit, and delete items they've created. Both logged-in users and non-logged-in users can view items created by others.

## Table of Contents
- [What's Included](#Whats_Included_12)
- [Requirements](#Requirements_25)
- [Seeding the Database](#Seeding_the_Database_30)
- [Application Configuration](#Application_Configuration_38)
- [Running the Application](#Running_the_Application_43)
- [Thanks](#Thanks_50)

## What's Included
- `application.py` - Main application
- `catalog_helpers.py` - Assorted commonly-used functions for use with `application.py`
- `client_secrets.json` - File containing application keys for use with Google sign-in. This file will need to be edited or replaced before the application can be run properly (see [Application Configuration](#Application_Configuration_38)).
- `database_setup.py` - Schema configuration for SqlAlchemy.
- `requirements.txt` - List of requirements needed to run this application (see [Requirements](#Requirements_25)).
- `seed_categories.py` - Creates database and seeds it with categories.
- `user_profile.py` - Data container class making it easier to pass user profile information from application code to views.
- `/static/` - Contains just one file, `styles.css`, which contains a handful of CSS class definitions for tweaking the application's appearance.
- `/templates/` - Contains various templates for application views. File names are self-explanatory.

## Requirements
To install the dependencies needed to run this project, type the following in a console window:

`pip install -r requirements.txt`

## Seeding the Database

To seed the database with categories, type the following into a console window:

`python seed_categories.py`

This will also create a file `catalog.db` in the application directory. You can reset the database with the command line `rm catalog.db` and then re-seeding.

## Application Configuration
Before running the application, you should replace the `json_secrets.json` file in the application's root directory with one obtained from Google for your own application. You can create a new application and obtain new secrets from the [Google Developers Console](https://console.developers.google.com/project).

You'll also need to change application's secret key. You can do this by opening `application.py` and changing the `app` object's `secret_key` attribute at the end of the file.

## Running the Application
Finally, to run the application, type the following in a console window:

`python application.py`

Open a browser and point it to `http://localhost:5000`.

## Thanks
Thanks for checking out my application. Enjoy.