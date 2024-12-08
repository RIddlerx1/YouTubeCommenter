import os
import pickle
import asyncio
import random
from datetime import datetime, timedelta, UTC
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import langdetect
import logging
import re
from concurrent.futures import ThreadPoolExecutor

SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
MAX_CONCURRENT_REQUESTS = 3
RESOURCES_DIR = 'resources'

class QuotaManager:
    def __init__(self):
        self.client_secrets = [
            os.path.join(RESOURCES_DIR, f) 
            for f in os.listdir(RESOURCES_DIR) 
            if f.startswith('client_secret_') and f.endswith('.json')
        ]
        self.current_index = 0
        self.services = []
        self._executor = ThreadPoolExecutor(max_workers=len(self.client_secrets))

    async def initialize(self):
        for client_secret in self.client_secrets:
            try:
                creds = await self._get_credentials(client_secret)
                service = build('youtube', 'v3', credentials=creds)
                self.services.append(service)
                logging.info(f"Initialized service for {client_secret}")
            except Exception as e:
                logging.error(f"Failed to initialize {client_secret}: {e}")
                continue

    async def _get_credentials(self, client_secret):
        token_file = os.path.join(RESOURCES_DIR, f'token_{os.path.basename(client_secret)}.pickle')
        creds = None
        try:
            if os.path.exists(token_file):
                with open(token_file, 'rb') as token:
                    creds = pickle.load(token)
            
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(client_secret, SCOPES)
                    creds = flow.run_local_server(port=0)
                with open(token_file, 'wb') as token:
                    pickle.dump(creds, token)
            return creds
        except Exception as e:
            logging.error(f"Credentials error for {client_secret}: {e}")
            raise

    def switch_service(self):
        if not self.services:
            raise RuntimeError("No services available")
        self.current_index = (self.current_index + 1) % len(self.services)
        logging.info(f"Switching to service {self.current_index}")
        return self.services[self.current_index]

    def get_current_service(self):
        if not self.services:
            raise RuntimeError("No services available")
        return self.services[self.current_index]

