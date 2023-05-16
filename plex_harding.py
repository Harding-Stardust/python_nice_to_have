#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''

Helper functions to work with a Plex Media Server via Python

https://python-plexapi.readthedocs.io/en/latest/modules/library.html#
https://github.com/pkkid/python-plexapi
https://pypi.org/project/PlexAPI/

# TODO: Trending on Plex:
https://app.plex.tv/desktop/#!/media/tv.plex.provider.discover?source=home

TODO: Plex has guids!
https://app.plex.tv/desktop/#!/provider/tv.plex.provider.discover/details?key=%2Flibrary%2Fmetadata%2F<guid>
The Super Mario Bros. Movie: https://app.plex.tv/desktop/#!/provider/tv.plex.provider.discover/details?key=%2Flibrary%2Fmetadata%2F5f40cdfabf3e560040d5cd85

section.search(guid='plex://movie/61ec22a05eba2b44f621dff3')
'''

__version__ = 230516182520
__author__ = "Harding"
__description__ = __doc__
__copyright__ = "Copyright 2023"
__credits__ = ["Other projects"]
__license__ = "GPL"
__maintainer__ = "Harding"
__email__ = "not.at.the.moment@example.com"
__status__ = "Development"


__path_to_vlc__ = r"C:\Program Files\VideoLAN\VLC\vlc.exe"
__PLEX_USERNAME = 'USERNAME'
__PLEX_PASSWORD = 'PASSWORD'

import os
from typing import Union, List, Dict, Set, Tuple
import pathlib
import plexapi.myplex # pip install plexapi
import harding_utils as hu
import harding_json as hj

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

def server(arg_plex_resource: Union[plexapi.myplex.MyPlexResource, str, plexapi.server.PlexServer]) -> plexapi.server.PlexServer:
    """ Connect to a Plex server """

    if isinstance(arg_plex_resource, plexapi.server.PlexServer):
        return arg_plex_resource

    arg_plex_resource = _resource(arg_plex_resource) if isinstance(arg_plex_resource, str) else arg_plex_resource

    if not isinstance(arg_plex_resource, plexapi.myplex.MyPlexResource):
        print('Invalid argument, arg_plex_resource must be either str or plexapi.myplex.MyPlexResource')
        return None

    _local_ips = ['https://172', 'https://192', 'https://10.', 'https://127']
    if not arg_plex_resource.clientIdentifier == 'XXXXXXXXXX': # My local server
        while arg_plex_resource.connections[0].uri[0:11] in _local_ips: # Never try to connect to the LAN IP on other Plex servers
            del arg_plex_resource.connections[0]

    return arg_plex_resource.connect()

def play_in_vlc(arg_plex_path: str) -> Union[str, None]:
    return download_from_plex(arg_plex_path=arg_plex_path, arg_virtual_file_system=False, arg_start_vlc=True)

def download_from_plex(arg_plex_path: Union[plexapi.base.Playable, str],
                       arg_virtual_file_system: bool = False,
                       arg_start_vlc: bool = False,
                       arg_download_poster: bool = False) -> Union[str, None]:
    ''' Enter a URL to a plex video and this function downloads the subs and the video
    '''
    if not arg_plex_path:
        return None

    _video = video(arg_plex_path) if isinstance(arg_plex_path, str) else arg_plex_path
    if not isinstance(_video, plexapi.base.Playable) and not isinstance(_video, plexapi.audio.Audio):
        hu.error_print(f"Cannot handle {type(_video)}")
        return None

    video_filename = filename_on_server(_video, arg_only_basename=True, arg_safe_local_filename=True)

    downloaded_subs = []
    if hasattr(video, "subtitleStreams"):
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

def users_can_download(arg_server: Union[plexapi.server.PlexServer, str], arg_allowed_download: bool = True):
    ''' Set the 'allow download' on all users '''

    _server = server(arg_server) if isinstance(arg_server, str) else arg_server
    for _user in account().users():
        hu.timestamped_print(f"Changing user: {_user.email}")
        account().updateFriend(_user, _server, allowSync=arg_allowed_download)

def users_can_access_sections(arg_users: List[plexapi.myplex.MyPlexUser],
                              arg_sections: List[plexapi.library.LibrarySection]):
    ''' The users in the arg_users will have access to the sections in arg_sections '''

    if isinstance(arg_users, dict):
        arg_users = list(arg_users.values())

    if isinstance(arg_sections, dict):
        arg_sections = list(arg_sections.values())

    section_names = [_section.title for _section in arg_sections]

    for _user in arg_users:
        hu.timestamped_print(f"Changing user: {_user.email} --> adding {', '.join(section_names)}")
        try:
            account().updateFriend(_user, arg_sections[0]._server, sections=arg_sections, allowSync=True)
        except plexapi.exceptions.BadRequest as exc:
            hu.log_print(f"Got a BadRequest exception: {exc}")

def sections(arg_server: Union[plexapi.server.PlexServer, str],
             arg_filter: Union[List[str], Dict[str, plexapi.library.LibrarySection], None] = None
             ) -> Union[Dict[str, plexapi.library.LibrarySection], None]:
    ''' Sections are what the use see on the left side ('Movies', 'Shows' and so on)

        returns a dict that looks like: result['Movies']: <MovieSection:8:Movies>,
    '''

    _server = server(arg_server) if isinstance(arg_server, str) else arg_server

    if not isinstance(_server, plexapi.server.PlexServer):
        hu.error_print('Invalid argument, arg_server must be either str or plexapi.server.PlexServer')
        return None
    res = {}
    for section in _server.library.sections():
        if arg_filter is None or section.title in arg_filter:
            res[section.title] = section

    return res

def https_url(arg_video: plexapi.video.Video, arg_index_if_multiple: int = 0) -> Union[str, None]:
    ''' Get the URL that is used to download a movie/episode/clip from something that identify a video '''

    _server = arg_video._server # This special member seems to exist on all of the given objects we can handle

    no_download_fix = '&download=0' # We add the download=0 cause if the server is configured to not allow downloads, this will will work anyway

    # Album
    if isinstance(arg_video, plexapi.audio.Album):
        arg_video = arg_video.tracks()[0] # arg_video is now plexapi.audio.Track

    # Track
    if isinstance(arg_video, plexapi.audio.Audio):
        return _server.url(arg_video.media[arg_index_if_multiple].parts[0].key, includeToken=True) + no_download_fix

    # Subtitle
    if isinstance(arg_video, plexapi.media.SubtitleStream):
        subtitle = arg_video
        return _server.url(subtitle.key, includeToken=True) + no_download_fix

    # Poster / art
    if isinstance(arg_video, plexapi.media.Poster):
        poster = arg_video
        return _server.url(poster.key, includeToken=True) + no_download_fix

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

    res = _server.url(part.key, includeToken=True) + no_download_fix
    return res

def video(arg_plex_url: str) -> plexapi.video.Video:
    ''' Take in an Plex URL that can identify a video and return the Video object '''

    if isinstance(arg_plex_url, plexapi.video.Video):
        return arg_plex_url
    if not isinstance(arg_plex_url, str):
        hu.error_print(f"Invalid type. You gave me {type(arg_plex_url)} but I only know how to handle str or plexapi.video.Video")
        return None

    video_id: int = int(hu.regexp_findall_quick_fix(r"metadata%2F(\d+)", arg_plex_url, ['video id not found'])[0])
    return server(arg_plex_url).fetchItem(video_id)

def share(arg_video: Union[plexapi.base.Playable, str]) -> Union[str, None]:
    ''' Get an URL you can send to your friends '''

    arg_video = video(arg_video) if isinstance(arg_video, str) else arg_video
    if not isinstance(arg_video, plexapi.base.Playable) and not isinstance(arg_video, plexapi.audio.Audio):
        hu.error_print(f"Invalid type. You gave me {type(arg_video)} but I only know how to handle str, plexapi.base.Playable (videos) or plexapi.audio.Audio")
        return None

    if arg_video.guid.startswith('com.plexapp.agents.none://'):
        hu.error_print("No GUID for this video")
        return None

    l_guid = hu.regexp_findall_quick_fix(r"/([0-9a-fA-F]{10,})", arg_video.guid)[0]
    res = f"https://app.plex.tv/desktop/#!/provider/tv.plex.provider.discover/details?key=%2Flibrary%2Fmetadata%2F{l_guid}"
    return res

def filename_on_server(arg_video: Union[plexapi.base.Playable, str],
                       arg_index_if_multiple: int = 0,
                       arg_only_basename: bool = False,
                       arg_safe_local_filename: bool = False) -> str:
    ''' Return the full file path on the SERVER for the video '''

    if isinstance(arg_video, str):
        arg_video = video(arg_video)
    if not isinstance(arg_video, plexapi.base.Playable) and not isinstance(arg_video, plexapi.audio.Audio):
        hu.error_print(f"Invalid type. You gave me {type(arg_video)} but I only know how to handle str, plexapi.base.Playable (videos) or plexapi.audio.Audio")
        return None

    if isinstance(arg_video, plexapi.audio.Album):
        arg_video = arg_video.tracks()[0] # arg_video is now a plexapi.audio.Track which has the .media[0].parts[0].file

    res = arg_video.media[arg_index_if_multiple].parts[0].file
    if arg_only_basename:
        res = os.path.basename(res)
    if arg_safe_local_filename:
        res = hu.smart_filesystem_safe_path(res)
    return res

def download_season(arg_plex_server: str,
                    arg_show_name: str,
                    arg_seasons: Union[str, List, Set, Tuple, None],
                    arg_dest_dir: str,
                    arg_filter: Union[List[str], Dict[str, plexapi.library.LibrarySection], None] = None) -> bool:
    arg_seasons = hu.list_from_str(arg_seasons)

    for section in sections(arg_plex_server, arg_filter=arg_filter).values():
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
    ''' Given a Video, check if there is a file named: <videoname>.json next to it
    For a show, there must be a file named .json in the root of the show
    For a season, there must be a file named .json in the root of the season

    If I find any summary file, I read the content and set it to the file
    '''
    if isinstance(arg_video, str):
        arg_video = video(arg_video)
    if not isinstance(arg_video, plexapi.video.Video):
        hu.error_print(f"Invalid type. You gave me {type(arg_video)} but I only know how to handle str or plexapi.video.Video")
        return None

    filename = ".json"
    if isinstance(arg_video, plexapi.video.Show):
        summary_filename = str(pathlib.Path(filename_on_server(arg_video.seasons()[0].episodes()[0])).parent.parent / filename ) # TODO: test this
    elif isinstance(arg_video, plexapi.video.Season):
        summary_filename = str(pathlib.Path(filename_on_server(arg_video.episodes()[0])).parent / filename )  # TODO: test this
    elif isinstance(arg_video, plexapi.base.Playable):
        video_filename = filename_on_server(arg_video)
        summary_filename = video_filename + filename
    else:
        hu.error_print(f"No support for {type(arg_video)} yet!")
        return False

    if os.path.exists(summary_filename):
        hu.timestamped_print(f"Summary file {summary_filename} found!")
        info_json = hj.unwrapped_json(summary_filename)
        summary = info_json.get('description', '').strip()
        youtube_id = info_json.get('id', '').strip()
        if youtube_id:
            if youtube_id.startswith('http'):
                summary += f"\n\n{youtube_id}"
            else:
                summary += f"\n\nhttps://www.youtube.com/watch?v={youtube_id}"

        title = ""
        if hasattr(arg_video, 'seasonEpisode'):
            title += f"{arg_video.seasonEpisode.upper()}: "

        title += f"{info_json.get('title', '').strip()}"

        if title:
            hu.timestamped_print(f"Setting the title to:\n'{title}'\n")
            arg_video.editTitle(title, locked=True)
        if summary:
            hu.timestamped_print(f"Setting the summary to:\n'{summary}'\n")
            arg_video.editSummary(summary, locked=True)
        return True

    hu.log_print(f"Could NOT find any file named: {summary_filename}")
    return False

def playlist(arg_server: str,
             arg_playlist: Union[plexapi.playlist.Playlist, List[plexapi.playlist.Playlist], str, List[str], None] = None,
             arg_migrate_to_server: Union[str, None] = None
             ) -> List[plexapi.base.Playable]:

    ''' Default: Get the playlist as a List[plexapi.base.Playable]
        argument arg_playlist --> set this to None to take ALL playlists
        argument arg_migrate_to_server: str --> set this to create the playlist on this server

    '''

    res = []
    if arg_playlist is None:
        arg_playlist = server(arg_server).playlists()

    if isinstance(arg_playlist, List):
        for _playlist in arg_playlist:
            res.append(playlist(arg_server, _playlist, arg_migrate_to_server))
        return res

    _server = server(arg_server)
    _new_server = server(arg_migrate_to_server) if arg_migrate_to_server else None
    print(f"Migrate to: {getattr(_new_server, 'friendlyName', '< Not migrating >')}")

    if isinstance(arg_playlist, str):
        arg_playlist = _server.playlist(arg_playlist)

    print(f"Playlist title: {arg_playlist.title}")
    _episodes = []
    _movies = []
    for _video in arg_playlist.items():
        if _video.type == 'episode':
            _episodes.append(_video.guid)
        else:
            _movies.append(_video.guid)

    if arg_migrate_to_server:
        print()
        hu.timestamped_print(f"Starting the hard work of creating the playlist on {_new_server.friendlyName}")
        for _episode in _episodes:
            res.extend(_new_server.library.section('TV Shows').searchEpisodes(guid=_episode))

        for _movie in _movies:
            res.extend(_new_server.library.section('Movies').search(guid=_movie))

        _new_server.createPlaylist(title=arg_playlist.title, items=res)
    else:
        res = list(arg_playlist)
    hu.timestamped_print("Done!")
    return res

def playlist_print(arg_playlist: List[plexapi.base.Playable]):
    ''' Print the playlist in a better way '''
    for item in arg_playlist:
        l_title: str = 'unknown'
        l_show = getattr(item, 'show', None)
        if l_show:
            l_title = "Show:  " + l_show().title
        else:
            l_title = "Movie: " + item.title
        print(l_title  + "    " + share(item))

def search_summary(arg_sections: List[plexapi.library.LibrarySection],
                   arg_regexp: str,
                   arg_limit_hits: int = 0
                   ) -> List[plexapi.base.Playable]:
    ''' Search for a video with text from the summary (description) '''

    if isinstance(arg_sections, plexapi.library.LibrarySection):
        arg_sections = [arg_sections]

    res = []
    for l_section in arg_sections:
        for l_video in l_section.all():
            l_match = hu.regexp_findall_quick_fix(arg_regexp, l_video.summary, arg_default_return_if_not_found='No match')[0]
            if l_match != 'No match':
                res.append(l_video)
                arg_limit_hits -= 1
                if arg_limit_hits == 0:
                    return res

    return res

def collections(arg_server: str, arg_save_to_file: str = None) -> Dict[str, Dict[str, Dict[str, str]]]:
    ''' Get all collections and their items in a massive dict:
        
        {
            "Movies": {
                "My favorite movies (collection name)": {
                    "plex://movie/XXXXXXXXXXXXXXXXXXXXXXXX": "Movie title 1",
                    "plex://movie/XXXXXXXXXXXXXXXXXXXXXXXX": "Movie title 2",
                    "plex://movie/XXXXXXXXXXXXXXXXXXXXXXXX": "Movie title 3"
                }
            }
        }

    '''
    res = {}
    l_sections = list(sections(arg_server).values())
    for l_section in l_sections:
        res[l_section.title] = {}
        l_collections = l_section.search(libtype='collection')
        for l_collection in l_collections:
            res[l_section.title][l_collection.title] = {}
            for l_video in l_collection:
                res[l_section.title][l_collection.title][l_video.guid] = l_video.title


    if arg_save_to_file:
        hu.dict_dump_to_json_file(res, arg_save_to_file)
    return res





















if __name__ == "__main__":
    import argparse
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
    urls: List[str] = []
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
    hu.timestamped_print(ret if ret else '')
    hu.timestamped_print("Done")
