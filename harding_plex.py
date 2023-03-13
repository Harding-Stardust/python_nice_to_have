#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__path_to_vlc__ = r"C:\Program Files\VideoLAN\VLC\vlc.exe"

import os
import argparse
import typing as _typing

import harding_utils as hu
import plexapi.myplex # pip install plexapi    https://pypi.org/project/PlexAPI/        https://github.com/pkkid/python-plexapi       https://python-plexapi.readthedocs.io/en/latest/modules/library.html#

g_account = None

def account(arg_force_reconnect: bool = False) -> plexapi.myplex.MyPlexAccount:
    global g_account

    if arg_force_reconnect:
        g_account = None

    if not g_account:
        g_account = plexapi.myplex.MyPlexAccount(username='PLEX_USERNAME', password='PLEX_PASSWORD') # TODO: SECRET: Make sure this is not posted on the internet
    return g_account

def _resource(arg_name_or_client_id: str) -> plexapi.myplex.MyPlexResource:
    """ Internal function, please use server() instead.

    Get the info needed to connect to the resource """

    _account = account()
    for r in _account.resources():
        if r.clientIdentifier.lower() in arg_name_or_client_id.lower() or arg_name_or_client_id.lower() in r.name.lower():
            return r
    return None

def server(arg_plex_resource: str) -> plexapi.server.PlexServer:
    """ Connect to a Plex server """

    if isinstance(arg_plex_resource, str):
        l_resource = _resource(arg_plex_resource)
    else:
        l_resource = arg_plex_resource

    if not isinstance(l_resource, plexapi.myplex.MyPlexResource):
        print('Invalid argument, arg_plex_resource must be either str or plexapi.myplex.MyPlexResource')
        return None

    if not l_resource.clientIdentifier == '64557c5f54f73dea8054c8317f8742e84a4cac85': # My local server
        while l_resource.connections[0].uri[0:11] in ['https://172', 'https://192']: # Never try to connect to the LAN IP on other Plex servers
            del l_resource.connections[0]

    return l_resource.connect()

def play_in_vlc(arg_plex_path: str) -> str:
    return download_from_plex(arg_plex_path=arg_plex_path, arg_virtual_file_system=False, arg_start_vlc=True)

def download_from_plex(arg_plex_path: str, arg_virtual_file_system: bool = False, arg_start_vlc: bool = False) -> str:
    if not arg_plex_path:
        return None
    _server = server(arg_plex_path)
    movie = video(arg_plex_path)
    movie_filename = hu.smart_filesystem_safe_path(os.path.basename(movie.media[0].parts[0].file))

    downloaded_subs = []
    for sub in movie.subtitleStreams():
        if not sub.key:
            continue
        sub_full_url = https_url(sub)
        sub_local_name = f"{os.path.splitext(movie_filename)[0]}.{sub.languageCode}.{sub.codec}"
        downloaded_subs.append(hu.download_file(arg_url=sub_full_url, arg_local_filename=sub_local_name))

    # video_url_in_plex = _server.url(f"{movie.media[0].parts[0]._details_key}?X-Plex-Token={_server._token}&download=0") # If the Plex server doesn't allow downloads, this has to be set to 0
    video_url_in_plex = https_url(movie)

    if arg_start_vlc:
        vlc_command = f'"{__path_to_vlc__}" "{video_url_in_plex}"'
        if downloaded_subs:
            vlc_command += f' --no-sub-autodetect-file --sub-file "{downloaded_subs[0]}"'
        hu.timestamped_print(f"\n\nStarting VLC: {vlc_command}\n\n")
        os.system('"' + vlc_command + '"')

        for sub in downloaded_subs:
            os.remove(sub)

        return vlc_command

    hu.download_file(movie.thumbUrl, arg_local_filename=os.path.splitext(movie_filename)[0] + ".jpg")

    if arg_virtual_file_system:
        downloaded_video = os.path.basename(movie.media[0].parts[0].file)
        with open(downloaded_video, 'w', encoding='utf-8', newline='\n') as f:
            f.write(f'HVFS\n{video_url_in_plex}')
    else:
        downloaded_video = hu.download_file(video_url_in_plex, arg_local_filename=movie_filename)
    return downloaded_video

def list_users() -> dict:
    _account = account()

    users = {}
    for user in _account.users():
        if not user.email:
            continue
        user.real_name = 'unknown name'
        user.notes = ' '
        if user.id == 2342342342342342:
            user.real_name = 'Johnny'
            user.notes = 'Friend of my sister'
        
        users[user.id] = user

    users = hu.dict_sort(users)

    print(f'{"Username:":20s}{"Real name":30s}{"Email:":40s}{"user_id:":55s}{"Notes:"}')
    for user in users.values():
        print(f'{user.username:20s}{user.real_name:30s}{user.email:40s}http://<PLEX_SERVER>/user?user_id={str(user.id):12s}{user.notes}')
    print("To remove users: https://app.plex.tv/desktop/#!/settings/manage-library-access")

    return users

def sections(arg_plex_server: str) -> _typing.Dict[str, plexapi.library.LibrarySection]:
    ''' Sections are what the use see on the left side ('Movies', 'Shows' and so on) '''
    if isinstance(arg_plex_server, str):
        _server = server(arg_plex_server)
    else:
        _server = arg_plex_server

    if not isinstance(_server, plexapi.server.PlexServer):
        print('Invalid argument, arg_plex_server must be either str or plexapi.server.PlexServer')
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
        part = arg_video.parts[arg_index_if_multiple]
    elif isinstance(arg_video, plexapi.video.Video):
        part = arg_video.media[0].parts[arg_index_if_multiple]

    res = _server.url(part._details_key, includeToken=True) + '&download=0' # We add the download=0 cause if the server is configured to not allow downloads, this will will work anyway
    return res

