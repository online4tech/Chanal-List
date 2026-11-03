# Plugins restructure rollback snapshot

- Baseline branch: `main`
- Baseline commit: `001878372c88ca4f5f3094ea5ac36334d0decca6`
- Full-project rollback branch: `backup-plugins-restructure-20261103`
- Working branch: `plugins-flat-grid`
- Captured: 2026-11-03

The rollback branch preserves the complete repository tree at the baseline commit, including all data, published assets, and configuration files. This folder contains byte-for-byte copies of the Control Center source, existing stylesheet, built HTML entrypoint, React entrypoint, global styles, package manifest, and Vite configuration.

The original minified JavaScript bundle and large catalog are preserved in the full-project rollback branch, rather than duplicated in this folder.

A live browser screenshot was not available in this execution environment. The original published HTML/JS/CSS remain intact in the rollback branch and were used as the code-level UI snapshot.

Restore the complete project by resetting the target branch to the baseline commit above, or restore individual files from the rollback branch.
