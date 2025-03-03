# Homebox LLM Tools
### LLM supported tools with Voice Recognition for Homebox storage
This is a program that does various things using voice recognition and LLMs to interact with your HomeBox storage. 

The current functionality is:

- Adder: Use your voice to add items to locations in your Homebox storage.
- Labeler: Let an LLM label your items with your predefined labels, according to name and description.

Further explanations for the functionality is further below.

## Requirements
- HomeBox
- Python
- [Google Gemini API Key](https://aistudio.google.com/app/apikey)
- Optionally FFMPEG for audio conversion, otherwise, processing WAV files will still work.

## Installation

Clone the repository

```bash
  git clone git@github.com:Magicanz/HB-Voice-Adder.git
```

Go to the project directory

```bash
  cd HB-Voice-Tools
```

Install Dependencies

```bash
  pip install -r requirements.txt
```

Add Homebox URL (or IP with port, keep http(s)://), Username and Password to the .env file (I would reccommend to create a new account in the same group using the "Generate Invite Link" under "Profile" in Homebox, instead of using your real credentials).

You also need to add an API key from Google Gemini to the .env file. This can be had from [This Link](https://aistudio.google.com/app/apikey).

Edit `config.ini` to change configurable settings. 

## Adder

This is a program that allows you to speak a line out loud stating where to store items, and then a list of items separated by "next". 

An example of a usable string would be:

"To drawer five of large cabinet in Garage, add a quarter inch spanner, next a Philips head screwdriver and next a Large Paintbrush. To drawer 3 of same cabinet, add five glass jars."

And have your voice recognised as a string which will be put through the Gemini LLM to generate objects that then are automatically added to Homebox through the Homebox API, or added to a CSV that can be imported by Homebox.

The program will not generate new locations and will only use the ones allowed by your setup.

You have the option to check through all the added items before they are committed to Homebox.

In `config.ini` you can choose to output to a CSV instead of interacting directly with the API, and you can make the LLM generate a short description for the items based on their names. 

Run the code by dropping an audio file onto `adder.py`

You may also run `adder.py` through the command line or an editor. 

```bash
python adder.py
```

## Labler

This is a program that allows you to let an LLM set labels for all your items.

You can choose through config whether this is done only on items that don't already have labels, or if it should be done for all items. 

Tha LLM will only use labels that you have already defined in Homebox. 

This program is run through the command line (or an editor).

```bash
python labeler.py
```
