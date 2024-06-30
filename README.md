### [Demo of a Generated Instrumental](http://sndup.net/9t8qn)

-----------------------

# Sample Pack Generator

## Overview

This project is a comprehensive automation tool designed to generate and publish sample packs and beats. It utilizes various libraries and APIs to create MIDI files, render audio samples, and automatically upload them to multiple platforms, including YouTube, BeatStars, and Payhip. The project includes a script that handles everything from sample generation to video creation and uploading.

## Features

- **Generate Sample Packs**: Create high-quality MIDI and audio samples using plugins like Addictive Keys, Ample Guitar, Serum, and Vital.
- **Automate Audio Rendering**: Use the DAWDreamer library to render audio samples from MIDI files.
- **Video Generation**: Create promotional videos with sample pack previews using MoviePy.
- **Image Downloading**: Automatically download relevant images from Pinterest for use in promotional materials.
- **Upload to Platforms**: Upload generated content to BeatStars, Payhip, and YouTube.
- **Customizable Tags and Metadata**: Automatically generate and insert tags and metadata for better search visibility and categorization.

## Requirements

- Python 3.8 or higher
- Required Python libraries:
  - `moviepy`
  - `pydub`
  - `random_word`
  - `scipy`
  - `shutil`
  - `PIL`
  - `google-auth`
  - `google-api-python-client`
  - `selenium`
  - `requests`
  - `beautifulsoup4`
- DAWDreamer (for rendering audio)
- OpenAI API key (for generating descriptions and images)
- BeatStars account
- Payhip account
- YouTube account with API access

## Setup

1. **Clone the Repository**:
    ```sh
    git clone https://github.com/yourusername/SamplePackGenerator.git
    cd SamplePackGenerator
    ```

2. **Install Dependencies**:
    ```sh
    pip install -r requirements.txt
    ```

3. **Set Up API Keys and Authentication**:
    - Obtain API keys for OpenAI, YouTube, and Google.
    - Save your keys in text files as specified in the script (`pushover_keys.txt`, `openai_key.txt`).

4. **Configure Paths**:
    - Update the paths in the script to point to your local directories for plugins, samples, and other resources.

5. **Run the Script**:
    ```sh
    python main_script.py
    ```

## Usage

### Generating a Sample Pack

To generate a sample pack, call the `generate_sample_pack` function with the desired parameters:

```python
generate_sample_pack(plugin_name="ample_guitar", set_preset_style="Sad", beat_generating=True)
```

## Customizing Tags
To choose tags within a character limit, use the choose_tags function:

```python
tags = choose_tags(tag_list, amount_allowed)
```
## Automating Uploads
The script includes functions to upload content to various platforms:

- BeatStars: uploadToBeatstars
- Payhip: upload_to_website
- YouTube: load_or_authenticate_channel and subsequent functions

## Error Handling

Errors and exceptions are logged and notifications are sent using Pushover.