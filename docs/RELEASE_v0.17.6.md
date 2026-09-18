# v0.17.6 · Do not discard the patient for unresolved mild skin moisture

The reported failure is `IMAGE-SCREEN-UNCERTAIN`, with `diaphoresis` as the
only uncertain domain after a correction. Earlier versions discarded the entire
image for any uncertainty, including subtle moisture below the resolution of
a wide bedside view. Changing the prompt did not address that decision rule.

This release changes the acceptance rule explicitly and narrowly:

- The frozen case must specify **mild** diaphoresis.
- All nine boolean checks must pass: no definite visible conflict.
- `diaphoresis` must be the only uncertain domain.
- The displayed image retains an examination note: skin moisture is not
  discernible in this view. The finding is not marked visually confirmed.
- Missing or invalid checks, any definite conflict, uncertainty about any other
  feature, and uncertain marked sweating still prevent display.

The reviewer is explicitly instructed to separate a definite conflict from an
unresolved feature. The limited image and its fixed note stay together through
the background job, cache and renderer. Repeated renders reuse the image. The
old case, physiology, examination findings, monitor and learner decisions do not
change. There are no additional model calls or retries for this exception.

Focused regression tests replay the reported state through the real result
parser, job cache and HTML renderer, both on the initial screen and after one
correction. External provider responses and image creation are substituted;
those tests verify application behavior, not clinical quality of a new image.
They also verify that conflicts and other uncertainties cannot use the exception.

Scene renderer version 11 and pipeline version 4 refresh existing development
sessions. Images discarded by older completed jobs cannot be recovered by this
release; an existing encounter may require one new image request, not a new case.

Publish only to `clinical-encounter-v0.13`. Protected branches and account or
database settings are not changed.

```bash
cd ~/Downloads
unzip -n management_reasoning_simulator_v0.17.6.zip
cd management_reasoning_simulator_v0.17.6
```
