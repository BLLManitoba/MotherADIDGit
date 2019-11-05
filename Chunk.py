import os
import wave
from numpy import fromstring, cumsum
import struct
from glob import glob


class Chunk(object):

    _parts_length = 1 # seconds

    def __init__(self, path, name, index):

        self.path = path
        self.name = name
        self.index = index

        self.clips = Chunk.get_clips(path)
        data, chans, width, rate, frames, clipslist = Chunk.merge_clips(self.clips)

        self.audio_data = data
        self.n_channels = chans
        self.sample_width = width
        self.sample_rate = rate
        self.bytes = len(data) # length in bytes
        self.seconds = self.bytes2sec(self.bytes)
        self.frames = frames

        self.clips_length_list = clipslist
        self.parts_length_list = self.get_parts_list()


    @classmethod
    def update_parts_length(cls, value):
        cls._parts_length = value


    # @utils.timer
    def get_parts_list(self):
        parts_list = []
        clip_ind = 0
        while clip_ind < len(self.clips_length_list):
            part_length = 0
            while part_length < self.sec2bytes(self._parts_length) and clip_ind < len(self.clips_length_list):
                part_length += self.clips_length_list[clip_ind]
                clip_ind += 1
            parts_list.append(part_length)

        return parts_list


    def get_startend_idcs(self):

        end = cumsum(self.parts_length_list)
        start = end - self.parts_length_list

        return zip(start, end)


    @staticmethod
    def get_clips(path):
        clips=[]
        for dir,_,filenames in os.walk(path):
            for filename in [f for f in filenames if f.endswith(".wav")]:
                clips.append(os.path.join(dir,filename))
            # clips = [clip for clip in os.listdir(path) if clip.endswith('.wav')]
            #     clips.extend(glob(os.path.join(sub_dir,'*.wav')))
        try:
            # clips = sorted(clips, key = lambda x: int(x[:-4]))
            clips = sorted(clips, key=lambda x:x.split(os.sep)[-1].split("_")[0])
        except:
            pass

        clips = [os.path.join(path, clip) for clip in clips]
        return clips


    @staticmethod
    def merge_clips(clips):

        raw_data = ''
        frames = 0
        clips_length_list = []
        for clip in clips:
            f = wave.open(clip, 'r')
            clip_bytes = f.readframes(-1)
            raw_data += clip_bytes
            clips_length_list.append(len(clip_bytes))
            frames += f.getnframes()
            if clip == clips[0]:
                n_channels, sample_width, sample_rate, _, _, _ = f.getparams()
            f.close()
        return raw_data, n_channels, sample_width, sample_rate, frames, clips_length_list

    # @utils.timer
    def convert_audio(self):

        bits = self.sample_width * 8
        dtype = 'int{}'.format(bits)
        norm = (2 ** bits) / 2.0 - 1

        if self.n_channels == 1:
            data = fromstring(self.audio_data, dtype) / norm
        elif self.n_channels == 2:
            data = fromstring(self.audio_data, dtype)[0::2] / norm
        else:
            data = False

        return data

    # @utils.timer
    def _convert_audio(self):

        assert self.sample_width in (1, 2)

        if self.sample_width == 1:
            fmt = '{}b'.format(self.frames)
            # maxint =
        elif self.sample_width == 2:
            fmt = '{}h'.format(self.frames)

        data = struct.unpack(fmt, self.audio_data)
        return data


    def bytes2sec(self, byte):
        secs = float(byte) / self.sample_rate / self.sample_width / self.n_channels
        return secs

    def sec2bytes(self, seconds):
        byte = seconds * self.sample_rate * self.sample_width * self.n_channels
        return int(byte)

