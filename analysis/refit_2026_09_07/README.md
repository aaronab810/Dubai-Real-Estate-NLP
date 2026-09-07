# Executed BERTopic refit, 7 September 2026

**47,748 final-clean records → 4 AutoModerator records excluded → 47,744 fitted records → 23,261 assigned to 274 topics + 24,483 outliers.** No empty texts were removed. All records in the fitted corpus are saved, including topic -1. No semantic-group or SMDI mapping has been assigned.

The outlier proportion is 51.28%, versus 47.83% in the old 87,574-record model. The inputs and software environments differ, so this is not a controlled estimate of an AutoModerator-removal effect or proof of improved topic quality. Thirty records, sampled with seed 42 across ten topic IDs including -1, were inspected qualitatively by Codex. Examples exposed DM/contact requests, generic comments, repeated filler and a property listing; this is error analysis, not independent human validation. Further filtering and parameter evaluation remain necessary.

## Reproduce locally

The script expects the Drive final-clean parquet under `inputs/` and the previous row-aligned `smdi_posts.csv` and `embeddings.npy` under `../research_review_2026_09_06/inputs/`. Source IDs and input hashes are recorded in `refit_manifest.json`. `download_public_drive.py` is a downloader for the identified shared files; it does not authenticate or change source permissions.

Create a Python 3.12 environment and install `requirements-lock.txt`. Run `python refit.py`. This performs actual UMAP/HDBSCAN training, saves all outputs in `outputs/`, verifies row conservation and reloads the complete fitted model. Runtime on the execution host was about four minutes after dependencies and encoder weights were available.

MiniLM vectors were reused for 40,564 exactly matching texts only after fresh encoding of a seeded 32-text sample matched within a maximum absolute difference of 1.46e-7. The 7,180 remaining rows contain 7,173 distinct texts, encoded with the same normalized MiniLM model. The model revision is pinned in the manifest. The script retains notebook clustering parameters and disables only the all-topic membership probability matrix; assigned-cluster strengths remain available.

## Use the saved run in the notebook

Extract the delivered `clean_refit_2026_09_07.zip` under `Dubai_Real_Estate_Data/SMDI creation/`. The archive contains a top-level `clean_refit_2026_09_07` directory. This matches the canonical notebook's resume path. The notebook can read `social_with_topics.parquet` and the aligned `embeddings.npy` directly. Start at the resume section to inspect the existing topics; do not rerun discovery unless you want another fit. Install the recorded package versions before loading `bertopic_model.pkl`; pickled models are environment-dependent.

The separate 25-group experiment is still an experiment. Its group IDs will differ from the old model. Review the content and grouping before entering any SMDI mapping. Topic -1 is never a normal topic/group, and these outputs do not automatically recover outliers.

## Files

- `refit.py`: executed training and verification code.
- `refit_manifest.json`: aggregate counts, parameters, model revision and hashes.
- `requirements-lock.txt`: actual installed dependency versions.
- `annotation_recheck.json`: comparison of the two accessible 400-row Drive files with the previous snapshots; both are unchanged.
- `outputs/`: local model, assignments, embeddings, audit and package. Ignored by Git.
- `inputs/`: local source records, annotation files, read-only draft snapshot and encoder cache. Ignored by Git.

The current literature assessment and plain-language responses are in [the methodology review](../../docs/METHODOLOGY_EVIDENCE_2026_09_07.md). Only code and aggregate documentation are intended for GitHub.
