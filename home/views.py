import json
import datetime

from battle import spellCheck
from django import forms
from django.shortcuts import *
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.contrib.auth import logout as auth_logout
from social.apps.django_app.default.models import UserSocialAuth
import twitter
from twitter import TwitterError
from twython import Twython
from home.models import Image



# QUERY_MAX_STATUSES = 3200
QUERY_MAX_STATUSES = 200

SIZE_5MB = 5 * 1024 * 1024


class ImageForm(forms.Form):
    file = forms.FileField()


def login(request):
    
    context = {"request": request}
    return render_to_response('login.html', context, context_instance=RequestContext(request))


@login_required
def home(request):
    
    context = {"request": request}
    return render_to_response('home.html', context, context_instance=RequestContext(request))


@login_required
def tweet(request):

    status = request.POST.get("status", None)
    
    api = get_twitter(request.user)
    response = None
    
    if status:
        response = api.PostUpdates(status)[0].AsDict()

    context = {'request': request, 'response': response, 'response_pretty': json.dumps(response)}
    return render_to_response('tweet.html', context, context_instance=RequestContext(request))


@login_required
def query(request):
    
    screen_name = request.POST.get("screen_name", None)
    if not screen_name:
        screen_name = request.user.username
    
    api = get_twitter(request.user)
        
    statuses = []  
    max_id = None   
    while True and QUERY_MAX_STATUSES > 0:
         
        # get latest page
        new_statuses = api.GetUserTimeline(screen_name=screen_name, count=15, max_id=max_id)

        # out of statuses: done
        if len(new_statuses) == 0:
            break
 
        max_id = min([s.id for s in new_statuses]) - 1
        statuses = statuses + new_statuses
         
        # reached max: done
        if len(statuses) >= QUERY_MAX_STATUSES:
            break

    context = {'request': request, 'statuses': statuses}
    return render_to_response('query.html', context, context_instance=RequestContext(request))


@login_required
def media_photo(request):

    return media(request, "photo", 'media_photo.html')


@login_required
def media_video(request):

    return media(request, "video", 'media_video.html')


@login_required
def media(request, type, template):
    
    log = Log()

    api = get_twitter(request.user)
    response = {}
    metadata = None
        
    status = request.POST.get("status", None)
    media_type = request.POST.get("media_type", None)
    media_category = request.POST.get("media_category", None)
    upload_url = '%s/media/upload.json' % api.upload_url

    form = ImageForm(request.POST, request.FILES)
    if form.is_valid():
        file = request.FILES['file']
        
        # save to file
        image = Image(file=file)
        image.save()

        # metadata of file        
        metadata = get_metadata(image.file.path) 
        
        media_id = None
        
        if type == "video":
            result = media_upload_chunked(api, upload_url, image, media_type, media_category, log=log)
            response["media"] = result.get("upload", None)
            media_id = result.get("media_id", None)
            
        else:
            result = media_upload(api, upload_url, image, media_type, log=log)
            response["media"] = result.get("upload", None)
            media_id = result.get("media_id", None)
        
        # this is wrong, based on photo vs. video
        if media_id:
            data = {'status': status, 'media_ids': [media_id]}
            url = '%s/statuses/update.json' % api.base_url
            log.append("%s request: %s" % (url, data))
            json_data = api._RequestUrl(url, 'POST', data=data)
            json_data = json_data.content
            log.append("%s response: %s" % (url, json_data))

            data = None        
            if not 'error' in json_data and not 'errors' in json_data:
                data = api._ParseAndCheckTwitter(json_data)

            response['tweet'] = data
            
        response["log"] = log.out()
            
    context = {'request': request, 'form': form, 'response': response, 'metadata': metadata}
    return render_to_response(template, context, context_instance=RequestContext(request))


def media_upload(api, upload_url, image, media_type=None, log=None):

    media_id = None
    data = {}
         
    contents = open(str(image.file.path), 'rb').read()

    # using 'media' parameter (binary)
    if media_type == "binary":  
        data['media'] = contents
        
    # using 'media_data' parameter (base64)
    else:                       
        import base64
        contents = base64.b64encode(contents)
        data['media_data'] = contents
        
    log.append("%s request: %s" % (upload_url, data))
        
    json_data = api._RequestUrl(upload_url, 'POST', data=data)
    json_data = json_data.content
    
    log.append("%s response: %s" % (upload_url, json_data))

    if not 'error' in json_data and not 'errors' in json_data:
        response = api._ParseAndCheckTwitter(json_data)
        media_id = response['media_id_string']

    result = {
        "media_id": media_id,
        "upload": json_data
    }
    
    return result


