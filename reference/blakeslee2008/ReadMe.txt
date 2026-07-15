J/AJ/136/2295  Ultra-compact dwarf candidates in Abell S0740  (Blakeslee+, 2008)
================================================================================
Ultra-compact dwarf candidates near the lensing galaxy in Abell S0740.
    Blakeslee J.P., Degraaff R.B.
   <Astron. J., 136, 2295-2305 (2008)>
   =2008AJ....136.2295B
================================================================================
ADC_Keywords: Clusters, galaxy ; Galaxies, photometry ; Photometry, HST
Keywords: galaxies: clusters: individual (Abell S0740) - galaxies: dwarf -
          galaxies: elliptical and lenticular, cD - galaxies: evolution -
          galaxies: individual (ESO 325-G004)

Abstract:
    We analyze three-band imaging data of the giant elliptical galaxy
    ESO 325-G004 from the Hubble Space Telescope Advanced Camera for
    Surveys (ACS). This is the nearest known strongly lensing galaxy, and
    it resides in the center of the poor cluster Abell S0740 at redshift
    z=0.034. Based on magnitude, color, and size selection criteria, we
    identify a sample of 15 ultra-compact dwarf (UCD) galaxy candidates
    within the ACS field.

Description:
    ESO 325-G004 was imaged with the ACS/WFC in the F475W, F625W, and
    F814W filters. Throughout this paper, we refer to magnitudes in these
    filters as g475, r625, and I814, respectively. The galaxy was
    initially observed in F814W and F475W as part of the HST GO Program
    10429 during 2005 January.

    There were 22 F814W exposures of varying times totaling 18882s, and
    three exposures in F475W of 367s each. In 2006 February, further
    imaging of the ESO 325-G004 field was carried out by the HST DD
    Program 10710 for a Hubble Heritage public release image.

File Summary:
--------------------------------------------------------------------------------
 FileName   Lrecl  Records   Explanations
--------------------------------------------------------------------------------
ReadMe         80        .   This file
table1.dat     92       41   Ultra-compact dwarf (UCD) candidates and
                              compact galaxies
--------------------------------------------------------------------------------

See also:
  J/A+A/383/823 : Radial velocities of UCOs in Fornax (Mieske+, 2002)
  J/A+A/418/445 : FCOS Ultra Compact Dwarf galaxies radial vel. (Mieske+, 2004)
  J/A+A/472/111 : Centaurus Compact Object Survey (Mieske+, 2007)

Byte-by-byte Description of file: table1.dat
--------------------------------------------------------------------------------
   Bytes Format Units   Label   Explanations
--------------------------------------------------------------------------------
   1-  4  I4    ---    [BD2008] [211/5503] Identification number
   6- 14  F9.5  deg     RAdeg   Right ascension in decimal degrees (J2000)
  16- 24  F9.5  deg     DEdeg   Declination in decimal degrees (J2000)
  26- 31  F6.3  mag     Imag    [20/24] HST/ACS F814W magnitude
  33- 37  F5.3  mag   e_Imag    rms uncertainty on Imag
  39- 43  F5.3  mag     r-I     HST/ACS F625W-F814W colour index
  45- 49  F5.3  mag   e_r-I     rms uncertainty on r-I
  51- 55  F5.3  mag     g-I     HST F475W-F814W colour index
  57- 61  F5.3  mag   e_g-I     rms uncertainty on g-I
  63- 66  F4.2  ---     b/a     [0/1] Axis ratio measured by SExtractor
                                      (no PSF correction)
  68- 71  F4.2  ---     q       [0/1] Intrinsic axis ratio q=b/a=1-{epsilon}
                                      from our two-dimensional modeling with
                                      PSF correction
  73- 77  F5.1  pc      Rc      Fitted circularized effective radius,
                                       R_c_=R_e_*sqrt(q)
  79- 85  E7.2  Msun    Mass    Photometrically derived stellar mass estimate
  87- 92  A6    ---     MType   Morphological type from our visual inspection.
                                (all objects in Fi.8 are ultra-compact dwarfs
                                (UCD); see text for further details)
--------------------------------------------------------------------------------

History:
  * 30-Jul-2011: From electronic version of the journal
  * 22-Nov-2013: Table 1 corrected (source #211 added)
================================================================================
(End)                                      Patricia Vannier [CDS]    24-May-2011
