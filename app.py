from flask import Flask, request, render_template, jsonify
import yt_dlp
import os

app = Flask(__name__)

# Define the download folder path (inside the static directory)
DOWNLOAD_FOLDER = os.path.join(app.root_path, 'static', 'downloads')

# Ensure the download folder exists
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

def download_video(url, audio_only=False):
    ydl_opts = {}

    if audio_only:
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
            'postprocessor_args': ['-ar', '44100'],  # Ensure audio is 44100Hz
            'verbose': True,  # Enable verbose logging for diagnostics
        }
    else:
        ydl_opts = {
            'format': 'best',
            'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
            'verbose': True,
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            file_name = ydl.prepare_filename(info_dict)

            # Handle audio-only file extensions (convert .webm to .mp3)
            if audio_only:
                file_name_mp3 = file_name.rsplit('.', 1)[0] + '.mp3'
                if os.path.exists(file_name_mp3):
                    return os.path.basename(file_name_mp3)  # Return MP3 filename
                else:
                    raise Exception("MP3 file not found after post-processing.")

            return os.path.basename(file_name)  # Return video filename
    except Exception as e:
        print(f"Error downloading: {str(e)}")
        return None

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        url = data.get('url')
        choice = data.get('type')

        if not url or not choice:
            return jsonify({'error': 'URL or choice is missing'}), 400

        if choice == 'video':
            file_name = download_video(url)
        elif choice == 'audio':
            file_name = download_video(url, audio_only=True)
        else:
            return jsonify({'error': 'Invalid choice'}), 400

        if file_name:
            # Return the file URL relative to the static folder
            return jsonify({'file_url': f'/static/downloads/{file_name}'})
        else:
            return jsonify({'error': 'Download failed'}), 500

    return render_template('index.html')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=3000, debug=True)
