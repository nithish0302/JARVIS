# Sidecar runtime release (`_internal`)

The PyInstaller onedir build of `jarvis-engine` produces a `_internal/`
support directory (~3.7GB, ~19.6k files) that must sit physically next to
the sidecar `.exe` at runtime. It is **not** bundled into the NSIS
installer (that would make the installer itself ~3.7GB) - instead
`apps/desktop/src-tauri/src/sidecar_setup.rs` downloads it from a GitHub
Release on the app's first launch and caches it next to the sidecar exe
for every launch after that.

## Current release

- **Tag**: `sidecar-runtime-v1`
- **Release**: https://github.com/nithish0302/JARVIS/releases/tag/sidecar-runtime-v1
- **Assets** (gzip-compressed tar, split under GitHub's 2GB/file limit):
  - `internal.tar.gz.part_aa` — 1,992,294,400 bytes — sha256 `a5bba4c522c854cc33e52ce5f85074598a3b61c44216a095880b4c30844986dc`
  - `internal.tar.gz.part_ab` — 283,638,255 bytes — sha256 `27656f00bf7f46c40aaa325af05967c80f3515ada47f195c80f7ae611b0156d8`
- Extracted result: 19,571 files, 3,748,643,176 bytes

These values are hardcoded as `PARTS`/`EXPECTED_FILE_COUNT`/
`EXPECTED_TOTAL_SIZE_BYTES` constants in `sidecar_setup.rs` - the sidecar
downloads each part, verifies its sha256 while streaming, concatenates
them into one `internal.tar.gz`, extracts it with the system `tar`
(bundled in Windows since 10 1803, no extra crate dependency), then
sanity-checks the extracted file count and total size before declaring
setup complete.

## Re-cutting the release after a backend rebuild

Whenever `services/jarvis-engine/dist/jarvis-engine/_internal` changes
(a backend dependency bump, PyInstaller spec change, etc.), the release
must be re-cut and `sidecar_setup.rs` updated to match:

```bash
# 1. From services/jarvis-engine/dist/jarvis-engine/
find _internal -type f | wc -l          # -> EXPECTED_FILE_COUNT
du -sb _internal                        # -> EXPECTED_TOTAL_SIZE_BYTES

# 2. Compress and split under 2GB/part
tar -czf - _internal | split -b 1900m - internal.tar.gz.part_
sha256sum internal.tar.gz.part_* > checksums.sha256

# 3. Create a new release (bump the tag, e.g. sidecar-runtime-v2) and
#    upload each part as a release asset - via `gh release create` /
#    `gh release upload`, or the GitHub REST API directly.

# 4. Update sidecar_setup.rs: RELEASE_TAG, the PARTS table (name/sha256/
#    size per part from checksums.sha256 and `ls -la`), EXPECTED_FILE_COUNT,
#    and EXPECTED_TOTAL_SIZE_BYTES from step 1.
```

Old release tags/assets can be left in place (they cost nothing extra
once superseded) or deleted from GitHub once no shipped installer still
points at them.
