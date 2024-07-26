# sixel-nixel
Tools for processing results from a certain unnamed database.

This is a set of one-off scripts that were written to support a volunteer research effort. The group had acquired a dataset that was presented in a particularly ungainly format: human-readable plaintext results of a complex database query. Because of the way data was interleaved in each record, it couldn't easily be parsed with OpenRefine. See the test data in `test_data/input/sixel-nixel-raw-data.txt` for an example of this formatting.

The project consists of:
- `record.proto` - An object schema representing the information contained in each record. This is written in the Protocol Buffers schema definition language, which I chose because of my experience using it in my commercial work. For various reasons (implementation quirks, specificity of toolset, incompatibilities with JSON), I would strongly consider choosing JSON Schema or JSON TypeDef for ease of use in the future. Whatever definition language is used, a well-documented object schema goes a long way towards creating a usable, testable, and maintainable workflow.
- `raw_to_flattened.py` - First stage of data processing: collapse human-readable database query results into a single line for ease of processing.
- `flattened_to_record.py` - Second stage of data processing: for each input line consisting of a "flattened" plaintext record, convert it into a line of JSON corresponding to the object schema.
- `filter_records.py` - Optional third stage of processing. For each input line consisting of a JSON record, emit the line or filter it out based on a Python fragment passed in by the command line. I chose this model because the volunteer group was familiar with python, and the 'emit/filter' pattern corresponds to a usage pattern I'm familiar with from working with Flume (a.k.a. Beam, a differed execution framework similar to Spark). For a more robust approach, one could convert the json lines into a proper json list, and filter the records with jq.

Taken together, they represent a modest but hopefully effective example of how to create a workflow to manage ungainly data from aggregate sources.

```
Usage:

# Convert raw pretty-formatted database query result into a 'flattened' result, one record per line of text.
python3 raw_to_flattened.py test_data/input/sixel-nixel-raw-data.txt test_data/output/sixel-nixel-flattened.actual.txt

# Convert the flattened database query result into json or text proto strings, one record per line.
# default format: json lines.
python3 flattened_to_record.py test_data/output/sixel-nixel-flattened.actual.txt test_data/output/sixel-nixel-testdata.actual.jsonlines

# Example usage for pipe-and-filter of records in the shell.
# This pattern generalizes well to certain deferred execution frameworks.
# Code fragments can access input data via 'record' (dictionary representing
json) or 'record_proto' (proto wrapper object)
CODEFRAGMENT_EMIT_EVEN_RECORDS="if record['record_num'] %2 == 0: to_emit = True"

# filter json records
python3 filter_records.py --exec "$CODEFRAGMENT_EMIT_EVEN_RECORDS" --input_filename ./test_data/output/sixel-nixel-testdata.actual.jsonlines --output_filename ./test_data/output/sixel-nixel-testdata.filtered-even.jsonlines

```
