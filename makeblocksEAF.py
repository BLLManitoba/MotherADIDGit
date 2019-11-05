import subprocess as sp

import csv
import os, glob, shutil
import sys
import random
import re
import datetime
import zipfile
import shutil
# from pydub import AudioSegment #insatll mpeg
from multiprocessing import Process
import pympi

input_dir = 'S:\Soderstrom-Lab\CurrentStudies\MotherBabyAffectRating\InputFiles'
file_names = []
for wav_file in glob.iglob('S:\Soderstrom-Lab\CurrentStudies\MotherBabyAffectRating\InputFiles' + os.sep + '*.wav'):
    file_names.append(wav_file.replace(input_dir + os.sep, "").replace(".wav", ""))
    #print "file names are: ", file_names

output_dir1 = 'output_eafs2'
output_dir_tmp = 'output_eafs'
program_path = os.getcwd()
print "program path - ", program_path
if not os.path.exists(output_dir_tmp):
    os.mkdir(output_dir_tmp)
for file_name in file_names:
    if not os.path.exists(os.path.join(output_dir_tmp, file_name)):
        os.mkdir(os.path.join(output_dir_tmp, file_name))
    eafob = pympi.Elan.Eaf(os.path.join(input_dir, file_name + ".eaf"))
    # wav_file = AudioSegment.from_wav( os.path.join(input_dir,file_name+".wav"))

    tier_names = eafob.get_tier_names()
    regex = re.compile("FA*")
    tier_names = list(filter(regex.match, tier_names))
    print("tier names are: ", tier_names)
    start_positions = []
    for tier_name in tier_names:
        print "curr tier name = ", tier_name
        if not os.path.exists(os.path.join(output_dir_tmp, file_name, tier_name)):
            os.mkdir(os.path.join(output_dir_tmp, file_name, tier_name))
        xds = eafob.get_annotation_data_for_tier('xds@' + tier_name)
        tier_info = eafob.get_annotation_data_for_tier(tier_name)
        print "tier_info = ", tier_info
        # for index, annotation in enumerate(eafob.get_annotation_data_for_tier(tier_name)):
        for index in range(len(xds)):
            #annotation = tier_info[index]
            # if index<len(xds):
            #print "lenth of xds tier: ", len(xds[index])
            if len(xds[index]) >= 2:

                tag = (xds[index])[2]
                #print "tag: ", tag
                if tag == 'A' or tag == 'C' or tag == 'T' or tag == 'B':
                    start_time =((xds[index])[0])
                    #print "start time: ", start_time
                    end_time = ((xds[index])[1] - (xds[index])[0]) / 1000.0
                    #print "end time: ", end_time
                    # if annotation[1] != xds[index-1][1]:

                    #print("xds index: ", xds[index][1])
                    #print("annotation: ", annotation[1])
                    # exit()
                    #print("xds index 2: ", xds[index][2])
                    # wav_file_tmp = wav_file[annotation[0]-1000:annotation[1]+1000]
                    # wav_file_tmp.export(os.path.join(output_dir,file_name,tier_name,str(annotation[0])+"_"+str(annotation[1])+".wav"), format='wav')
                    command = ["ffmpeg",
                               "-ss",
                               str((xds[index])[0] / 1000.0),
                               "-t",
                               str(end_time),
                               "-i",
                               os.path.join(program_path, input_dir, file_name + ".wav"),
                               os.path.join(program_path, output_dir_tmp, file_name, tier_name,
                                            str((xds[index])[0]) + "_" + str((xds[index])[1]) + "_" + tag + ".wav"),
                               "-y",
                               "-loglevel",
                               "error"]

                    command_string = " ".join(command)
                    #print(command_string)
                    #
                    pipe = sp.Popen(command, stdout=sp.PIPE, bufsize=10 ** 8)
                    out, err = pipe.communicate()
                    #print(err)
                    start_positions.append((xds[index])[0])

    start_positions = sorted(start_positions, key=int)
    #print "start positions: ", start_positions
    tmp = 0
    considered_position = 0
    chunk = 1
    while tmp < len(start_positions):
        if considered_position == 0:
            considered_position = start_positions[tmp]
        for wav_file in glob.iglob(os.path.join('output_eafs', file_name, '**', str(start_positions[tmp]) + "_*.wav")):
            if start_positions[tmp] - considered_position > 1 * 60 * 1000:
                chunk += 1
                considered_position = start_positions[tmp]
            print(str(chunk) + ':' + wav_file)
            tier_name = wav_file.split(os.sep)[2]
            copy_file_name = wav_file.split(os.sep)[3]
            if not os.path.exists(os.path.join(output_dir1, file_name, 'chunk' + str(chunk), tier_name)):
                os.makedirs(os.path.join(output_dir1, file_name, 'chunk' + str(chunk), tier_name))
            shutil.copy(wav_file, os.path.join('output_eafs2', file_name, 'chunk' + str(chunk), tier_name, copy_file_name))

        tmp += 1
