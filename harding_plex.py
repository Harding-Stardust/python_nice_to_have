#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''

Helper functions to work with a Plex Media Server via Python

https://github.com/pkkid/python-plexapi
https://pypi.org/project/PlexAPI/
https://github.com/pkkid/python-plexapi
https://python-plexapi.readthedocs.io/en/latest/modules/library.html#

'''

__version__ = 230408011247
__author__ = "Harding"
__description__ = __doc__
__copyright__ = "Copyright 2023"
__credits__ = ["Other projects"]
__license__ = "GPL"
__maintainer__ = "Harding"
__email__ = "not.at.the.moment@example.com"
__status__ = "Development"


__path_to_vlc__ = r"C:\Program Files\VideoLAN\VLC\vlc.exe"
__PLEX_USERNAME = '< PLEXUSERNAME >' 
__PLEX_PASSWORD = '<PLEX PASSWORD >'

import os
import argparse
from typing import Union, List, Dict, Set, Tuple
import pathlib
import harding_utils as hu
import plexapi.myplex # pip install plexapi

g_account = None

def account(arg_force_reconnect: bool = False) -> plexapi.myplex.MyPlexAccount:
    global g_account

    if arg_force_reconnect:
        g_account = None

    if not g_account:
        g_account = plexapi.myplex.MyPlexAccount(username=__PLEX_USERNAME, password=__PLEX_PASSWORD)
    return g_account

def _resource(arg_name_or_client_id: str) -> plexapi.myplex.MyPlexResource:
    """ Internal function, please use server() instead.

    Get the info needed to connect to the resource """

    _account = account()
    for r in _account.resources():
        if r.clientIdentifier.lower() in arg_name_or_client_id.lower() or arg_name_or_client_id.lower() in r.name.lower():
            return r
    return None

def server(arg_plex_resource: Union[plexapi.myplex.MyPlexResource, str]) -> plexapi.server.PlexServer:
    """ Connect to a Plex server """

    arg_plex_resource = _resource(arg_plex_resource) if isinstance(arg_plex_resource, str) else arg_plex_resource

    if not isinstance(arg_plex_resource, plexapi.myplex.MyPlexResource):
        print('Invalid argument, arg_plex_resource must be either str or plexapi.myplex.MyPlexResource')
        return None

    if not arg_plex_resource.clientIdentifier == '<LOCAL SERVER ID>': # My local server
        while arg_plex_resource.connections[0].uri[0:11] in ['https://172', 'https://192']: # Never try to connect to the LAN IP on other Plex servers
            del arg_plex_resource.connections[0]

    return arg_plex_resource.connect()

def play_in_vlc(arg_plex_path: str) -> str:
    return download_from_plex(arg_plex_path=arg_plex_path, arg_virtual_file_system=False, arg_start_vlc=True)

def download_from_plex(arg_plex_path: Union[plexapi.base.Playable, str], 
                       arg_virtual_file_system: bool = False, 
                       arg_start_vlc: bool = False, 
                       arg_download_poster: bool = False) -> str:
    ''' Enter a URL to a plex video and this function downloads the subs and the video
    '''
    if not arg_plex_path:
        return None

    _video = video(arg_plex_path) if isinstance(arg_plex_path, str) else arg_plex_path
    if not isinstance(_video, plexapi.base.Playable):
        hu.error_print(f"Cannot handle {type(_video)}")
        return None

    video_filename = filename_on_server(_video, arg_only_basename=True, arg_safe_local_filename=True)

    downloaded_subs = []
    for sub in _video.subtitleStreams():
        if not sub.key:
            continue
        sub_full_url = https_url(sub)
        sub_local_name = f"{os.path.splitext(video_filename)[0]}.{sub.languageCode}.{sub.codec}"
        downloaded_subs.append(hu.download_file(arg_url=sub_full_url, arg_local_filename=sub_local_name))

    video_url = https_url(_video)

    if arg_start_vlc:
        vlc_command = f'"{__path_to_vlc__}" "{video_url}"'
        if downloaded_subs:
            vlc_command += f' --no-sub-autodetect-file --sub-file "{downloaded_subs[0]}"'
        hu.timestamped_print(f"\n\nStarting VLC: {vlc_command}\n\n")
        os.system('"' + vlc_command + '"')

        for sub in downloaded_subs:
            os.remove(sub)

        return vlc_command

    if arg_download_poster:
        hu.download_file(_video.thumbUrl, arg_local_filename=os.path.splitext(video_filename)[0] + ".jpg")

    if arg_virtual_file_system:
        with open(video_filename, 'w', encoding='utf-8', newline='\n') as f:
            f.write(f'HVFS\n{video_url}')
    else:
        hu.download_file(video_url, arg_local_filename=video_filename)
    return video_filename

def users_can_download(arg_allowed_download: bool = True):
    ''' Set the 'allow download' on all users '''
    _account = account()
    _server = server('Ymer')
    for user in _account.users():
        hu.timestamped_print(f"Checking user: {user.email}", arg_force_flush=True)
        _account.updateFriend(user, _server, allowSync=arg_allowed_download)

def list_users():
    _account = account()

    users = {}
    for user in _account.users():
        if not user.email:
            continue
        user.real_name = ' '
        user.notes = ' '
        if user.id == 123456:
            user.real_name = 'Johnny'
            user.notes = 'My sisters friend'
        users[user.id] = user

    users = hu.dict_sort(users)

    print(f'{"Username:":20s}{"Real name":30s}{"Email:":40s}{"user_id:":55s}{"Notes:"}')
    for user in users.values():
        print(f'{user.username:20s}{user.real_name:30s}{user.email:40s}http://<PLEXPY URL>/user?user_id={str(user.id):12s}{user.notes}')
    print("To remove users: https://app.plex.tv/desktop/#!/settings/manage-library-access")

def sections(arg_plex_server: Union[plexapi.server.PlexServer, str]) -> Dict[str, plexapi.library.LibrarySection]:
    ''' Sections are what the use see on the left side ('Movies', 'Shows' and so on)

        returns a dict that looks like: result['Movies']: <MovieSection:8:Movies>,
    '''

    _server = server(arg_plex_server) if isinstance(arg_plex_server, str) else arg_plex_server

    if not isinstance(_server, plexapi.server.PlexServer):
        hu.error_print('Invalid argument, arg_plex_server must be either str or plexapi.server.PlexServer')
        return None
    res = {}
    for section in _server.library.sections():
        res[section.title] = section

    return res

def https_url(arg_video: plexapi.video.Video, arg_index_if_multiple: int = 0) -> str:
    ''' Get the URL that is used to download a movie/episode/clip from something that identify a video '''

    _server = arg_video._server # This special member seems to exist on all of the given objects we can handle

    # Subtitle
    if isinstance(arg_video, plexapi.media.SubtitleStream):
        subtitle = arg_video
        return _server.url(subtitle.key, includeToken=True)

    # Poster / art
    if isinstance(arg_video, plexapi.media.Poster):
        poster = arg_video
        return _server.url(poster.key, includeToken=True)

    # Video
    part = None
    if isinstance(arg_video, plexapi.media.MediaPart):
        part = arg_video
    elif isinstance(arg_video, plexapi.media.Media):
        part = arg_video.parts[0]
    elif isinstance(arg_video, plexapi.base.Playable):
        part = arg_video.media[arg_index_if_multiple].parts[0]
    else:
        hu.error_print(f"No support for {type(arg_video)} yet!")
        return None

    res = _server.url(part._details_key, includeToken=True) + '&download=0' # We add the download=0 cause if the server is configured to not allow downloads, this will will work anyway
    return res

def HVFS_full_server_clone(arg_plex_server: Union[plexapi.server.PlexServer, str], arg_dest_dir: str, arg_ignore: list = None) -> bool:
    if not arg_ignore:
        arg_ignore = ["4K", "Anime", "Fitness", "Foreign", "Audiobooks"]

    for section_name, section in sections(arg_plex_server).items():
        for ignore_word in arg_ignore:
            if ignore_word.lower() in section_name.lower().strip():
                hu.timestamped_print(f"Ignoring {section_name}")
                continue

        if section.type == 'show':
            for _show in section.all():
                for season in _show.seasons():
                    for episode in season.episodes():
                        full_path = os.path.join(arg_dest_dir,
                                                 hu.smart_filesystem_safe_path(section.title),
                                                 hu.smart_filesystem_safe_path(_show.title),
                                                 f"S{season.seasonNumber:02d}",
                                                 filename_on_server(episode, arg_only_basename=True, arg_safe_local_filename=True))

                        if len(full_path) > 259:
                            ext = os.path.splitext(episode.media[0].parts[0].file)[1]
                            full_path = os.path.join(arg_dest_dir,
                                                     hu.smart_filesystem_safe_path(section.title),
                                                     hu.smart_filesystem_safe_path(_show.title), f"S{season.seasonNumber:02d}",
                                                     filename_on_server(episode, arg_only_basename=True, arg_safe_local_filename=True)[0:100] + ext)

                        hu.ensure_dir(full_path)
                        hu.text_write_whole_file(full_path, f"HVFS\n{https_url(episode)}")

        elif section.type == 'movie':
            for _movie in section.all():
                full_path = os.path.join(arg_dest_dir,
                                         hu.smart_filesystem_safe_path(section.title),
                                         hu.smart_filesystem_safe_path(_movie.title),
                                         filename_on_server(_movie, arg_only_basename=True, arg_safe_local_filename=True))

                if len(full_path) > 259:
                    full_path = os.path.join(arg_dest_dir,
                                             hu.smart_filesystem_safe_path(section.title),
                                             hu.smart_filesystem_safe_path(_movie.title[50]),
                                             filename_on_server(_movie, arg_only_basename=True, arg_safe_local_filename=True))

                if len(full_path) > 259:
                    ext = os.path.splitext(_movie.media[0].parts[0].file)[1]
                    full_path = os.path.join(arg_dest_dir,
                                             hu.smart_filesystem_safe_path(section.title),
                                             hu.smart_filesystem_safe_path(_movie.title[50]),
                                             filename_on_server(_movie, arg_only_basename=True, arg_safe_local_filename=True)[0:50] + ext)

                hu.ensure_dir(full_path)
                hu.text_write_whole_file(full_path, f"HVFS\n{https_url(movie)}")

def video(arg_plex_url: str) -> plexapi.video.Video:
    ''' Take in an Plex URL that can identify a video and return the Video object '''
    video_id = int(hu.regexp_findall_quick_fix(r"metadata%2F(\d+)", arg_plex_url, ['video id not found'])[0])
    _server = server(arg_plex_url)
    res = _server.fetchItem(video_id)
    return res

def filename_on_server(arg_video: Union[plexapi.base.Playable, str],
                       arg_index_if_multiple: int = 0,
                       arg_only_basename: bool = False,
                       arg_safe_local_filename: bool = False) -> str:
    ''' Return the full file path on the SERVER for the video '''

    if isinstance(arg_video, str):
        arg_video = video(arg_video)
    if not isinstance(arg_video, plexapi.base.Playable):
        hu.error_print(f"Invalid type. You gave me {type(arg_video)} but I only know how to handle str or plexapi.base.Playable")
        return None
    res = arg_video.media[arg_index_if_multiple].parts[0].file
    if arg_only_basename:
        res = os.path.basename(res)
    if arg_safe_local_filename:
        res = hu.smart_filesystem_safe_path(res)
    return res

def download_season(arg_plex_server: str, arg_show_name: str, arg_seasons: Union[str, List, Set, Tuple, None], arg_dest_dir: str) -> bool:
    arg_seasons = hu.list_from_str(arg_seasons)

    for section in sections(arg_plex_server).values():
        if section.type == 'show':
            for _show in section.all():
                if _show.title.lower() == arg_show_name.lower():
                    print(f"Found the show named '{arg_show_name}'")
                    for season in _show.seasons():
                        print(f"Season named '{season.title}' found")
                        if str(season.seasonNumber) in arg_seasons or season.seasonNumber in arg_seasons:
                            print(f"Season named '{season.title}' matched in {arg_seasons}")
                            for episode in season.episodes():
                                print(f"Found episode '{episode.title}' and starting to download that")
                                # plex_url = episode._server.url(episode.media[0].parts[0]._details_key, includeToken=True) + '&download=0'
                                plex_url = https_url(episode)
                                full_path = os.path.join(arg_dest_dir, 
                                                         hu.smart_filesystem_safe_path(section.title), 
                                                         hu.smart_filesystem_safe_path(_show.title), f"S{season.seasonNumber:02d}", 
                                                         hu.smart_filesystem_safe_path(os.path.basename(episode.media[0].parts[0].file)))

                                if len(full_path) > 259:
                                    ext = os.path.splitext(episode.media[0].parts[0].file)[1]
                                    full_path = os.path.join(arg_dest_dir, hu.smart_filesystem_safe_path(section.title), 
                                                             hu.smart_filesystem_safe_path(_show.title), 
                                                             f"S{season.seasonNumber:02d}", 
                                                             hu.smart_filesystem_safe_path(os.path.basename(episode.media[0].parts[0].file[0:100] + ext)))


                                hu.ensure_dir(full_path)
                                hu.timestamped_print(f"Downloading: {plex_url}")
                                hu.timestamped_print(f"Saving as: {full_path}")

                                hu.download_file(plex_url, arg_local_filename=full_path) # TODO: Call download_from_plex() instead?
                    return True


    return False

def scan_library_files(arg_section: plexapi.library.LibrarySection) -> bool:
    ''' Same as clicking a library and selecting Scan Library Files in the Plex webgui '''
    arg_section.update()
    return True

def kill_plex():
    ''' Kills everything that has to do with Plex. Plex hangs sometimes on scans. '''
    os.system('taskkill /f /im "Plex Media Server.exe"')
    os.system('taskkill /f /im "PlexScriptHost.exe"')
    os.system('taskkill /f /im "Plex Media Scanner.exe"')

# def restart_plex():
    # ''' Kills everything that has to do with Plex (calling kill_plex() ) and then restarts the main binary "Plex Media Server.exe" '''
    # kill_plex()
    # os.system(r'"C:\Program Files (x86)\Plex\Plex Media Server\Plex Media Server.exe"')

def summary_set_from_file(arg_video: Union[plexapi.video.Video, plexapi.video.Show, str]) -> bool:
    ''' Given a Video, check if there is a file named: <videoname>.summary.txt next to it
    For a show, there must be a file named summary.txt in the root of the show
    For a season, there must be a file named summary.txt in the root of the season

    If I find any summary file, I read the content and set it to the file
    '''
    if isinstance(arg_video, str):
        arg_video = video(arg_video)
    if not isinstance(arg_video, plexapi.video.Video):
        hu.error_print(f"Invalid type. You gave me {type(arg_video)} but I only know how to handle str or plexapi.video.Video")
        return None

    if isinstance(arg_video, plexapi.video.Show):
        summary_filename = str(pathlib.Path(filename_on_server(arg_video.seasons()[0].episodes()[0])).parent.parent / 'summary.txt' )
    elif isinstance(arg_video, plexapi.video.Season):
        summary_filename = str(pathlib.Path(filename_on_server(arg_video.episodes()[0])).parent / 'summary.txt' )
    elif isinstance(arg_video, plexapi.base.Playable):
        video_filename = filename_on_server(arg_video)
        summary_filename = video_filename + '.summary.txt'
    else:
        hu.error_print(f"No support for {type(arg_video)} yet!")
        return False

    if os.path.exists(summary_filename):
        hu.timestamped_print(f"Summary file {summary_filename} found!")
        summary = hu.text_read_whole_file(summary_filename)
        hu.timestamped_print(f"Setting the summary to:\n'{summary}\n'")
        return arg_video.editSummary(summary, locked=True)

    hu.log_print(f"Could NOT find any file named: {summary_filename}")
    return False

def show(arg_server: str, arg_show: Union[List[str], str]) -> List[plexapi.video.Show]:
    ''' Given a shows EXACT name, find them '''

    res = []
    if not arg_show:
        return res

    if isinstance(arg_show, str):
        arg_show = [arg_show]

    for section in sections(arg_server).values():
        if section.type == 'show':
            for _show in section.all():
                if _show.title in arg_show:
                    res.append(_show)
                    del arg_show[arg_show.index(_show.title)]
                    if not arg_show:
                        return res
    return res

def movie(arg_server: str, arg_movie: Union[List[str], str]) -> List[plexapi.video.Movie]:
    ''' Given movies EXACT names, find them '''

    res = []
    if not arg_movie:
        return res

    if isinstance(arg_movie, str):
        arg_movie = [arg_movie]

    for section in sections(arg_server).values():
        if section.type == 'movie':
            for _movie in section.all():
                if _movie.title in arg_movie:
                    res.append(_movie)
                    del arg_movie[arg_movie.index(_movie.title)]
                    if not arg_movie:
                        return res
    return res

def playlist(arg_server: str,
             arg_playlist: Union[plexapi.playlist.Playlist, List[plexapi.playlist.Playlist], str, List[str], None] = None,
             arg_migrate_to_server: str = None) -> List[plexapi.base.Playable]:

    ''' Default: Get the playlist as a List[plexapi.base.Playable]
        
        argument arg_migrate_to_server: str --> set this to create the playlist on this server
    
    '''

    res = []
    if arg_playlist is None:
        arg_playlist = server(arg_server).playlists()

    if isinstance(arg_playlist, List):
        for _playlist in arg_playlist:
            res.append(playlist_print(arg_server, _playlist, arg_migrate_to_server))
        return res

    _server = server(arg_server)
    _new_server = server(arg_migrate_to_server) if arg_migrate_to_server else None
    print(f"Migrate to: {_new_server.friendlyName}")

    if isinstance(arg_playlist, str):
        arg_playlist = _server.playlist(arg_playlist)

    print(f"Playlist title: {arg_playlist.title}")
    _shows = []
    _movies = []
    for _video in arg_playlist.items():
        if _video.type == 'episode':
            _shows.append(_video.show().title)
        else:
            _movies.append(_video.title)

    print("Shows:")
    print('\n'.join(_shows))
    print()
    print("Movies:")
    print('\n'.join(_movies))

    if arg_migrate_to_server:
        hu.timestamped_print(f"Starting the hard work of creating the playlist on {_new_server.friendlyName}")
        for _show in show(arg_migrate_to_server, _shows):
            res.append(_show.seasons()[0].episodes()[0])

        res.extend(movie(arg_migrate_to_server, _movies))

        _new_server.createPlaylist(title=arg_playlist.title, items=res)

    hu.timestamped_print("Done!")
    return res

if __name__ == "__main__":
    version = f"{__version__} by {__author__}"
    parser = argparse.ArgumentParser(
        description=f"Downloader and player for Plex {version}")
    parser.add_argument("-s", "--subfolders", action="store_true",
                        dest="check_subfolders", help="Look in subfolders", default=False)
    parser.add_argument("-i", "--virtual", action="store_true",
                        dest="virtual_file_system", help="Create a HVFS file", default=False)
    parser.add_argument("-l", "--vlc", action="store_true",
                        dest="vlc", help="Play in VLC", default=False)
    parser.add_argument("-p", "--playlist", action="store_true",
                        dest="playlist", help="Read input from playlist file", default=False)
    parser.add_argument("url", nargs="+")
    args = parser.parse_args()

    hu.timestamped_print("Starting")
    urls = []
    if args.playlist:
        urls = hu.text_read_whole_file(args.url[0]).splitlines()
    else:
        for url in args.url:
            urls.append(url)

    for url in urls:
        if args.vlc:
            ret = play_in_vlc(url)
        else:
            ret = download_from_plex(url, args.virtual_file_system)
    hu.timestamped_print(ret)
    hu.timestamped_print("Done")
