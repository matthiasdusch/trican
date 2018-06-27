"""
Classes and other stuff
"""

import numpy as np


class TreeringData:

    def __init__(self,
                 orgfile,
                 orgheader,
                 begin,
                 end,
                 unit,
                 key,
                 data,
                 sampledepth):

        # most important attributes have to be initialized
        self.orgfile = orgfile
        self.orgheader = orgheader
        self.begin = begin
        self.end = end
        self.unit = unit
        self.key = key
        self.data = data
        self.sampledepth = sampledepth


class TreeringSeries(TreeringData):

    # Method to apply a correction factor and offset
    def altitude_correction(self, factor=1., offset=0.):
        self.factor = factor
        self.offset = offset
        self.corrected_data = self.data * self.factor + self.offset

    def altitude_fitting(self, chronology):
        # some sanity checks
        assert self.unit == chronology.unit, 'Units do not match'
        assert self.begin > chronology.begin, 'Begin date not in chronology'
        assert self.begin < chronology.end, 'Begin date not in chronology'
        assert self.end > chronology.begin, 'End date not in chronology'
        assert self.end < chronology.end, 'End date not in chronology'
        assert self.begin < self.end, 'Wrong dates'

        # calcualte fitting factor
        self.fitfactor = chronology.mean(self.begin, self.end)/self.data.mean()

        # fit data to bias==0
        self.fitted_data = self.data * self.fitfactor

        # store the name of the used chronology for output
        self.chronokey = chronology.key


class TreeringChronology(TreeringData):

    # calculate the variance of the chronology for a certain time period
    def variance(self, t1, t2):
        # timesteps of chronology
        chrono = np.arange(self.begin, self.end+1)
        # timesteps of requested period
        period = np.arange(t1, t2+1)

        # return variance
        return self.data[np.isin(chrono, period)].var()

    # calculate the chronology mean for a certain time period
    def mean(self, t1, t2):
        # timesteps of chronology
        chrono = np.arange(self.begin, self.end+1)
        # timesteps of requested period
        period = np.arange(t1, t2+1)

        # return mean
        return self.data[np.isin(chrono, period)].mean()
