# filter_records.py

import argparse
import record_pb2
import sys
import google.protobuf.json_format as json_format
import google.protobuf.text_format as text_format

# usage:
# filter_records.py --exec EXEC
#                   [--input_mode {textproto,json}]
#                   [--output_mode {textproto,json}]
#                   [--input_filename INPUT_FILENAME]
#                   [--output_filename OUTPUT_FILENAME]

# EXEC is a block of python which has access to the locals 'record_proto' and
# 'to_emit'. EXEC is executed once per input record. if 'to_emit' evaluates to
# True after the block is run, then the record is included in the output.
#
# Do *NOT* write to stdout in EXEC.
#
# By default, reads json records from stdio, one record per line, and writes to
# stdout.
#
# If input_filename is supplied, reads input from that file instead.
# If output_filename is supplied, writes to that file instead.


# print to stderror. this allows us to use stdout for main output, if specified
# by the command line args.
#
# !!! for debugging messages, error logs, etc, ONLY use this -- not print() !!!
def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def line_to_recordproto(line, input_mode):
    record_proto = record_pb2.Record()
    if input_mode == "textproto":
        text_format.Parse(line, record_proto) 
    elif input_mode == "json":
        json_format.Parse(line, record_proto)
    else:
        eprint("Unrecognized input format")
        return None

    return record_proto


def filter_lines(instream, outstream, input_mode, output_mode, args):
    while True:
        line = instream.readline()
        if not line:
            break  # end of input.
        record_proto = line_to_recordproto(line, input_mode)

        string_to_execute = args.exec
        if not string_to_execute:
           eprint("!!! no execution block found !!!")
           return

        exec_locals = {}
        exec_locals['to_emit'] = False
        exec_locals['record_proto'] = record_proto

        exec(string_to_execute, {}, exec_locals)

        # if we're here, then the executed block has set 'to_emit' to reflect
        # whether this line should be included in the output.

        if exec_locals['to_emit']:
            line = ""

            if output_mode == "textproto":
                line = text_format.MessageToString(
                        record_proto, as_one_line=True)
            elif output_mode == "json":
                line = json_format.MessageToJson(
                        record_proto, indent=None,
                        preserving_proto_field_name=True)
            else:
                eprint("!!! unexpected output_mode: " + output_mode)
                return

            outstream.write(line)
            outstream.write("\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=
        "filters record protos based on a boolean expression, "
        + "where 'record_proto' contains a parsed record_pb2 Record object "
        + "representing a given record.")

    parser.add_argument("--input_mode", type=str,
            choices=[
                "textproto",
                "json"
            ],
            help="format of input records. expects one record per line, in "
            + "the specified format (json, textproto). "
            + "default: json",
            default="json")

    parser.add_argument("--output_mode", type=str,
            choices=[
                "textproto",
                "json"
            ],
            help="if supplied, format to emit output records in. defaults to "
            + "the value of input_mode.")

    parser.add_argument("--exec", type=str,
            help="python block, to be executed once for each input record. "
            + "has access to two local variables: record_proto (a Record "
            + "proto object) and to_emit (a boolean). If to_emit is set to "
            + "True when the block is finished executing, then the record "
            + "will be included in output. Otherwise, it's filtered out. "
            + " *DO NOT* write to stdout.",
            required=True)

    parser.add_argument("--input_filename", type=str,
            help="filename of input records to evaluate. if not supplied, "
            + "reads from stdin.")

    parser.add_argument("--output_filename", type=str,
            help="filename to emit records which pass the filter. if not "
            + " supplied, writes to stdout.")
    args = parser.parse_args()
   
    # it's anyone's guess why they decided to overload the 'if' keyword for
    # ternaries, but here it is.
    input_mode = args.input_mode
    output_mode = args.output_mode if args.output_mode else input_mode

    # simply absurd. who designed this language?
    instream = sys.stdin if not args.input_filename else open(
            args.input_filename, 'r')
    outstream = sys.stdout if not args.output_filename else open(
            args.output_filename, 'w')

    filter_lines(instream, outstream, input_mode, output_mode, args)

    outstream.close()
    instream.close()

    eprint("done")
