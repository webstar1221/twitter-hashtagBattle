## Battle of the hashtags (BoHT)
***

###### Tweet analysis application using hashtags in Twitter 
----------------

### Overview 

The goal of this app is to allow a user to create 'battles' between two hashtags and analyze the number of typos in tweets tagged with them. 

With the BoHT application, user can: 

- pull/post a tweet with photo/video through Twitter App. 
- create/read/update/delete a battle by specifying the start & end date times. 
- run the certain analysis actions on some typos set of tweets pulled from Twitter. 
- create an endpoint so that data flowing into his/her own SPA leverage some set of actions prior to defining the comparison factors. 

The final API endpoint is exposed to return the current result for a specific battle id/name/started_at/ended_at and winning hashtags, in JSON format. 


### Roadmap 

_Note: Version 1.0.0 & 1.0.1 is currently functional with a simple front-end UI. 
It enables to start a battle with two specific hashtags and result in winning one.
But Version 1.0.2 is still in progress for implementing the periodic tasks.

#### Version 1.0.0 

In this version, user is able to: 

- Capture @username via Twitter Login
- Contest/sweepstakes sign-up via Twitter
- Pull the last tweets and post new tweet including photo/video
- Tweet out a photo from a user (requires user's explicit contest) 
- Induce interests via friends & followers 

#### Version 1.0.1 

In this version, user is able to: 

- Filter a query of tweets by a specific hashtag
- Battle CRUD with some certain configuration (battle_id, started_at/ended_at, frequency scope, tweet length, etc...)
- Determine the winner by some specific comparison factors (i.e., number of typos)

#### Version 1.0.2

In this version, user is able to:

- Set up the periodic task in battle settings (i.e., time-line config: Next Monday ~ Friday)


### Requirements 
----------------

- python (2.7, 3.4, 3.5) 
- django (v1.8.13) 
- pyenchant (v1.6.6)
- python-social-auth (v0.2.19)
- python-twitter (v2.2)
- twython (v3.4.0)


### Setup 
----------------

#### Installation for REST API Server (run the application locally) 

In the version 1.0, BoHT's architecture will use these technologies, django + RDBMS + Twitter Authentication API. 

1. Initialize the Virtualenv 

    ```virtualenv venv```
    
2. Start the Virtualenv 

    ```source venv/bin/activate```
    
3. Install the package dependencies 

    ```pip install -r requirements.txt```
    
4. Twitter Auth Settings (config/settings.py) 

    _Note: In your Twitter Application Settings, you MUST set up the Callback URL to http://127.0.0.1:8000/complete/twitter 
    
    ```SOCIAL_AUTH_TWITTER_KEY = 'your app client id'```
    ```SOCIAL_AUTH_TWITTER_SECRET = 'your app client secret'```
    ```TWITTER_ACCESS_TOKEN  = 'your app access token'``` 
    ```TWITTER_ACCESS_TOKEN_SECRET  = 'your app access token secret'```
    
5. Migrate the database 

    ```python manage.py makemigrations && python manage.py migrate```
    
6. Create an administrator 

    ```python manage.py createsuperuser```
    
7. Run the application 

    ```python manage.py runserver```

#### Installation for live application (run on the Digital Ocean) 

In the version 2.0, BoHT application will run on the Ubuntu Server of Digital Ocean, and go to move the final version on the living server. 