def generate_HVFS(arg_plex_server: plexapi.server.PlexServer, arg_dest_dir: str, arg_ignore: list = None) -> bool:
    if not arg_ignore:
        arg_ignore = ["Anime Movies (Dual)", "Anime Movies (Subs)", "Movies (4K)", "Movies (Foreign)", "Anime (Dual-Audio)", "Anime (Dubs)", "Anime (Subs)", "Fitness", "TV Shows (4K)", "TV Shows (Foreign)", "Audiobooks"]
    
    for section_name, section in sections(arg_plex_server).items():
        if section_name.strip() in arg_ignore:
            print(f"Ignoring {section_name}")
            continue

        if section.type == 'show':
            for show in section.all():
                for season in show.seasons():
                    for episode in season.episodes():
                        full_path = os.path.join(arg_dest_dir, hu.smart_filesystem_safe_path(section.title), hu.smart_filesystem_safe_path(show.title), f"S{season.seasonNumber:02d}", hu.smart_filesystem_safe_path(os.path.basename(episode.media[0].parts[0].file)))

                        if len(full_path) > 259:
                            ext = os.path.splitext(episode.media[0].parts[0].file)[1]
                            full_path = os.path.join(arg_dest_dir, hu.smart_filesystem_safe_path(section.title), hu.smart_filesystem_safe_path(show.title), f"S{season.seasonNumber:02d}", hu.smart_filesystem_safe_path(os.path.basename(episode.media[0].parts[0].file[0:100] + ext)))

                        hu.ensure_dir(full_path)
                        hu.text_write_whole_file(full_path, f"HVFS\n{https_url(episode)}")
                        # print(f"{section.title} / {show.title} / S{season.seasonNumber:02d}E{episode.episodeNumber:02d} Title: {episode.title} filename: {os.path.basename(episode.media[0].parts[0].file)} --> {episode._server.url(episode.media[0].parts[0]._details_key, includeToken=True) + '&download=0'}")

        elif section.type == 'movie':
            for movie in section.all():
                full_path = os.path.join(arg_dest_dir, hu.smart_filesystem_safe_path(section.title), hu.smart_filesystem_safe_path(movie.title), hu.smart_filesystem_safe_path(os.path.basename(movie.media[0].parts[0].file)))

                if len(full_path) > 259:
                    full_path = os.path.join(arg_dest_dir, hu.smart_filesystem_safe_path(section.title), hu.smart_filesystem_safe_path(movie.title[50]), hu.smart_filesystem_safe_path(os.path.basename(movie.media[0].parts[0].file)))

                if len(full_path) > 259:
                    ext = os.path.splitext(movie.media[0].parts[0].file)[1]
                    full_path = os.path.join(arg_dest_dir, hu.smart_filesystem_safe_path(section.title), hu.smart_filesystem_safe_path(movie.title[50]), hu.smart_filesystem_safe_path(os.path.basename(movie.media[0].parts[0].file[0:50] + ext)))

                hu.ensure_dir(full_path)
                hu.text_write_whole_file(full_path, f"HVFS\n{https_url(movie)}")

def video(arg_url: str) -> plexapi.video.Video:
    ''' Take in an Plex URL that can identify a video '''
    _server = server(arg_url)
    video_id = int(hu.regexp_findall_quick_fix(r"metadata%2F(\d+)", arg_url, ['video id not found'])[0])
    res = _server.fetchItem(video_id)
    return res

def download_season(arg_plex_server: str, arg_show_name: str, arg_seasons: list, arg_dest_dir: str) -> bool:
    arg_seasons = hu.list_from_str(arg_seasons)

    for section in sections(arg_plex_server).values():
        if section.type == 'show':
            for show in section.all():
                if show.title.lower() == arg_show_name.lower():
                    print(f"Found the show named '{arg_show_name}'")
                    for season in show.seasons():
                        print(f"Season named '{season.title}' found")
                        if str(season.seasonNumber) in arg_seasons or season.seasonNumber in arg_seasons:
                            print(f"Season named '{season.title}' matched in {arg_seasons}")
                            for episode in season.episodes():
                                print(f"Found episode '{episode}' and starting to download that")
                                # plex_url = episode._server.url(episode.media[0].parts[0]._details_key, includeToken=True) + '&download=0'
                                plex_url = https_url(episode)
                                full_path = os.path.join(arg_dest_dir, hu.smart_filesystem_safe_path(section.title), hu.smart_filesystem_safe_path(show.title), f"S{season.seasonNumber:02d}", hu.smart_filesystem_safe_path(os.path.basename(episode.media[0].parts[0].file)))

                                if len(full_path) > 259:
                                    ext = os.path.splitext(episode.media[0].parts[0].file)[1]
                                    full_path = os.path.join(arg_dest_dir, hu.smart_filesystem_safe_path(section.title), hu.smart_filesystem_safe_path(show.title), f"S{season.seasonNumber:02d}", hu.smart_filesystem_safe_path(os.path.basename(episode.media[0].parts[0].file[0:100] + ext)))


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

if __name__ == "__main__":
    ''' Main function is run when the script is called from the console '''

    version = "v0.2 by Harding 2022-06-16 12:15:38"
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
