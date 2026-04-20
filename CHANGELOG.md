# Changelog

All notable changes to this project will be documented in this file.

## [0.7.0] - 2026-04-20

### Added

- Display LLM-generated group names and descriptions in the `Groups` tab.

## [0.6.2] - 2026-04-18

### Fixed

- Fixed Groups tab loading incorrect CSV file for group data.

## [0.6.1] - 2026-04-04

### Changed

- Sort by `Detected` date (newest first) by default in the `Citation Changes` tab.

## [0.6.0] - 2026-03-21

### Added

- Add a `Group` tab to display community detection results of the citation network.

### Changed

- Improve readability of node labels in the `Network` tab by adding a white outline to the text.

## [0.5.1] - 2026-03-15

### Changed

- Change the sort order in the `Citation Changes` tab from ascending to descending by date.
- Store PEP metadata as node attributes in the NetworkX `DiGraph` . (internal)
- Add the Python-Version metadata field for PEPs.

## [0.5.0] - 2026-03-08

### Added
- Add a `Citation Changes` tab to show newly detected citation relationships between PEPs.
- Add data documentation ( `data/README.md` ) and a `Data` link in the dashboard header.

### Changed
- Detect and record changes in citation relationships during the data preprocessing step.
- Show hover descriptions for the node size options in the `Network` tab.

## [0.4.0] - 2026-03-03

### Added
- Store data retrieval date and data check date separately.
- Display the data check date in the UI.

### Changed
- Skip metrics recomputation when no citation or metadata changes are detected.
- Update the layout of the data updated date in the dashboard.
- Update browser tab title to reflect application name.

## [0.3.0] - 2026-02-28

### Added
- Added the `PEP Metrics` tab.
- Enabled node size scaling by PageRank in the Network tab.

### Changed
- Moved metric calculations to the scheduled data processing script.

## [0.2.1] - 2026-02-26

### Changed
- Improve responsiveness when tapping a node in the network graph.

## [0.2.0] - 2026-02-26

### Added
- Added the `Network` tab.
- Added links to the User Guide in the header and within each tab.
- Added links to the Changelog in the header.
- Added scheduled data update processing.

## [0.1.0] - 2026-02-20

### Added
- Initial release
