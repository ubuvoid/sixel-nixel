# sixel-nixel
Tools for processing results from a fictitious database.

```
Usage:

# Convert raw pretty-formatted database query result into a 'flattened' result, one record per line of text.
python raw_to_flattened.py test_data/input/sixel-nixel-raw-data.txt test_data/output/sixel-nixel-flattened.actual.txt

# Convert the flattened database query result into json or text proto strings, one record per line.
# default format: json lines.
python flattened_to_record.py test_data/output/sixel-nixel-flattened.actual.txt test_data/output/sixel-nixel-testdata.actual.jsonlines

# for text proto:
python flattened_to_record.py test_data/output/sixel-nixel-flattened.actual.txt test_data/output/sixel-nixel-testdata.actual.textprotolines --output_mode=textproto

# Example usage for pipe-and-filter of records in the shell.
# This pattern generalizes well to certain deferred execution frameworks.
CODEFRAGMENT_EMIT_EVEN_RECORDS=" if record_proto.record_num %2 == 0: to_emit = True "

# filter json records
python filter_records.py --exec "$CODEFRAGMENT_EMIT_EVEN_RECORDS" --input_filename ./test_data/output/sixel-nixel-testdata.actual.jsonlines --output_filename ./test_data/output/sixel-nixel-testdata.filtered-even.jsonlines

# filter textproto records
python filter_records.py --exec "$CODEFRAGMENT_EMIT_EVEN_RECORDS" --input_filename ./test_data/output/sixel-nixel-testdata.actual.textprotolines --output_filename ./test_data/output/sixel-nixel-testdata.filtered-even.textprotolines --input_mode textproto --output_mode textproto

```
