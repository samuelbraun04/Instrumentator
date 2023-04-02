# Instrumentator

Instrumentator is a Python-based project that creates trap beats and uploads them to digital marketplaces.

## Demo

[![IMAGE ALT TEXT HERE](https://cdn-icons-png.flaticon.com/512/0/375.png)](https://sndup.net/3rrc/)

## Installation

To use Instrumentator, you will need to have Python 3.x installed on your system. You can download Python from the official website: https://www.python.org/downloads/

Once you have Python installed, you can download the Instrumentator repository:

```
git clone https://github.com/samuelbraun04/Instrumentator.git
```

With the repo cloned, run the following command to install all the required dependencies:

```
pip install -r requirements.txt 
```

To use the project to its full potential, one must have access to an OpenAI key. To get an OpenAI API key, you need to create an account on the OpenAI website and then follow these steps:

* Log in to your OpenAI account at https://beta.openai.com/login/.
* Once you are logged in, click on your username in the top right corner of the screen and select "Dashboard" from the dropdown menu.
* On the Dashboard page, click on the "Create API Key" button.
* Enter a name for your API key, such as "My App Key", and select the permissions you want to grant to the key.
* Click on the "Create API Key" button to generate your key.
* Your API key will be displayed on the next screen. Copy the key and store it in a safe place.

Once you have your API key, you can use it to access OpenAI's APIs and services. Input it in runner.py at line 60:

```
openAIKey = ''
```

## Usage

Instrumentator can be used to create trap beats using the provided instrument samples and patterns (MIDI). Add the samples and patterns you'd like to use in the Ingredients directory.

Instrumentator generates images for uploaded beats by creating variations on inputted images. Input the images you'd like to be used as bases for these variations in the Not Used subdirectory of the Images directory.

## Contributing

If you have any suggestions or improvements for Instrumentator, feel free to submit a pull request or open an issue on the GitHub repository.

## License

Instrumentator is licensed under the MIT license. See the LICENSE file for more details.