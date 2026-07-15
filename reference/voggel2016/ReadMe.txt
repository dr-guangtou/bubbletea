J/A+A/586/A102      UCDs in the halo of NGC1399                  (Voggel+, 2016)
================================================================================
Globular cluster clustering and tidal features around ultra-compact dwarf
galaxies in the halo of NGC 1399.
    Voggel K., Hilker M., Richtler T.
   <Astron. Astrophys., 586, A102-102 (2016)>
   =2016A&A...586A.102V    (SIMBAD/NED BibCode)
================================================================================
ADC_Keywords: Galaxies, nearby ; Associations, stellar ; Clusters, globular
Keywords: galaxies: clusters: individual: NGC 1399 - galaxies: dwarf -
          galaxies: fundamental parameters - galaxies: nuclei -
          galaxies: star clusters: general

Abstract:
    We present a novel approach to constrain the formation channels of
    ultra-compact dwarf galaxies (UCDs). They most probably are an
    inhomogeneous class of objects, composed of remnants of tidally
    stripped dwarf elliptical galaxies and star clusters that occupy the
    high mass end of the globular cluster luminosity function. We use
    three methods to unravel their nature: 1) we analyzed their surface
    brightness profiles; 2) we carried out a direct search for tidal
    features around UCDs; and 3) we compared the spatial distribution of
    GCs and UCDs in the halo of their host galaxy. Based on FORS2
    observations under excellent seeing conditions, we studied the
    detailed structural composition of a large sample of 97 UCDs in the
    halo of NGC1399, the central galaxy of the Fornax cluster, by
    analyzing their surface brightness profiles. We found that 13 of the
    UCDs were resolved above the resolution limit of 23pc and we derived
    their structural parameters fitting a single Sersic function. When
    decomposing their profiles into composite King and Sersic profiles, we
    find evidence for faint stellar envelopes at {mu}=~26mag/arcsec^2^,
    surrounding the UCDs up to an extension of 90pc in radius. We also
    show new evidence for faint asymmetric structures and tidal tail-like
    features surrounding several of these UCDs, a possible tracer of their
    origin and assembly history within their host galaxy halos. In
    particular, we present evidence for the first discovery of a
    significant tidal tail with an extension of ~350pc around UCD-FORS2.
    Finally, we studied the local overdensities in the spatial
    distribution of globular clusters within the halo of NGC1399 out to
    110kpc to see if they are related to the positions of the UCDs. We
    found a local overabundance of globular clusters on a scale of <=1kpc
    around UCDs, when we compared it to the distribution of globulars from
    the host galaxy. This effect is strongest for the metal-poor blue GCs.
    We discuss how likely it is that these clustered globulars were
    originally associated with the UCD, either as globular cluster systems
    of a nucleated dwarf galaxy that was stripped down to its nucleus, or
    as a surviving member of a merged super star cluster complex.

Description:
    To study UCDs within the Fornax cluster, we used data from ESO program
    076.B-0520 (PI:Richtler). The imaging data were taken in the nights
    October 9th and 10th, 2005, with the high-resolution collimator mode
    of FORS2, which is mounted on UT1 of the Very Large Telescope (VLT).
    Three separate fields were observed in the R-band. Fields 1 and 2 with
    3x800s exposure time each and field 3 with 5x800s.

File Summary:
--------------------------------------------------------------------------------
 FileName      Lrecl  Records   Explanations
--------------------------------------------------------------------------------
ReadMe            80        .   This file
table1.dat        96       13   Results from the Sersic fits for those 13 UCDs
                                 that have half-light radii larger than the
                                 resolution limit of 23 pc
tablea1.dat       89       21   UCD and companion properties of all 19 objects
                                 for which a faint point source was found
                                 within r<300pc (see Fig. 9)
tablea2.dat       63       71   UCDs from the original sample of 97 in the FORS
                                 fields, which are not yet listed in Table 1 or
                                 as a companion hosting UCD in Table A.1
--------------------------------------------------------------------------------

See also:
 J/A+A/383/823    : Radial velocities of UCOs in Fornax (Mieske+, 2002)
 J/AJ/127/2114    : Globular clusters around NGC 1399 (Dirsch+, 2004)
 J/A+A/418/445    : FCOS Ultra Compact Dwarf galaxies radial vel. (Mieske+ 2004)
 J/A+A/513/A52    : Velocities of NGC 1399 globular clusters (Schuberth+, 2010)
 J/MNRAS/382/1342 : Compact stellar systems around NGC 1399 (Firth+, 2007)

Byte-by-byte Description of file: table1.dat
--------------------------------------------------------------------------------
   Bytes Format Units   Label     Explanations
