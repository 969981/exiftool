# ExifTool upstream sync/build/release

This repository automatically tracks the official [exiftool/exiftool](https://github.com/exiftool/exiftool) `master` branch. Local GitHub Actions controls are preserved under `.github/`. Code is mirrored from upstream without modifications. The upstream SHA is kept in `.github/sync/upstream-head.sha`.

## Triggers

- Every 10 minutes: query upstream and build only when the commit SHA changes.
- Manual workflow run: set `force_build=true` to rebuild and republish the mirrored revision.
- CI control changes on `master`: run the workflow and rebuild.

Changes are committed as descendants of the local branch; the script does not force-push. GitHub Actions built-in token pushes do not recursively trigger another workflow. It is normal for cron jobs to run late.

## What "build" means

ExifTool is implemented in Perl, not native C/C++. We run `perl Makefile.PL`, `make`, and `make test` on Linux/macOS, plus a smoke test on all platforms. Portable archives include ExifTool's command-line script, libraries, sample config files and documentation and **require a Perl interpreter**.

For Windows, the workflow additionally attempts a self-contained `exiftool.exe` with upstream's `windows_exiftool` script and PAR::Packer. This optional step is best-effort; it is uploaded only if it compiles and passes a version check. The cross-platform source distributions are still published if the Windows EXE toolchain is unavailable. We do not represent portable Perl script archives as native executables.

## Release naming

Each upstream revision has a unique pre-release tag: `exiftool-VERSION-UPSTREAM_SHA12`. It contains Windows portable ZIP and Linux/macOS tarballs, with the EXE only when successfully verified. The GitHub mirror commit is the release target. No new Release is made when upstream is unchanged, unless a user explicitly forces a rebuild.

## Development notes

- Workflow: `.github/workflows/auto-sync-release.yml`
- Synchronizer: `.github/scripts/sync-upstream.sh`
- Packager: `.github/scripts/package-portable.py`
- Official upstream packaging notes: `README`, `Makefile.PL`, `pp_build_exe.args`
- Preserve licenses, distinguish unofficial output from Phil Harvey's official binaries.
