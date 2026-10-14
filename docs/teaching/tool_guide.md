# Step-by-step guide: find the same object in different surveys

These optional online steps are platform-independent and need no student code.
The [standalone activity](ucd_investigation.html) has saved data/images if a service
is unavailable. Use that snapshot as the common basis for submitted answers.

## 1. Gaia Archive: identify the record

1. Choose M60-UCD1 in the activity. Copy Gaia DR3 identifier
   **3927659910436411136** as text; note RA **190.89985110**, Dec **+11.53462982**, in degrees.
2. Open the [ESA Gaia Archive](https://gea.esac.esa.int/archive/). Choose its
   object-search route, labeled Single Object or basic position search in different
   interface versions. Select **Gaia DR3** if a release choice is offered.
3. Search the exact identifier if supported. Otherwise enter the decimal-degree
   coordinates and a small radius such as **5 arcseconds**. This identifies a known
   object; it is not the size of a host-galaxy search region.
4. Select the row with exactly that source identifier. A nearby symbol or similar
   name is insufficient. If lookup fails, use the saved row and report the failure.
5. Inspect G, BP-RP, parallax/error, pmra/error, pmdec/error, RUWE, and
   `phot_bp_rp_excess_factor`. Use result-table column controls or source details
   if fields are hidden. Read units; missing fields remain missing.
6. Repeat for the foreground comparison. Record the date and any differences from
   the supplied DR3 snapshot. More decimal places do not mean a more certain class.

The saved queries were verified with ESA's TAP service. Current graphical menu
labels have not been fully tested; this is not a screenshot-exact menu transcript.
Official help: [data extraction](https://www.cosmos.esa.int/web/gaia-users/archive/extract-data).

## 2. Gaia Visualization: examine sky context

1. Open [Gaia Visualization](https://gea.esac.esa.int/archive/visualization/).
2. Use its sky/position view and available coordinate-search controls to navigate
   to M60. If direct object search is unavailable, use the Archive or Aladin for
   exact identification instead.
3. Inspect the distribution of catalog sources. A source-density view is not a
   color image or a map of confirmed galaxies. Is the UCD obvious from position alone?
4. Try supported linked selections or magnitude histograms if available. Do not
   assume every selected source is a UCD or our labeled examples represent that area.
5. Use the activity's built-in G-versus-flux-excess plot for Task 2;
   arbitrary-feature plotting in the live service is not required. A parallax-based
   stellar 3D view does not give a UCD's host distance.

Official [visualization guide](https://www.cosmos.esa.int/web/gaia-users/archive/visualisation/).
Unavailable online services do not block the core exercise.

## 3. Aladin Desktop: overlay images and catalogs

1. Download [Aladin Desktop from CDS](https://aladin.cds.unistra.fr/AladinDesktop/).
   Choose your operating-system installer. Windows users can use the official
   installer rather than configure a development environment. Aladin installation
   is optional and is not needed to open the supplied HTML.
2. Enter **190.89985110 +11.53462982** in Aladin's target/location box. Confirm
   equatorial coordinates in degrees or use an explicitly formatted equivalent.
3. Use the image/server selector to load an optical image. HiPS services stream
   sky images at different zoom levels. Record the service name/release: a DSS or
   Pan-STARRS image is not Legacy Survey DR11.
4. Use the catalog/server selector for **Gaia DR3**, available in VizieR as
   **I/355/gaiadr3**, around this position. Start with a small field; overlay the
   catalog symbols on the image.
5. Select the target symbol and inspect its table row. Check the exact identifier.
   Toggle the catalog layer to compare the marker against the actual image.
6. Zoom in for source shape and out for neighbors/host light. Use the angular-
   distance tool if needed; screen pixels do not have a fixed angular scale across zooms.
7. Repeat with the foreground star. It can shift between an image's epoch and
   Gaia's **J2016.0** position. A discrepancy still needs identifier/epoch/neighbor checks.

Menu names vary by version. See CDS [manuals and tutorials](https://aladin.cds.unistra.fr/java/nph-aladin.pl?frame=manual).
No Windows-specific execution or complete GUI walkthrough is claimed.

## 4. Legacy Survey: inspect the observation

1. Select a source in the activity and choose **Legacy viewer ↗**.
   The link points to its Gaia coordinates with `layer=ls-dr11`.
2. Confirm the DR11 image layer; model/residual layers are not the original image.
   A release label does not imply new observations everywhere.
3. At high zoom inspect the intended compact source; at lower zoom inspect host
   background, neighbors, and defects. Compare with the embedded close/context views.
4. Use the coordinate readout and angular scale. A crosshair marks the requested
   position, not a verified physical association.
5. A blank tile means unavailable imaging, not necessarily empty sky. The documented
   `ls-dr11-grz` layer returned blank tiles for two preparation examples; this
   activity uses `ls-dr11` instead.
6. Record morphology with uncertainty. RGB display colors are not calibrated
   photometric colors. A compact image alone cannot separate a star, QSO, or UCD.

Official references: [viewer API](https://www.legacysurvey.org/viewer/urls),
[DR11 description](https://www.legacysurvey.org/dr11/description/),
[known issues](https://www.legacysurvey.org/dr11/issues/).

## 5. Save and return to the activity

Record unavailable steps and live-data differences instead of silently replacing
the supplied measurements. **Download answers (JSON)** to save/resume or
**Download readable answers** for a text copy. Nothing uploads automatically.
