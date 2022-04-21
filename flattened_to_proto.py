# flattened_to_proto.py

import argparse
import re
import record_pb2
from record_pb2 import ColumnType as ColumnType
import google.protobuf.text_format as text_format

sentinel_linemarker = "\\n"

def line_to_recordproto(recordline):
    # inflate flattened l-n record to a Record proto.

    # rudimentary validation
    if not recordline:
        print(
            "line_to_recordproto: returning empty proto for empty input.")
        return record_pb2.Record()

    # first, pop out the record into multiple lines for easy editing.
    lines = recordline.split(sentinel_linemarker)

    # in the first row of the record, every column is represented.
    # columns are separated by blocks of two or more spaces. iterate through
    # the first line to determine where those column boundaries occur.
    firstline = lines[0]

    if firstline[0].isspace():
        print(
            "malformed input -- first line of record should begin with "
            + "record number.")
        return record_pb2.Record()

    # fields are particular to the query requested, but in
    # the case of sample file the order of columns was as follows:
    col_labels = [
        ColumnType.RECORD_NUMBER,
        ColumnType.DEBTOR,
        ColumnType.ADDRESS,
        ColumnType.FILING,
        ColumnType.CREDITOR
    ]

    # keep track of characters on which columns start.
    col_starts = []
    # first column (RECORD_NUMBER) starts at character 0.
    col_starts.append(0) 
    in_column = True

    ind = 1  # already verified 0.
    while ind < len(firstline):
        is_space = firstline[ind].isspace()
        if (not in_column) and (not is_space):
            # "low to high" edge, we just jumped from 'padding' to 'new
            # column'.
            in_column = True
            col_starts.append(ind)
        elif is_space and firstline[ind - 1].isspace():
            # if we've hit two spaces in a row, we can consider the col to be
            # complete, and we're headed back into 'padding'.
            in_column = False

        # increment i for the next go-round.
        ind += 1

    # validate the column mapping:
    if len(col_starts) != len(col_labels):
        print(
            "error -- encountered unexpected number of columns."
            + " num labels: " + str(len(col_labels))
            + " num columns: " + str(len(col_starts))
            + " -- expected equal values.")
        return record_pb2.Record()

    # if we're here, col_starts now provides a guide to slicing up the
    # record into columns which can be independently parsed.

    col_lines_map = {}  # ColumnType -> list of lines (cropped from record).
    num_cols = len(col_labels)

    for i in range(num_cols):
        col_lines_map[col_labels[i]] = []  # placeholder list.

    # copy column line fragments to col_lines_map.
    for line in lines:
        for col_ind in range(num_cols):
            col_start = col_starts[col_ind]
            col_afterend = (
                    # final column ends where 'line' ends.
                    # otherwise, columns end at the start of next col.
                    len(line) if col_ind == (num_cols - 1) else
                    col_starts[col_ind+1]
            )

            # if col_start or col_afterend is out of bounds, str[a:b]
            # substring syntax will seamlessly fall back to empty or truncated
            # string.
            cropped_line = line[col_start:col_afterend].strip()

            col_lines_map[col_labels[col_ind]].append(cropped_line)

    # if we're here, each line of the record has been sliced into columns, and
    # the columns are collected in col_lines_map indexed by ColumnType enum.
    # leading and trailing whitespace has been trimmed.

    # now, unpack individual columns.
    record_proto = record_pb2.Record()

    # record number ("No.")
    recordnum_lines = col_lines_map[ColumnType.RECORD_NUMBER]
    try:
        # record number is limited to a single entry on the first line.
        # format: "1.", "36.", etc.
        match_str = re.search('^[0-9]*', recordnum_lines[0]).group(0)
        record_proto.record_num = int(match_str)
    except Exception as e:
        print("error -- couldn't parse record num: " + str(e))
        return record_pb2.Record()

    # Debtor
    debtor_lines = col_lines_map[ColumnType.DEBTOR]
    debtor_starting_linenos = []
    for ind, debtor_line in enumerate(debtor_lines):
        # skip empty lines.
        if not debtor_line:
            continue

        if "LexID(sm):" in debtor_line:
            # metadata for most recent debtor encountered in the column.
            # remove prefix and store number part as string.
            try:
                lexid_str = re.search(
                        'LexID\(sm\):([0-9]*)', debtor_line).group(1)

                # retrieve most recently-added debtor proto in list.
                debtor_proto = record_proto.debtors[-1]
                debtor_proto.lex_id = lexid_str
            except Exception as e:
                print("error -- couldn't parse debtor lex_id: " + str(e))
                return record_pb2.Record()
        elif ", " in debtor_line:
            # new debtor name.
            debtor_starting_linenos.append(ind)
            name_split = debtor_line.split(", ")

            debtor_proto = record_proto.debtors.add()
            debtor_proto.name = debtor_line
            debtor_proto.parsed_surname = name_split[0]
            if len(name_split) > 1:
                debtor_proto.parsed_forenames = name_split[1]
        else:
            undivided_name = debtor_line.strip()
            if undivided_name:
                debtor_starting_linenos.append(ind)
                debtor_proto = record_proto.debtors.add()
                debtor_proto.name = undivided_name

    # Address
    # addresses, unlike other columns, are scoped within debtors. to properly
    # match the address to the debtor, we must compare line numbers across
    # columns.
    address_lines = col_lines_map[ColumnType.ADDRESS]
    num_debtors = len(record_proto.debtors)

    # debugging! uncomment if these are useful....
    # print("debtor starting indices: ")
    # for ind, starting_lineno in enumerate(debtor_starting_linenos):
    #     print(str(ind) + " " + str(starting_lineno))
    # print("num_debtors: " + str(num_debtors))

    for line_ind, address_line in enumerate(address_lines):
        # skip empty lines.
        if not address_line:
            continue
        
        current_debtor = num_debtors - 1
        while current_debtor > 0:
            if debtor_starting_linenos[current_debtor] <= line_ind:
                break  # last debtor beginning on or before this line.
            current_debtor -= 1

        if current_debtor < 0:
                print(
                        "error -- couldn't match address to debtor: "
                        + "line_ind: " + str(line_ind) + " "
                        + "address lines: " + str(len(address_lines)) + " "
                        + "current_debtor: " + str(current_debtor) + " "
                        + "address line: " + address_line)
                return record_pb2.Record()
        
        # if we're here, current_debtor contains the appropriate debtor index
        # for this address line.
        #
        # todo: parsing for addr components.
        addr_proto = record_proto.debtors[current_debtor].address
        addr_proto.raw_lines.append(address_line)

    # Filing
    filing_lines = col_lines_map[ColumnType.FILING]
    filing_info_proto = record_proto.filing_info
    header_done = False

    for ind, filing_line in enumerate(filing_lines):
        if not filing_line:
            continue

        if filing_line.isupper():
            # upper-case lines describe filing categories. a category line
            # begins a new filing component, and ends the header if we were
            # still in the header.
            header_done = True
            # create a new component message at the end of the list, and set
            # the category.
            component_proto = filing_info_proto.components.add()
            component_proto.category = filing_line

        elif "Filing Date:" in filing_line:
            try:
                # TODO: parsing/cleanup of raw date.
                fd_str = re.search('Filing Date:(.*)$', filing_line).group(1)

                if header_done:
                    filing_info_proto.components[-1].raw_filing_date = fd_str
                else:
                    filing_info_proto.raw_filing_date = fd_str
            except Exception as e:
                print("error -- couldn't parse filing date: " + str(e))
                return record_pb2.Record()

        elif "Amount:" in filing_line: 
            try:
                amt_str = re.search('Amount:(.*)$', filing_line).group(1)
                filing_info_proto.amount = amt_str

                amt_str = amt_str.replace('$', '')
                amt_str = amt_str.replace(',', '')
                
                dollar_str = re.search('^([0-9]*)', amt_str).group(1)
                filing_info_proto.amount_usd = int(dollar_str)
            except Exception as e:
                print("error -- couldn't parse amount: " + str(e))
                return record_pb2.Record()

        elif "Filing Number:" in filing_line:
            if not header_done:
                print(
                        "error -- encountered filing number before "
                        + "header completed: " + filing_line)
                return record_pb2.Record()

            try:
                fn_str = re.search('Filing Number:(.*)$', filing_line).group(1)
                filing_info_proto.components[-1].filing_number = fn_str
            except Exception as e:
                print("error -- couldn't parse filing number: " + str(e))
                return record_pb2.Record()

        elif "Filing Office:" in filing_line:
            if not header_done:
                print(
                        "error -- encountered filing office before "
                        + "header completed: " + filing_line)
                return record_pb2.Record()
            try:
                office_str = re.search(
                        'Filing Office:(.*)$', filing_line).group(1)
                filing_info_proto.components[-1].filing_office = office_str
            except Exception as e:
                print("error -- couldn't parse filing office: " + str(e))
                return record_pb2.Record()

        elif "Certificate Number:" in filing_line:
            try:
                certnum_str = re.search(
                        'Certificate Number:(.*)$', filing_line).group(1)
                filing_info_proto.certificate_number = certnum_str
            except Exception as e:
                print("error -- couldn't parse certificate no: " + str(e))
                return record_pb2.Record()

        else:
            print("error -- unrecognized filing line: " + filing_line)

    # Creditor
    creditor_lines = col_lines_map[ColumnType.CREDITOR]
    seen_creditor = False
    for ind, creditor_line in enumerate(creditor_lines):
        if not creditor_line:
            continue

        if seen_creditor:
            print("error -- unexpected redundant creditor line: "
                    + creditor_line)
            return record_pb2.Record()

        if not creditor_line.isupper():
            print("error -- expected upper-case creditor line, found: "
                    + creditor_line)
            return record_pb2.Record()

        # if we're here, then this is the properly-formatted creditor line.
        record_proto.creditor.name = creditor_line
        seen_creditor = True

    # if we're here, the proto is now fully assembled.
    return record_proto

def convert_stream(instream, outstream):
    while True:
        line = instream.readline()
        if not line:
            break  # end of file.
        record_proto = line_to_recordproto(line)
        record_textproto = text_format.MessageToString(
                record_proto, as_one_line=True, as_utf8=True)
        outstream.write(record_textproto)
        outstream.write("\n")

    # if we're here, all the lines have been converted. ok to return.


def convert_flattened_file(input_filename, output_filename):
    infile = open(input_filename, 'r')
    outfile = open(output_filename, 'w')

    convert_stream(infile, outfile)

    outfile.close()
    infile.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="flattened_to_proto")
    parser.add_argument("input_filename", type=str,
            help="filename of flattened l-n query text result (one record per "
            + "line, with escaped newlines).")
    parser.add_argument("output_filename", type=str,
            help="filename to write a file where each line is a text-format "
            + "protocol buffer representing the corresponding record.")
    args = parser.parse_args()

    convert_flattened_file(args.input_filename, args.output_filename)    
