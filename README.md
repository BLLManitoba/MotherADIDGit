
# MotherADIDLabeler
is a simple program that allows percentage-based labelling of conversational blocks. Essentially, it is a modified version of [IDSLabel](https://github.com/babylanguagelab/bll_app/tree/master/src/app/IDSLabel/client) to label conversations instead of speech segments, combined with another modified version of convolabel called alexislabel(insert link to github of that app)

![convolabel screenshot](https://github.com/babylanguagelab/bll_app/blob/master/src/app/convolabel/screenshot.PNG?raw=true "Example")

## Installation (for Windows):

The program requires two additional python modules - [PyAudio](https://people.csail.mit.edu/hubert/pyaudio/) and [Numpy](http://www.numpy.org/). These can be installed via python's package manager Pip with the following in the command prompt:
```
apt-get install ffmpeg
pip install pyaudio numpy pydub
```
To start the program, double-click on the `MotherADIDLabeler.py` file. If that does not work, you might need to [associate python files with python executable](https://docs.python.org/2/using/windows.html#executing-scripts).

Alteratively, open the program folder -> `Shift + right-click` -> `Open command window here`. In the command window, navigate to the folder where the program is saved, and then type: `python NonnativeAffectiveLabeler2l.py`

Optional: if you do not want the black console window to pop up when you open the program, add 'w' to the extension of the file name (so that it becomes `MotherADIDLabeler.pyw`)

## How it works

1. When the program opens, type in your name/initials where it says "-->Coder's Name <--". The labels you create will be saved under this name, which allows several coders to label the same audio files independently.

2. Then, type "Enter/Return" or click `Load` to pull up the audio data. The program looks for pre-processed blocks in the `output` folder of the directory where the python labeler program is saved (see [How to make blocks](#how-to-make-blocks))

3. Select a recording, chunk, speaker, and part. Click `Play` to listen to the selected part of a recording (usually a short few-second soundbite).

4. Use the radio-buttons and slider to label the part. The labels are organised in the following way:

   * Adult-Directed Speech
   * Child-Directed Speech
   * Junk
   * Confidence level in your ratings (slider)

5. If you need to make comments on the recording, do so in the comments pane at the bottom of the window.

6. After you have finished labelling a part, click `Submit` or type `Сtrl+s`. This will tell the program that you'd like it to remember everything that you've entered. This won't, however, save your labels to the hard drive! Click `Menu` -> `Save data` to properly save your data.

   Select another part by clicking on its name in the list (or arrow up/down). Parts that have been previously labelled by you will appear grey in the list.

7. When you finish working, click `Menu` -> `Save data` (or `X` button -> `Save`). This will save the labels on the hard drive. You can see the data file under the `labelled_data` folder: it will have the coder's name and a .pkl extension (e.g. `Ivan.pkl`). Do not delete or move any of these files (unless you want to reset the data). When you re-open the program, it will pull these files to load all previous labels made by that coder.

   After you have saved the data, it is safe to exit the program. In case you forget to save, a prompt will show up asking whether you really want to exit without saving. Also, as soon as the data has been modified , a little star will appear next to the program's title. It disappears if the data is saved!

   Note that you have to `Submit` the labels after each block, but you only need to `Save data` once you have finished a session and want to exit (although saving a couple of times during a session does not hurt).

8. If you want to export the data in an Excel or csv file, click `Menu` -> `Export to csv`. This will create an Excel spreadsheet with all the labelled data. You can save over previous exported excel sheets: you won't lose anything. You are exporting all coded data from all coders every time. You can export as often as you want and delete these Excel data sheets as needed. They do not matter for the functioning of the program.



## How to make blocks
NOTE: This has already been done for Kiana's project and for Megan's project!

1. Place the folders for each recording in the `input` directory. These folders should contain a .wav recording and an .eaf file for each recording you want made into blocks.

2. In the same folder as your 'input' directory, double-click on the file 'makeblocksEAF.py' to launch the block-making program. Alternately, use command prompt.

3. The program will check whether each folder contains one .eaf and one .wav file and whether their names match. Then, the processing of the recordings will begin. You should see a lot of activity in the black terminal window that opens up. Depending on the size of your files and how many you're processing, it can take several hours for the makeblocksEAF program to run, so be patient!


## Backups

To make sure that no data is lost by mistake, the program saves all block entries in the `Name.db` file under the `labelled_data` folder. This is a simple database file that is intended to keep track of data changes every time a coder clicks `Submit` button. If a program crushes unexpectedly or if a coder forgets to save, it is possible to recover most of the data from these files. It is possible to open and explore these files by istalling [Sqlite browser](http://sqlitebrowser.org/) app.


## Hot keys (some of these may have questionable/mysterious functionality...)

- `space`			        = play the selected part
- `control` + `s`		    = submit the labels to the memory
- `arrow up`        	    = select previous block/recording
- `arrow down`				= select next block/recording

----------------------------------------------------------------------

If you have any questions or suggestions, or if something does not work, contact me (Sarah) at Sarah.Macewan@umanitoba.ca, or contact convolabel's original creator Roman at belenyar@myumanitoba.ca

The program was tested on:
- Windows 10 Python 2.7.13
- Windows 7 Python 2.7.12
