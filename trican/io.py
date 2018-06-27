"""
File I/O (input/output) functions
"""

import numpy as np
import pandas as pd
from trican.objects import TreeringSeries, TreeringChronology


def read_heidelberg(filename, seriestype='Series'):
    # Heidelberg Format (.fh)

    # list of treering series:
    series = []

    # read full input file
    # full = np.genfromtxt(filename, delimiter='\n', dtype=str)
    # nr = np.where([lis=='HEADER:'])[1]

    # use pandas to read full input file
    df = pd.read_csv(filename, header=None)

    # location of header strings:
    head = df.loc[df[0].str.contains('HEADER')].index
    datastr = df.loc[df[0].str.contains('DATA')].index

    # loop over multiple treering series if present
    for nr in range(len(head)):

        header = df.loc[head[nr]:datastr[nr]]

        begindate = int(header.loc[header[0].str.contains('DateBegin')].
                        values[0][0].split('=')[1])
        enddate = int(header.loc[header[0].str.contains('DateEnd')].
                      values[0][0].split('=')[1])
        length = int(header.loc[header[0].str.contains('Length')].
                     values[0][0].split('=')[1])
        unit = header.loc[header[0].str.contains(
            'Unit')].values[0][0].split('=')[1]
        key = header.loc[header[0].str.contains(
            'KeyCode')].values[0][0].split('=')[1]
        datatype = header.loc[header[0].str.contains(
            'DATA')].values[0][0].split(':')[1]

        # check dates
        if begindate + length - 1 != enddate:
            raise RuntimeError('Dates of Series %s in file %s do not match!'
                               % (key, filename))

        # determine length of actual data in file
        if nr == len(head)-1:
            # last series data goes until end
            end = len(df)
        else:
            # series data goes until one before next header
            end = head[nr+1]-1

        # empty data array
        data = np.empty(0)
        for line in df.loc[datastr[nr]+1:end].values:
            data = np.append(data, np.array(line[0].split()).astype(int))

        # remove trailing zeros and check for zero values
        zer = np.where(data == 0)[0]
        if len(zer) > 0:
            assert zer.max() == len(data)-1, 'Zeros not at the end of file'
            assert all(np.diff(zer)), 'Zero values not concatenated'
            data = np.delete(data, zer)

        if datatype == 'Single':
            sampledepth = None
        elif datatype == 'Double':
            sampledepth = data[1::2]
            data = data[0::2]
            assert len(data) == len(sampledepth),\
                'length of data and depth do not match'
        elif datatype == 'Quad':
            raise RuntimeError('Heidelberg QUAD format not implemented yet!')

        # give header as array to treeringseries
        header = np.squeeze(header.values)

        if seriestype == 'Series':
            # initialize treering object
            tree = TreeringSeries(filename,
                                  header,
                                  begindate,
                                  enddate,
                                  unit,
                                  key,
                                  data,
                                  sampledepth)

            series.append(tree)
        elif seriestype == 'Chronology':
            # initialize treering chronology
            series = TreeringChronology(filename,
                                        header,
                                        begindate,
                                        enddate,
                                        unit,
                                        key,
                                        data,
                                        sampledepth)

    return series


def write_heidelberg(series, filename=None):

    if filename is None:
        if hasattr(series[0], 'corrected_data'):
            subfix = '_corrected.fh'
        elif hasattr(series[0], 'fitted_data'):
            subfix = '_fitted.fh'

        filename = series[0].orgfile.split('.fh')[0] + subfix

    dataformat = '%6d%6d%6d%6d%6d%6d%6d%6d%6d%6d\n'

    with open(filename, 'w') as out:
        for tree in series:

            if hasattr(tree, 'corrected_data'):
                header = np.append(tree.orgheader[:-1],
                                   'CorrectionFactor=%.5f' % tree.factor)
                header = np.append(header,
                                   'CorrectionOffset=%.5f' % tree.offset)
                header = np.append(header, tree.orgheader[-1])
                outdata = tree.corrected_data

            elif hasattr(tree, 'fitted_data'):
                header = np.append(tree.orgheader[:-1],
                                   'FittingFactor=%.5f' % tree.fitfactor)
                header = np.append(header,
                                   'ChronologyUsed=%s' % tree.chronokey)
                header = np.append(header, tree.orgheader[-1])
                outdata = tree.fitted_data

            for head in header:
                # write header
                out.write(head + '\n')

            # write data
            for line in np.arange(0, len(outdata), 10):

                data = outdata[line:line+10]

                if len(data) < 10:
                    dif = 10-len(data)
                    data = np.append(data, np.zeros(dif))
                elif len(data) > 10:
                    raise RuntimeError('Something went wrong writing data')

                out.write(dataformat % tuple(data))