# chunked media upload always does base64 encoded uploads    
def media_upload_chunked(api, upload_url, image, media_type=None, media_category=None, log=None):

    import base64

    #ffprobe check (TODO: Add this to return or only use in standalone tool?)
    #video_info = ffprobe(image.file.path)
    #print json.dumps(video_info, indent=4)

    contents = open(str(image.file.path), 'rb').read()
    contents = base64.b64encode(contents)

    chunks = chunkify(contents, SIZE_5MB) 
        
    # INIT
    data = {
        "command": "INIT", 
        "media_type": "video/mp4", 
        "total_bytes": image.file.size
    }
    
    if media_category:
        data["media_category"] = media_category
        
    log.append("%s INIT request: %s" % (upload_url, data))
    
    json_data = api._RequestUrl(upload_url, 'POST', data=data)
    json_data = json.loads(json_data.content)
    media_id = json_data.get("media_id_string", None)
    
    log.append("%s INIT response: %s" % (upload_url, json_data))

    if media_id:
        # APPEND
        count = 0 
        for c in chunks:
            data = {
                "command": "APPEND",
                "media_id": media_id,
                "segment_index": count,
                "media_data": c
            }
            
            log.append("%s APPEND request: segment %s" % (upload_url, count))

            try:
                json_data = api._RequestUrl(upload_url, 'POST', data=data)
                count = count + 1
                log.append("%s APPEND response: %s" % (upload_url, json_data))
                
            except TwitterError as e:
                        
                media_id = None
                json_data = e.args
                break

    if media_id:
        # FINALIZE
        data = {
            "command": "FINALIZE", 
            "media_id" : media_id
        }
        
        log.append("%s FINALIZE request: %s" % (upload_url, media_id))
        
        json_data = api._RequestUrl(upload_url, 'POST', data=data)
        if json_data.status_code == 400:
            media_id = None

        json_data = json.loads(json_data.content)
        log.append("%s FINALIZE response: %s" % (upload_url, json_data))
        processing_info = json_data.get('processing_info', None)
        
        while processing_info and processing_info.get('state', None) == 'pending':
            check_after_secs = processing_info.get('check_after_secs', None)
                
            import time
            time.sleep(check_after_secs)
                
            # STATUS
            data = {
                "command": "STATUS", 
                "media_id" : media_id
            }

            log.append("%s STATUS request: %s" % (upload_url, data))
            
            json_data = api._RequestUrl(upload_url, 'GET', data=data)
            json_data = json.loads(json_data.content)

            log.append("%s STATUS response: %s" % (upload_url, json_data))

            processing_info = json_data.get('processing_info', None)
                          
    result = {
        "media_id": media_id,
        "upload": json_data,
        "log": log.out()
    }
    return result


@login_required
def media_inspector(request):

    video_info = {}
    video_metadata = None
    ffprobe_exists = True

    if which('ffprobe') == None:
        ffprobe_exists = False
    # TODO: use this flag in view to add instructions to install ffprobe

    form = ImageForm(request.POST, request.FILES)
    if form.is_valid():
        file = request.FILES['file']
        
        # save to file
        image = Image(file = file)
        image.save()

        # metadata of file        
        #video_metadata = get_metadata(image.file.path) 
        #print video_metadata

        # ffprobe
        if ffprobe_exists:
            video_info = ffprobe(image.file.path)
            print json.dumps(video_info, indent=4)
            
            # Add warning checks
            if video_info.get('streams', None):
                for stream in video_info['streams']:
                    if stream.get('codec_type', None) == "audio":
                        stream['channel_layout_warning'] = (stream.get('channel_layout', None) in ["mono","stereo"])

    context = {'request': request, 'form': form, 'video_info': video_info, 'video_info_pretty': json.dumps(video_info), 'video_metadata': video_metadata, 'ffprobe_exists': ffprobe_exists }
    return render_to_response('media_inspector.html', context, context_instance=RequestContext(request))


