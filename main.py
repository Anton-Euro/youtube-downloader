from pytube import YouTube
from CTkMessagebox import CTkMessagebox
import customtkinter
import re
import os
from threading import Thread
import subprocess

customtkinter.set_appearance_mode("dark")

app = customtkinter.CTk()
app.resizable(False, False)
app.title('YouTube Downloader')
x = (app.winfo_screenwidth() - app.winfo_reqwidth()) // 2 - (500 // 4)
y = (app.winfo_screenheight() - app.winfo_reqheight()) // 2 - (300 // 4)
app.wm_geometry(f"+{x}+{y}")
app.geometry("500x300")

if os.path.exists('.\output') == False:
    os.mkdir('.\output')
if os.path.exists('.\cache') == False:
    os.mkdir('.\cache')

name_size_file = {
	0: 'bytes',
	1: 'KB',
	2: 'MB',
	3: 'GB',
	4: 'TB'
}

def remove_special_characters(text):
    pattern = r'[^a-zA-Z0-9\s]'
    return re.sub(pattern, '', text)

file = {}

def on_progress(stream, chunk, bytes_remaining):
    totalsize = stream.filesize
    bytes_downloaded = totalsize - bytes_remaining
    percentage = round(progress_c + (bytes_downloaded / total_size), 2)
    progress_label.configure(text=f'{int(percentage * 100)} %')
    progressbar.set(percentage)

def search():
    global file, yt
    progress_label.configure(text='0 %')
    progressbar.set(0)
    url = entry.get()
    name_label.configure(text=f'name: None')
    duration_label.configure(text=f'duration: None')
    filesize_label.configure(text=f'file size: None')
    try:    
        yt = YouTube(url, on_progress_callback=on_progress)
        file['url'] = url
        file['name'] = yt.title
        file['duration'] = yt.length
    except:
        CTkMessagebox(title="Error", message="URL not valid", icon="cancel")
        return
    file['video'] = {}; file['audio'] = {}
    for stream in yt.streaming_data['adaptiveFormats']:
        if stream['mimeType'].split(';')[0].split('/')[1] not in file['video'] and stream['mimeType'].split(';')[0].split('/')[0] == 'video':
            file['video'][stream['mimeType'].split(';')[0].split('/')[1]] = [[f"{stream['height']}p/{stream['fps']}fps", stream['itag']]]
        elif stream['mimeType'].split(';')[0].split('/')[1] in file['video'] and stream['mimeType'].split(';')[0].split('/')[0] == 'video':
            file['video'][stream['mimeType'].split(';')[0].split('/')[1]].append([f"{stream['height']}p/{stream['fps']}fps", stream['itag']])
        elif stream['mimeType'].split(';')[0].split('/')[1] not in file['audio'] and stream['mimeType'].split(';')[0].split('/')[0] == 'audio':
            file['audio'][stream['mimeType'].split(';')[0].split('/')[1]] = [stream['itag']]
        elif stream['mimeType'].split(';')[0].split('/')[1] in file['audio'] and stream['mimeType'].split(';')[0].split('/')[0] == 'audio':
            file['audio'][stream['mimeType'].split(';')[0].split('/')[1]].append(stream['itag'])
    name_label.configure(text=f'name: {file["name"]}')
    duration_label.configure(text=f'duration: {file["duration"] // 60} m {file["duration"] % 60} s')
    res.configure(values=[el[0] for el in list(file['video'].items())[0][1]])
    res.set(list(file['video'].items())[0][1][0][0])
    mime_type.configure(values=[el for el in list(file['video'].keys())])
    mime_type.set(list(file['video'].keys())[0])
    size = yt.streams.get_by_itag(list(file['video'].items())[0][1][0][1]).filesize + yt.streams.get_by_itag(list(file['audio'].values())[0][-1]).filesize
    d = 0
    while size / 1024 > 1:
        d += 1
        size = round(size / 1024, 2)
    filesize_label.configure(text=f'file size: {size} {name_size_file[d]}')

def on_search():
    t = Thread(target=search, daemon=True)
    t.start()

