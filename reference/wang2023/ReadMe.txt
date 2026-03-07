J/ApJ/954/206  A GCs search in M31 with Gaia, PS1, LAMOST, PAndAS  (Wang+, 2023)
================================================================================
Searching for new globular clusters in M31 with Gaia EDR3.
    Wang Y., Yuan H., Chen B., Chen X., Wu H., Niu Z., Huang S., Liu J.
   <Astrophys. J., 954, 206 (2023)>
   =2023ApJ...954..206W
================================================================================
ADC_Keywords: Clusters, globular; Galaxies, nearby; Colors; Photometry, ugriz;
              Spectra, optical
Keywords: Globular star clusters ; Star clusters ; Random Forests ;
          Observational astronomy

Abstract:
    We have found 50 new globular cluster (GC) candidates around M31 with
    Gaia Early Data Release 3 (EDR3), with the help of Pan-STARRS1 DR1
    magnitudes and Pan-Andromeda Archaeological Survey (PAndAS) images.
    Based on the latest Revised Bologna Catalog and simbad, we trained two
    random forest (RF) classifiers, the first one to distinguish extended
    sources from point sources and the second one to further select GCs
    from extended sources. From 1.85 million sources of 16^m^<g<19.5^m^
    and within a large area of ~392deg2 around M31, we selected
    20,658 extended sources and 1934 initial GC candidates. After visual
    inspection of the PAndAS images, to eliminate the contamination from
    noncluster sources, particularly galaxies, we finally got
    50 candidates. These candidates are divided into three types (a, b,
    and c), according to their projected distance D to the center of M31
    and their probability of being a true GC, P_GC_, which is calculated
    by our second RF classifier. Among these candidates, 14 are found to
    be associated (in projection) with the large-scale structures within
    the halo of M31. We also provide several simple parameter criteria for
    selecting extended sources effectively from Gaia EDR3, which can reach
    a completeness of 92.1% with a contamination fraction lower than 10%.

Description:
    The Panoramic Survey Telescope and Rapid Response System (Pan-STARRS),
    located at Hawaii, conducted a stacked 3{pi} Steradian Survey in the
    five broad bands grizy_p1_. We used the PSF magnitude of grizyp1 and
    the colors (g-r, r-i, i-y, and y-z). See Section 2.1.

    We used the classification data in the Low-Resolution Spectroscopic
    (LRS) Survey of the Large Sky Area Multi-Object Fiber Spectroscopic
    Telescope (LAMOST) DR8 as auxiliary data in Sections 3.1 and 4.2.
    LAMOST, also called the Guo Shou Jing Telescope, is a specially
    designed Schmidt telescope with both a large aperture (an effective
    aperture of 3.6-4.9m) and a wide field of view (5{deg}). It is capable
    of observing thousands of targets using 4000 fibers in a single
    observation. The spectrum wavelength coverage is from 370 to 900nm,
    with a resolving power of ~1800. We used a subsample of LAMOST DR8 LRS
    that had a signal-to-noise ratio (S/N) larger than 20. To avoid
    contamination from M31, we excluded the sources in a 3.5{deg}x3.5{deg}
    area centered at M31. see Section 2.3.

    Our visual inspection relies on the optical images of the PAndAS
    survey, which were obtained around M31 and M33 by the
    Canada-France-Hawaii Telescope, with average seeings of 0.6" and 0.67"
    in the i and g bands, respectively. See Section 2.4.

Objects:
    ----------------------------------------------------------
        RA   (ICRS)   DE        Designation(s)
    ----------------------------------------------------------
     00 42 44.33  +41 16 07.5   M31 = NAME Andromeda Galaxy
    ----------------------------------------------------------

File Summary:
--------------------------------------------------------------------------------
 FileName  Lrecl  Records   Explanations
--------------------------------------------------------------------------------
ReadMe        80        .   This file
table8.dat    82    20658   Catalog of the 20,658 extended sources classified by
                             Clf1 (see Section 3.2)
table10.dat   65       50   Catalog of the visually checked globular cluster
                             (GC) candidates
--------------------------------------------------------------------------------