# used check if ffprobe exists
def which(program):
    import os

    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    # short-circuit on heroku 
    FFPROBE_HEROKU = '/app/.heroku/vendor/ffmpeg/bin/ffprobe'
    if is_exe(FFPROBE_HEROKU):
        return FFPROBE_HEROKU

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file
            
    return None


def ffprobe(file_path):
    import os
    import subprocess

    if file_path is None:
        return json.loads("{ 'error': 'no file path'}")

    # check if ffprobe exists
    ffprobe_path = which('ffprobe')
    if ffprobe_path == None:
        return json.loads("{ 'error': 'ffprobe not installed'}")

    # check if input file exists
    if not os.path.isfile(file_path):
        return json.loads("{ 'error': 'input file does not exist'}")

    # run ffprobe and get output
    p = subprocess.Popen([ffprobe_path, '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', file_path ],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    out, err = p.communicate()
    if err:
        return json.loads("{ 'error': '%s'}" % err)

    # read output and get the packets info
    return json.loads(out)


@login_required
def profile(request):
    
    api = get_twitter(request.user)
    response = None
        
    form = ImageForm(request.POST, request.FILES)
    if form.is_valid():
        file = request.FILES['file']
        
        # save to file
        image = Image(file=file)
        image.save()
        
        response = api.UpdateImage(image.file.path)
        
    context = {'request': request, 'form': form, 'response': response}
    return render_to_response('profile.html', context, context_instance=RequestContext(request))


def logout(request):
    
    """Logs out user"""
    auth_logout(request)
    return HttpResponseRedirect('/')


def get_twython(user):

    consumer_key = settings.SOCIAL_AUTH_TWITTER_KEY
    consumer_secret = settings.SOCIAL_AUTH_TWITTER_SECRET
    access_token_key = settings.TWITTER_ACCESS_TOKEN
    access_token_secret = settings.TWITTER_ACCESS_TOKEN_SECRET

    usa = UserSocialAuth.objects.get(user=user, provider='twitter')
    if usa:
        access_token = usa.extra_data['access_token']
        if access_token:
            access_token_key = access_token['oauth_token']
            access_token_secret = access_token['oauth_token_secret']

    if not access_token_key or not access_token_secret:
        raise Exception('No user for twitter API call')

    api = Twython(
        app_key=consumer_key,
        app_secret=consumer_secret,
        oauth_token=access_token_key,
        oauth_token_secret=access_token_secret)

    return api


def get_twitter(user):

    consumer_key = settings.SOCIAL_AUTH_TWITTER_KEY  
    consumer_secret = settings.SOCIAL_AUTH_TWITTER_SECRET 
    access_token_key = settings.TWITTER_ACCESS_TOKEN 
    access_token_secret = settings.TWITTER_ACCESS_TOKEN_SECRET 

    usa = UserSocialAuth.objects.get(user=user, provider='twitter')
    if usa:
        access_token = usa.extra_data['access_token']
        if access_token:
            access_token_key = access_token['oauth_token']
            access_token_secret = access_token['oauth_token_secret']

    if not access_token_key or not access_token_secret:
        raise Exception('No user for twitter API call')

    api = twitter.Api(
        base_url='https://api.twitter.com/1.1',
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        access_token_key=access_token_key,
        access_token_secret=access_token_secret)

    return api


def get_metadata(filename):
    
    from hachoir_core.error import HachoirError
    from hachoir_parser import createParser
    from hachoir_metadata import extractMetadata

    #     filename, realname = unicodeFilename(filename), filename
    parser = createParser(filename, filename)
    if not parser:
        return "Unable to parse file"
    
    try:
        metadata = extractMetadata(parser)
    except HachoirError, err:
        return "Metadata extraction error: %s" % unicode(err)
    
    if not metadata:
        return "Unable to extract metadata"
    
    text = metadata.exportPlaintext()
    return text


def chunkify(l, n):
    n = max(1, n)
    return [l[i:i + n] for i in range(0, len(l), n)]


class Log():
    
    y = ""
    
    def append(self, x):
        self.y = self.y + "\n" + x
        if settings.DEBUG:
            print x
        
    def out(self):
        return self.y