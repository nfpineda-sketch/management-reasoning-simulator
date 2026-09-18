# v0.14.1: embedded ECG rendering fix

Compacts the existing SVG's markup whitespace before composing it with the
photographic scene. Markdown no longer interprets the indented SVG as a code
block. Path coordinates and monitor values are unchanged. A renderer-version
check refreshes the module on a Streamlit hot update without clearing the scene
image or encounter state.

Verified with a CommonMark rendering regression and the existing clinical-scene
checks. Test dependencies: pip install -r requirements-dev.txt.
Only clinical-encounter-v0.13 is updated.