class YouTubeCommenter:
    _commented_videos = set()

    def __init__(self, quota_manager, comments_file):
        self.quota_manager = quota_manager
        self.comments = self.load_comments(os.path.join(RESOURCES_DIR, comments_file))
        self.comment_index = 0
        self.CATEGORY_IDS = {'22': 'People & Blogs', '24': 'Entertainment', '20': 'Gaming'}

    def load_comments(self, filename):
        with open(filename, 'r') as f:
            return [line.strip() for line in f if line.strip()]

    async def execute_with_quota(self, action, *args):
        max_retries = len(self.quota_manager.services)
        for _ in range(max_retries):
            try:
                service = self.quota_manager.get_current_service()
                return await action(service, *args)
            except HttpError as e:
                if e.resp.status == 403 and "quotaExceeded" in str(e):
                    logging.warning("Quota exceeded, switching services")
                    self.quota_manager.switch_service()
                    continue
                raise
        raise Exception("All services exhausted")

    async def is_valid_video(self, video_id):
        try:
            async def check_video(service, vid):
                request = service.videos().list(
                    part='contentDetails,snippet,status',
                    id=vid
                )
                response = await asyncio.to_thread(request.execute)
                return response
            
            response = await self.execute_with_quota(check_video, video_id)
            if not response.get('items'):
                return False
                
            video_details = response['items'][0]
            content_details = video_details['contentDetails']
            
            duration = content_details.get('duration', '')
            dimension = content_details.get('dimension', '')
            definition = content_details.get('definition', '')
            
            total_seconds = self.get_duration_seconds(duration)
            
            if total_seconds < 60:
                logging.info(f"Skipping short video {video_id} ({total_seconds}s)")
                return False
            
            if dimension != '2d' or definition != 'hd':
                logging.info(f"Skipping non-HD video {video_id}")
                return False
                
            return True
        except Exception as e:
            logging.error(f"Error checking video format: {str(e)}")
            return False

    def get_duration_seconds(self, duration):
        match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
        if match:
            hours = int(match.group(1) or 0)
            minutes = int(match.group(2) or 0)
            seconds = int(match.group(3) or 0)
            return hours * 3600 + minutes * 60 + seconds
        return 0

    async def get_recent_videos(self, category_id):
        await asyncio.sleep(random.uniform(3, 7))
        time_threshold = datetime.now(UTC) - timedelta(minutes=5)
        
        async def fetch_videos(service, cat_id):
            request = service.search().list(
                part='snippet',
                type='video',
                videoCategoryId=cat_id,
                relevanceLanguage='en',
                publishedAfter=time_threshold.isoformat().replace('+00:00', 'Z'),
                maxResults=50,
                order='date'
            )
            return await asyncio.to_thread(request.execute)

        try:
            response = await self.execute_with_quota(fetch_videos, category_id)
            valid_videos = []
            
            for item in response.get('items', []):
                await asyncio.sleep(random.uniform(1, 3))
                video_id = item['id']['videoId']
                if await self.is_valid_video(video_id):
                    valid_videos.append({
                        'id': video_id,
                        'title': item['snippet']['title'],
                        'description': item['snippet']['description']
                    })
            return valid_videos
        except Exception as e:
            logging.error(f"Video fetch error: {str(e)}")
            return []

    def is_english_content(self, title, description):
        try:
            return langdetect.detect(f"{title} {description}") == 'en'
        except:
            return False

    async def post_comment(self, video_id):
        if video_id in self._commented_videos:
            return False
        
        await asyncio.sleep(random.uniform(15, 30))
        
        async def post(service, vid):
            comment = self.comments[self.comment_index]
            self.comment_index = (self.comment_index + 1) % len(self.comments)
            
            request = service.commentThreads().insert(
                part='snippet',
                body={
                    'snippet': {
                        'videoId': vid,
                        'topLevelComment': {
                            'snippet': {'textOriginal': comment}
                        }
                    }
                }
            )
            return await asyncio.to_thread(request.execute)

        max_retries = 3
        for retry in range(max_retries):
            try:
                await self.execute_with_quota(post, video_id)
                self._commented_videos.add(video_id)
                logging.info(f"Successfully commented on video {video_id}")
                return True
            except Exception as e:
                if retry == max_retries - 1:
                    logging.error(f"Failed to comment on {video_id} after {max_retries} attempts")
                await asyncio.sleep(random.uniform(30, 60))
        return False

    async def process_category(self, category_id):
        comments_posted = 0
        session_videos = set()
        
        while comments_posted < 10:
            try:
                while True:
                    videos = await self.get_recent_videos(category_id)
                    found_new = False
                    
                    for video in videos:
                        if comments_posted >= 10:
                            break
                            
                        video_id = video['id']
                        if (video_id not in self._commented_videos and 
                            video_id not in session_videos and 
                            self.is_english_content(video['title'], video['description'])):
                            
                            if await self.post_comment(video_id):
                                comments_posted += 1
                                found_new = True
                                session_videos.add(video_id)
                                logging.info(f"Category {category_id}: Posted comment {comments_posted}/10")
                                await asyncio.sleep(random.uniform(60, 180))
                    
                    if comments_posted >= 10:
                        break
                        
                    if not found_new:
                        logging.info(f"Category {category_id}: No new videos found, waiting...")
                        await asyncio.sleep(random.uniform(45, 90))
                    else:
                        await asyncio.sleep(random.uniform(30, 60))
                        
            except Exception as e:
                logging.error(f"Category {category_id} error: {str(e)}")
                await asyncio.sleep(random.uniform(30, 60))

async def main():
    try:
        quota_manager = QuotaManager()
        await quota_manager.initialize()
        
        bot = YouTubeCommenter(quota_manager, 'comments.txt')
        tasks = [bot.process_category(cat_id) for cat_id in bot.CATEGORY_IDS]
        await asyncio.gather(*tasks)
        
    except Exception as e:
        logging.error(f"Main error: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
