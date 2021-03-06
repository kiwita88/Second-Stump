import os, sys
import time
import random
import datetime
import threading
from filelock import Timeout, FileLock

from tooling import prettyPrint, bcolors, fullPath

def VideoFormatter(target):
    targetPath = fullPath("data/rawClips/{}.mp4".format(target))
    outputPath = fullPath("data/sync_data/{}.mp4".format(target))

    prettyPrint(bcolors.OKBLUE, "Formatting data/rawClips/{}.mp4".format(target))
    # This is a really long command so here are a bunch of comments explaining it
    # Step #1: FFMPEG makes two copies, [original] and [copy]
    # Step #2: Take [copy] and scale it to 16/9 so all videos are the same size, and apply a blur effect to it
    # Step #3: Append [original] on top of [copy] and output the finished video to data/sync_data
    prettyPrint(bcolors.ENDC, os.popen("ffmpeg -i {} -vf 'split[original][copy];[copy]scale=ih*16/9:-1,crop=h=iw*9/16,gblur=sigma=20[blurred];[blurred][original]overlay=(main_w-overlay_w)/2:(main_h-overlay_h)/2' -video_track_timescale 29971 -ac 1 {}".format(targetPath, outputPath)).read())
    # Checks to make sure the video are valid files
    try: 
        float(os.popen("ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 {}".format(outputPath)).read())
    except Exception as e:
        prettyPrint(bcolors.WARNING, "Non-viable file, file will be removed. Error code {}".format(e))
        os.remove(outputPath)
    
    # Cleans up the files and exist the thread
    os.remove(targetPath); sys.exit("Exiting the thread")

def GenerateVideo():
    # Gets minimum length of video (between 11 and 14 minutes)
    videoLength = random.randint(660, 841)
    prettyPrint(bcolors.OKBLUE, "Expected video length is {}".format(datetime.timedelta(seconds=videoLength)))

    # A list of which clips to use and how long the video is currently
    clipPaths = []
    totalLength = 0
    
    # Randomly selecting clips to add until the video is long enough
    while (totalLength < videoLength):
        newChoice = fullPath("data/sync_data/{}".format(random.choice(os.listdir(fullPath("data/sync_data")))))

        if newChoice not in clipPaths:
            try:
                totalLength += float(os.popen("ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 {}".format(newChoice)).read())
                clipPaths.append(newChoice)
            except Exception as e:
                prettyPrint(bcolors.WARNING, "Exception thrown, continuing with process. Exception: {}".format(e))
            
    
    # Just some output for the user
    prettyPrint(bcolors.OKBLUE, "Actual video length is {} and contains {} videos. All file paths are listed below".format(datetime.timedelta(seconds=int(totalLength)), len(clipPaths)))
    # Logs the video files for future reference
    logString = ""
    spacing = len(str(datetime.datetime.now())) + 4
    for path in clipPaths:
        logString += "{} || ".format(path)
        logString += "\n"
        for x in range(spacing):
            logString += " "
    prettyPrint(bcolors.ENDC ,logString)

    # Edits the video together
    startTime = time.perf_counter()

    # Creates a list of the input files for FFMPEG
    with open(fullPath("inputPaths.txt"), "a") as inputPathFile:
        ouputString = ""
        for inputPath in clipPaths: 
            ouputString += "file '{}' \n".format(inputPath)
        inputPathFile.write(ouputString)

    # Finally edits the clips togeather
    vidIndex = len(os.listdir(fullPath("/data/output"))) + 1
    prettyPrint(bcolors.ENDC, os.popen("ffmpeg -f concat -safe 0 -i {} -c copy {}".format(fullPath("inputPaths.txt"), fullPath("data/output/video_{}.mp4".format(vidIndex)))).read())
    os.remove(fullPath("inputPaths.txt"))

    # A little alert to let the user know the function is over and how long it took
    endTime = time.perf_counter()
    prettyPrint(bcolors.OKGREEN, f"Collected clips and edited video. Process took {endTime - startTime:0.4f} seconds")


# A little bit of structure. Allows me to call `videoEditor.py GenerateVideo` from the command line
if __name__ == '__main__':
   globals()[sys.argv[1]]()
