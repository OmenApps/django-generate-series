# History

## 1.0.0 (2022-04-27)

  * Added ability to generate cartesian products with a QuerySet or an iterable.
  * Changed license to MIT.
  * When generating sequences of ranges, if `span` is not provided, it will default to the value of `step` if provided, or 1 if not.

Breaking changes

  * All arguments are now keyword-only.

## 0.4.3 (2022-04-27)

  * Add ability to specify the span from lower to upper values in each term for ranges.

## 0.4.0 (2022-04-27)

Breaking changes

  * Modify API taking into consideration recommendations from Adam Johnson.

## 0.3.0 (2022-04-25)

Breaking changes

  * Changed from using `id` as the sequence value to using the `term` field.

## 0.2.1 (2022-04-25)

  * Implemented all PRs from adamchainz.
  * Improve test matrix.
  * Cleanup unused code and comments.

## 0.2.0 (2022-04-23)

  * Basic package functionality is implemented.
  * Tests have been added.
  * Initial documentation is added.

## 0.1.0 (2022-02-08)

* Built initial readme entry to start documenting project goals.