See also:
 V/143   : Revised Bologna Catalog of M31 clusters, V.5 (Galleti+ 2012)
 V/156   : LAMOST DR7 catalogs (Luo+, 2019)
 VII/285 : Gaia DR2 quasar & galaxy classification (Bailer-Jones+, 2019)
 I/350   : Gaia EDR3 (Gaia Collaboration, 2020)
 I/355   : Gaia DR3 Part 1. Main source (Gaia Collaboration, 2022)
 II/389  : The Pan-STARRS release 1 (PS1) Survey - DR2 (Magnier+, 2025)
 J/A+A/416/917  : Revised Bologna Cat. of M31 globular clusters (Galleti+, 2004)
 J/AJ/134/706   : New globular clusters in M 31 (Kim+, 2007)
 J/PASP/119/7   : HST WFPC2 star clusters in M31 (Krienke+, 2007)
 J/ApJS/177/174 : Star clusters in M31 (Narbutis+, 2008)
 J/MNRAS/402/803  : M31 globular cluster system (Peacock+, 2010)
 J/AJ/142/139   : A new catalog of HII regions in M31 (Azimlu+, 2011)
 J/ApJ/752/95   : PHAT stellar cluster survey. I. Year 1 (Johnson+, 2012)
 J/ApJS/199/37  : GALEX catalog of star clusters in M31 (Kang+, 2012)
 J/ApJ/802/127  : PHAT stellar cluster survey. II. AP catalog (Johnson+, 2015)
 J/ApJ/833/167  : PAndAS view of Andromeda satellites. II. (Martin+, 2016)
 J/ApJ/868/55   : Large-scale structure of M31. II. PAndAS (McConnachie+, 2018)
 J/A+A/623/A65  : Multiphot. of M31 outer halo globular clusters (Wang+, 2019)
 J/ApJ/899/140  : 632 Gaia Ultracompact Dwarf galaxy candidates (Voggel+, 2020)
 J/A+A/649/A3   : Gaia EDR3 photometric passbands (Riello+, 2021)
 J/A+A/658/A51  : New M31 star cluster candidates (Wang+, 2022)
 J/ApJ/947/34   : New velocity measurements of NGC 5128 GCs (Hughes+, 2023)

Byte-by-byte Description of file: table8.dat
--------------------------------------------------------------------------------
   Bytes Format Units  Label    Explanations
--------------------------------------------------------------------------------
   1- 19 I19    ---    Gaia     Gaia EDR3 identifier
  21- 29 F9.6   deg    RAdeg    [0/22.7] Right Ascension (J2000)
  31- 39 F9.6   deg    DEdeg    [29.2/53.3] Declination (J2000)
  41- 46 F6.3   mag    Gmag     [15.7/22.4] Gaia EDR3 G band magnitude
  48- 53 F6.3   mag    gmag     [15.1/19.5] Pan-STARRs g band AB magnitude
  55- 59 F5.3   mag    g-r      [0.001/2.2] Pan-STARRs (g-r) color
  61- 65 F5.3   [-]    E(BP/RP) [0.04/2.5] Log of Gaia EDR3 bp_rp_excess
                                 parameter; Section 2.2
  67- 72 F6.3   mag    Gp-G     [-4.92/0.6] Difference between predicted and
                                 observed Gaia G magnitudes
  74- 77 F4.2   ---    Pext     [0.5/1] Likelihood source is extended (G1)
  79- 82 F4.2   ---    PGC      [0/1] Likelihood source is a globular
                                 cluster (G1)
--------------------------------------------------------------------------------

Byte-by-byte Description of file: table10.dat
--------------------------------------------------------------------------------
   Bytes Format Units   Label    Explanations
--------------------------------------------------------------------------------
   1-  2 I2     ---     Seq      [1/50] Identifier; same as in Figure 14
   4- 12 F9.6   deg     RAdeg    [0.6/22.6] Right Ascension (J2000)
  14- 22 F9.6   deg     DEdeg    [33.4/49.2] Declination (J2000)
  24- 29 F6.3   mag     Gmag     [18.3/22] Gaia EDR3 G band magnitude
  31- 36 F6.3   mag     gmag     [16.7/19.5] Pan-STARRs g band AB magnitude
  38- 42 F5.3   mag     g-r      [0.002/1.2] Pan-STARRs (g-r) color
  44- 48 F5.3   [-]     E(BP/RP) [0.4/1.5] Log of Gaia EDR3 bp_rp_excess
                                  parameter; Section 2.2
  50- 55 F6.3   mag     Gp-G     [-3.2/-0.7] Difference between predicted and
                                  observed Gaia G magnitudes
  57- 60 F4.2   ---     Pext     [0.6/1] Likelihood source is extended (G1)
  62- 65 F4.2   ---     PGC      [0.27/0.97] Likelihood source is a globular
                                  cluster (G1)
--------------------------------------------------------------------------------

Global notes:
Note (G1): For detail about these 2 probability, please refer to
           Sections 3.2 and 3.3.
--------------------------------------------------------------------------------

History:
    From electronic version of the journal

Licences: cc-by

================================================================================
(End)                    Prepared by [AAS], Emmanuelle Perret [CDS] 14-Oct-2025
