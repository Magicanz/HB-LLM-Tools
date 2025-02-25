# Homebox Voice Adder
### Voice recognition & LLM supported adding of items into Homebox storage
This is a program that allows you to speak a line out loud stating where to store items, and then a list of items separated by "next". 

An example of a usable string would be:

"To drawer five of large cabinet in Garage, add a quarter inch spanner, next a Philips head screwdriver and next a Large Paintbrush. To drawer 3 of same cabinet, add five glass jars."

And have your voice recognised as a string which will be put through the Gemini LLM to generate objects that then are automatically added to Homebox through the Homebox API, or added to a CSV that can be imported by Homebox.

The program will not generate new locations and will only use the ones allowed by your setup.

You have the option to check through all the added items before they are committed to Homebox.

## Requirements
The project requires Python and the modules included in requirements.txt.

The voice recognition only works on WAV files, however the program has file conversion built in. For this to work FFMPEG is required to be installed on your computer. Otherwise, processing WAV files will still work. 

## Usage


Clone the repository

```bash
  git clone git@github.com:Magicanz/HB-Voice-Adder.git
```

Go to the project directory

```bash
  cd HB-Voice-Adder
```

Install Dependencies

```bash
  pip install -r requirements.txt
```

Add Homebox URL (or IP with port, keep http(s)://), Username and Password to the .env file (I would reccommend to create a new account in the same group using the "Generate Invite Link" under "Profile" in Homebox, instead of using your real credentials).

You also need to add an API key from Google Gemini to the .env file. This can be had from [This Link](https://aistudio.google.com/app/apikey).

Edit `config.ini` to save to a CSV instead of adding with API, or to have the LLM add simple descriptions to the items. 

Run the code by dropping a .wav file onto `adder.py`

You may also run `adder.py` through the command line or an editor. 

```bash
python adder.py
```