def download():
    global total_size, progress_c
    itag = 0; resolution = res.get(); mimetype = mime_type.get()
    for el in file['video'][mimetype]:
        if el[0] == resolution:
            itag = int(el[1])
            break
    progress_c = 0
    total_size = yt.streams.get_by_itag(file['video'][mimetype][0][1]).filesize + yt.streams.get_by_itag(file['audio'][mimetype][-1]).filesize
    yt.streams.get_by_itag(itag).download(output_path='cache', filename=f'part1.{mimetype}')
    progress_c = progressbar.get()
    yt.streams.get_by_itag(file['audio'][mimetype][-1]).download(output_path='cache', filename=f'part2.{mimetype}')
    
    subprocess.call(['ffmpeg.exe', '-i', f'cache\part1.{mimetype}', '-i', f'cache\part2.{mimetype}', '-c', 'copy', f'output\{remove_special_characters(file["name"])}.{mimetype}', '-loglevel', 'quiet'], creationflags=0x08000000)
    progress_label.configure(text='100 %')
    progressbar.set(1)
    os.remove(f'cache\\part1.{mimetype}')
    os.remove(f'cache\\part2.{mimetype}')

def on_download():
    t = Thread(target=download, daemon=True)
    t.start()

def mime_type_callback(choice):
    res.configure(values=[el[0] for el in file['video'][choice]])
    res.set(file['video'][choice][0][0])
    size = yt.streams.get_by_itag(file['video'][choice][0][1]).filesize + yt.streams.get_by_itag(file['audio'][choice][-1]).filesize
    d = 0
    while size / 1024 > 1:
        d += 1
        size = round(size / 1024, 2)
    filesize_label.configure(text=f'file size: {size} {name_size_file[d]}')

def res_callback(choice):
    mimetype = mime_type.get()
    for el in file['video'][mimetype]:
        if el[0] == choice:
            size = yt.streams.get_by_itag(el[1]).filesize + yt.streams.get_by_itag(file['audio'][mimetype][-1]).filesize
            break
    d = 0
    while size / 1024 > 1:
        d += 1
        size = round(size / 1024, 2)
    filesize_label.configure(text=f'file size: {size} {name_size_file[d]}')

entry = customtkinter.CTkEntry(app, width=380, placeholder_text="enter your download link")
entry.grid(row=0, column=0, pady=(20, 0), padx=(30,10), sticky='w')
searsh_butt = customtkinter.CTkButton(app, text="search", width=50, command=on_search)
searsh_butt.grid(row=0, column=1, pady=(20, 0))

name_label = customtkinter.CTkLabel(app, text='name: None', wraplength=380)
name_label.grid(row=1, column=0, padx=30, pady=5, sticky='w')
duration_label = customtkinter.CTkLabel(app, text='duration: None')
duration_label.grid(row=2, column=0, padx=30, pady=(0,5), sticky='w')
filesize_label = customtkinter.CTkLabel(app, text='file size: None')
filesize_label.grid(row=3, column=0, padx=30, pady=(0,10), sticky='w')

frame = customtkinter.CTkFrame(app, fg_color="transparent")
frame.grid(row=4, column=0, columnspan=2, padx=(30, 0), sticky='w')
res = customtkinter.CTkOptionMenu(frame, values=[''],width=180, command=res_callback)
res.grid(row=0, column=0, padx=(0,10))
mime_type = customtkinter.CTkOptionMenu(frame, values=[''], command=mime_type_callback)
mime_type.grid(row=0, column=1)

download_butt = customtkinter.CTkButton(app, text='download', width=445, command=on_download)
download_butt.grid(row=5, column=0, pady=10, padx=(30, 0), columnspan=2, sticky='w')

frame1 = customtkinter.CTkFrame(app, fg_color="transparent")
frame1.grid(row=6, column=0, columnspan=2, padx=(30, 0), sticky='w')

progress_label = customtkinter.CTkLabel(frame1, text='0 %')
progress_label.grid(row=0, column=0, padx=(0,10))
progressbar = customtkinter.CTkProgressBar(frame1, orientation="horizontal", width=415, height=15)
progressbar.grid(row=0, column=1)
progressbar.set(0)

app.mainloop()