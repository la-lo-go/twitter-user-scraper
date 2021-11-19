# Twitter User Scraper
This script will help you to create security copies on MEGA of the follows and followers of the twitter accounts you want. Also, the copies are compared to know if there has been any change and know if it was an unfollow, [*soft block*](https://www.urbandictionary.com/define.php?term=Soft%20Block) or if the account is suspended.

## Prerequisites

 1. Python 3+.
 2. A [Twitter developer account](https://developer.twitter.com/en).
 3. A [MEGA](https://mega.nz/) account.


## Steps

1. Clone (or download) the repository:
```
git clone https://github.com/la-lo-go/twitter-user-scraper
```
2. Install the APIs packages:
``` bash
python -m pip install -r requirements.txt
```
3. In key.py complete the APIs variables:

 - From the Twitter API: `consumer_key` [API Key], `consumer_secret` [API Secret Key], `access_token` y `access_token_secret`.
 - From the MEGA API: `mega_email` y `mega_password`.

4. Run the twUserScaper.py file.


## How to use the program
After you start the application yo will see a menu with these options:

 1. Update or create the followers backup.
 2. Update or create the follows backup.
 3. Update and create the followers and follows backup.
 4. Download locally all the files from a user.

Next you have to enter the user names of the people you want to get the backup and get the resume. You can enter as many user names as you like (separated by spaces), all the resumes will be shown at the end.

## Cloud storage

This program uses the [Mega.py](https://pypi.org/project/mega.py/) API to store the backups of the users on a MEGA account in separated folders labled by the user ID.

## About the database

The script uses a SQLite3 database to store the IDs and names to look up to the users that have already been copied so it can run way more faster and don't excced the API limit (900 users lookups per 15 minutes). If is not in the database it stores it.

The use of SQLite makes it easier to make security copies.

### IDs_database.db/usuarios scheme:

| id |  name  |  url  |
|:--:|:------:|:-----:|
| key of the database and unique for each account| @ of the user  (variable to future changes) | direct url to the user profile |


## License
[Mozilla Public License 2.0](https://www.mozilla.org/en-US/MPL/2.0/)

[![License: MPL 2.0](https://img.shields.io/badge/License-MPL_2.0-brightgreen.svg)](https://www.mozilla.org/en-US/MPL/2.0/)