--------------------------------------------------------------------------------
   1-  8  A8    ---     ---       [UCD-FORS -]
  10- 11  I2    ---     UCD-FORS  UCD-FORS number
  13- 18  A6    ---     AName     Alternative name (G1)
      20  A1    ---   n_AName     [abc] Note on AName (1)
      23  I1    h       RAh       Right ascension (J2000)
  25- 26  I2    min     RAm       Right ascension (J2000)
  28- 32  F5.2  s       RAs       Right ascension (J2000)
      34  A1    ---     DE-       Declination sign (J2000)
  35- 36  I2    deg     DEd       Declination (J2000)
  38- 39  I2    arcmin  DEm       Declination (J2000)
  41- 44  F4.1  arcsec  DEs       Declination (J2000)
  46- 50  F5.2  mag     Vmag      UCD V magnitude
  52- 56  F5.3  mag   e_Vmag      rms uncertainty on Vmag
  58- 62  F5.2  pc      Reff      Effective temperature
  64- 67  F4.2  pc    e_Reff      rms uncertainty on Reff (2)
  69- 72  F4.2  ---     n         Sersic index
  74- 77  F4.2  ---   e_n         rms uncertainty on n (2)
  79- 82  F4.2  mag     V-I       UCD V-I colour index (3)
  84- 87  F4.2  mag   e_V-I       rms uncertainty on V-I
  89- 92  I4    km/s    RV        Radial velocity (3)
  94- 96  I3    km/s  e_RV        rms uncertainty on RV
--------------------------------------------------------------------------------
Note (1): Some of these objects were also presented in Richtler et al.
           (2008A&A...478L..23R) with the following names:
           a = 78:12, [DRG2004] 78:12 in Simbad
           b = 91:93, [DRG2004] 91:93 in Simbad
           c = 90:12, [DRG2004] 90:12 in Simbad
Note (2): The provided errors on Reff and n are those given by GALFIT, which
  should be taken with caution because close to the resolution limit these
  errors might be underestimated.
Note (3): The (V-I) colors and radial velocities are taken from the respective
   original samples.
--------------------------------------------------------------------------------

Byte-by-byte Description of file: tablea1.dat
--------------------------------------------------------------------------------
   Bytes Format Units   Label     Explanations
--------------------------------------------------------------------------------
       1  A1    ---     Ref       Reference used in Fig. 9
   3- 10  A8    ---     ---       [UCD-FORS -]
  12- 13  I2    ---     UCD-FORS  UCD-FORS number
  15- 20  A6    ---     AName     Alternative name
      23  I1    h       RAh       Right ascension (J2000)
  25- 26  I2    min     RAm       Right ascension (J2000)
  28- 32  F5.2  s       RAs       Right ascension (J2000)
      34  A1    ---     DE-       Declination sign (J2000)
  35- 36  I2    deg     DEd       Declination (J2000)
  38- 39  I2    arcmin  DEm       Declination (J2000)
  41- 44  F4.1  arcsec  DEs       Declination (J2000)
  46- 50  F5.2  mag     Vmag      UCD V magnitude
  52- 55  F4.2  mag     V-I       UCD V-I colour index
  57- 61  F5.2  mag     Vcomp     V magnitude of the possible companion
  63- 65  I3    pc      Distc     Distance of the companion to the UCD
  67- 71  F5.2  kpc     DisttN    Distance of the UCD to the center of NCG 1399
  73- 75  I3    pc      r         Tidal radius (1)
  77- 80  F4.2  ---     Distc/r   Fraction between Distc/r (2)
  82- 85  I4    km/s    RV        Radial Velocity
  87- 89  I3    km/s  e_RV        rms uncertainty on RV
--------------------------------------------------------------------------------
Note (1): estimate of the tidal radius of this UCD for it's specific position
  using the formula given in 8.
Note (2): If this fraction is smaller than 1.0 the companion lies within the
  tidal radius of the UCD host object, which is the case for 16 of our 19 UCDs.
--------------------------------------------------------------------------------

Byte-by-byte Description of file: tablea2.dat
--------------------------------------------------------------------------------
   Bytes Format Units   Label     Explanations
--------------------------------------------------------------------------------
   1-  8  A8    ---     ---       [UCD-FORS -]
  10- 11  I2    ---     UCD-FORS  UCD-FORS number
  13- 18  A6    ---     AName     Alternative name (G1)
      21  I1    h       RAh       Right ascension (J2000)
  23- 24  I2    min     RAm       Right ascension (J2000)
  26- 30  F5.2  s       RAs       Right ascension (J2000)
      32  A1    ---     DE-       Declination sign (J2000)
  33- 34  I2    deg     DEd       Declination (J2000)
  36- 37  I2    arcmin  DEm       Declination (J2000)
  39- 42  F4.1  arcsec  DEs       Declination (J2000)
  44- 48  F5.2  mag     Vmag      UCD V magnitude
  50- 53  F4.2  mag   e_Vmag      rms uncertainty on Vmag
  55- 58  F4.2  mag     V-I       UCD V-I colour index
  60- 63  F4.2  mag   e_V-I       rms uncertainty on V-I
--------------------------------------------------------------------------------

Global notes:
Note (G1): The alternative object names from the literature are from the
     following sources:
  UCDx  = Firth et al. (2007, Cat. J/MNRAS/382/1342) [DJG2000] UCO XX in Simbad
  X_xxx = Mieske et al. (2002, Cat. J/A+A/383/823 & 2004, Cat. J/A+A/418/445
           FCOS F-NNNN in Simbad
  Yxxx  = Richtler et al. (2008A&A...478L..23R), [MHB2008] Yxxx in Simbad
           or from Schuberth et al. (2010, Cat. J/A+A/513/A52),
             [SRH2010] NN NNN, [SRH2010] GS0N-M0N NNN in Simbad
  NN.NNN = Dirsch et al. (2014, Cat. J/AJ/127/2114), [DRG2004] NN:NNN in Simbad
--------------------------------------------------------------------------------

History:
    From electronic version of the journal

================================================================================
(End)                                      Patricia Vannier [CDS]    22-Apr-2016
