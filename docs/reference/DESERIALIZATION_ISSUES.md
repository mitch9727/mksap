b# Deserialization Issues and Fixes

## Summary

Some question payloads could not be deserialized because fields that were modeled as strings
occasionally arrive as structured nodes. This caused errors like:

```
invalid type: map, expected a string
```

The failures were most commonly triggered by `options[].text` containing a rich node tree
instead of a plain string.

## Root Cause

The API response is not strictly uniform. Examples observed:

- `options[].text` can be either:
  - A plain string (most questions), or
  - An object with `type` and `children` nodes (for subscript, formatting, or mixed content).
- `objective` can be an HTML object or a plain string.
- `stimulus`, `prompt`, `exposition`, `keypoints`, and `references` can be null.

The original model assumed `options[].text` was always a string, which caused deserialization
to fail when a node object appeared.

## Fix Implemented

We updated the API model to tolerate both formats:

- `ApiAnswerOption.text` now accepts a string or a node.
- Node values are converted to text by recursively walking `children`.
- `objective` accepts either a `__html` object or a plain string.
- `stimulus`, `prompt`, `exposition`, `keypoints`, and `references` accept null.

These changes are implemented in:

- `src/models.rs`

## Recovery

After the fix, the `retry-missing` command re-fetched the previously failing IDs and
successfully saved their JSON output.

## Historical Failed IDs

The original set of failed IDs is preserved here for reference:

- `mksap_data_failed/deserialize_ids.txt`

If these need to be rechecked in the future, the list can be used to target them directly.
