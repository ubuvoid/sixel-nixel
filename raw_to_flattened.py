# raw_to_flattened.py

import argparse

# usage: python3 row_to_flattened.py infile outfile

# infile: filename of a multi-line query result txt.

# outfile: filename to write a a flattened version of the input, where each
# record occupies exactly one line, consisting of the record's lines from the
# input file concatenated together with escaped '\\n' sequences.

sentinel_linemarker = "\\n"

def starts_with_digit(instring):
    return instring[:1].isdigit()

def flatten_instream_to_outstream(instream, outstream):
    # first, read ahead past the header, to the first record line. this is the
    # first line that begins with a digit.
    to_emit = ""
    while True:
        line = instream.readline()
        if not line:
            break  # end of file.
        if starts_with_digit(line):
            to_emit = line.replace("\n", sentinel_linemarker)
            break  # exit read-loop, 'to_emit' contains first line of record.

    # if we're here, and to_emit is empty, it means we hit the end of the file.
    if not to_emit:
        return

    # if we're here, then to_emit contains the first record, in progress.
    # loop through to the end.
    while True:
        line = instream.readline()
        if not line:
            break  # end of file.
        if starts_with_digit(line):
            # line is the start of a new record. emit the old one.
            outstream.write(to_emit + "\n")
            to_emit = ""
        # then, add the contents of the current line to the entry in progress.    
        to_emit = to_emit + line.replace("\n", sentinel_linemarker)

    # emit the final entry.
    outstream.write(to_emit + "\n")


def flatten_by_filename(input_filename, output_filename):
    infile = open(input_filename, 'r')
    outfile = open(output_filename, 'w')

    flatten_instream_to_outstream(infile, outfile)

    outfile.close()
    infile.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="raw_to_flattened")
    parser.add_argument("input_filename", metavar="input_filename", type=str,
            help="filename of l-n query result.")
    parser.add_argument("output_filename", metavar="output_filename", type=str,
            help="filename of output file (single line per record).")
    args = parser.parse_args()

    flatten_by_filename(args.input_filename, args.output_filename)    
