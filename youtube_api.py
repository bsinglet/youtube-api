__author__ = 'Benjamin M. Singleton'
__date__ = '13 June 2024'
__version__ = '0.1.1'

import os
import pandas as pd
from tqdm import tqdm
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = ['https://www.googleapis.com/auth/youtube']


def get_playlist_ids(youtube_service) -> list:
    # Get playlist ID for Watch Later
    playlist_ids = list()
    playlists_response = youtube_service.channels().list(part='contentDetails', mine=True).execute()
    print(playlists_response)
    playlist_ids.append(playlists_response['items'][0]['id'])

    # get the normal playlists
    playlists_response = youtube_service.playlists().list(part='contentDetails', mine=True).execute()
    while True:
        try:
            # print(f'Retrieved {len(playlists_response['items'])} of {playlists_response['pageInfo']['totalResults']}')
            # print(playlists_response)
            # Print out each playlist
            for playlist in playlists_response['items']:
                # print(f"Playlist: {playlist}")
                playlist_ids.append(playlist['id'])
            if 'nextPageToken' in playlists_response.keys():
                next_page_token = playlists_response['nextPageToken']
                playlists_response = youtube_service.playlists().list(part='contentDetails', mine=True, pageToken=next_page_token).execute()
            else:
                break
        except:
            break
    return playlist_ids


def get_playlist_details(youtube_service, id) -> dict:
    try:
        playlists_response = youtube_service.playlists().list(part='snippet', id=id).execute()
        details = playlists_response['items'][0]['snippet']
        return {'title': details['title'], 'description': details['description'], 'thumbnails': details['thumbnails']}
    except:
        print(f"Couldn't retrieve playlist details for ID {id}")
        return {}


def get_playlist_items(youtube_service, playlistId) -> list:
    playlist_items = list()
    try:
        playlists_response = youtube_service.playlistItems().list(part='snippet', playlistId=playlistId).execute()
    except:
        print(f"Failed to retrieve any of the videos for playlist ID {playlistId}")
        return list()
    while True:
        for playlist in playlists_response['items']:
            try:
                playlist_items.append({'id': playlist['id'], 'title': playlist['snippet']['title'], 'description': playlist['snippet']['description'], 'thumbnails': playlist['snippet']['thumbnails'], 'videoOwnerChannelTitle': playlist['snippet']['videoOwnerChannelTitle'], 'videoOwnerChannelId': playlist['snippet']['videoOwnerChannelId']})
            except:
                continue
        try:
            if 'nextPageToken' in playlists_response.keys():
                playlists_response = youtube_service.playlistItems().list(part='snippet', playlistId=playlistId, pageToken=playlists_response['nextPageToken']).execute()
            else:
                break
        except:
            break
    return playlist_items


def main():
    # Set up authentication credentials
    creds = None
    if os.path.exists('token.json'):
        creds = Request().load('token.json')
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
            """
            with open('token.json', 'w') as my_file:
                my_file.write(creds.to_json())
            """

    # Connect to the YouTube API
    youtube_service = build('youtube', 'v3', credentials=creds)
    
    # Get all playlists from the account
    playlist_ids = get_playlist_ids(youtube_service=youtube_service)
    #print(playlist_ids)

    # get all playlist details (title, description, thumbnail)
    playlist_details = list()
    for each_playlist_id in playlist_ids:
        playlist_details.append(get_playlist_details(youtube_service, each_playlist_id))
        # print(playlist_details[-1])
    playlist_details[0]['title'] = 'Watch Later'

    # get metadata of all playlist videos
    playlist_videos = list()
    for each_playlist_id in tqdm(playlist_ids):
        playlist_videos.append(get_playlist_items(youtube_service, each_playlist_id))

    
    # save all retrieved information to limit API usage
    df = pd.DataFrame(playlist_details)
    df.to_csv('playlist_details.csv')
    df.to_pickle('playlist_details.pkl')

    df = pd.DataFrame(playlist_videos)
    df.to_pickle('playlist_videos.pkl')

    for number, each_playlist in enumerate(playlist_videos):
        try:
            df = pd.DataFrame(each_playlist)
            df.to_csv(f'{playlist_details[number]['title']}.csv')
        except:
            continue


if __name__ == '__main__':
    main()
