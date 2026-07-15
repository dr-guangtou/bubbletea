J/AJ/137/498        UCD and bright GC in Fornax              (Gregg+, 2009)
================================================================================
A large population of ultra-compact dwarfs and bright intracluster globulars in
the Fornax cluster.
    Gregg M.D., Drinkwater M.J., Evstigneeva E., Jurek R., Karick A.M.,
    Phillipps S., Bridges T., Jones J.B., Bekki K., Couch W.J.
   <Astron. J., 137, 498-506 (2009)>
   =2009AJ....137..498G
================================================================================
ADC_Keywords: Clusters, galaxy ; Galaxies, optical ; Clusters, globular
Keywords: galaxies: clusters: general - galaxies: dwarf -
          globular clusters: general

Abstract:
    All the previously cataloged ultracompact dwarf (UCD) galaxies
    in the Fornax and Virgo clusters have 17.5<b_J_<20. Using the 2dF
    spectrograph on the Anglo-Australian Telescope, we have carried out
    a search for fainter UCDs in the Fornax Cluster. In the magnitude
    interval 19.5<b_J_<21.5, we have found 54 additional compact cluster
    members within a projected radius of 0.9{deg} (320kpc) of the cluster
    center, all of which meet our selection and observational criteria to
    be UCDs.

Description:
    The original FCSS observations in the central field of the Fornax
    Cluster produced six UCDs in the range 16.5<b_J_<20.0. Here, we define
    UCDs simply as objects, which were classified as "stellar"
    (unresolved) in the photographic Automatic Plate Measuring (APM)
    catalog but were found to have redshifts consistent with the
    membership of the Fornax Cluster (600km/s<cz<2500km/s).

    In 2003 October and 2004 November, we made new 2dF observations in
    Fornax to test this prediction.

File Summary:
--------------------------------------------------------------------------------
 FileName   Lrecl  Records   Explanations
--------------------------------------------------------------------------------
ReadMe         80        .   This file
table2.dat     66       60   UCDs in Fornax
table3.dat     79       53   Fornax velocity member dE/S0,N galaxies
--------------------------------------------------------------------------------

See also:
       VII/180 : Galaxies in Fornax Cluster & 5 nearby groups (Ferguson+ 1990)
 J/A+A/383/823 : Radial velocities of UCOs in Fornax (Mieske+, 2002)

Byte-by-byte Description of file: table2.dat
--------------------------------------------------------------------------------
   Bytes Format Units   Label     Explanations
--------------------------------------------------------------------------------
   1-  2  I2    ---     Seq       Sequential number, [GDE2009] UCD NN in Simbad
   4-  5  I2    h       RAh       Right ascension (J2000)
   7-  8  I2    min     RAm       Right ascension (J2000)
  10- 14  F5.2  s       RAs       Right ascension (J2000)
      16  A1    ---     DE-       Declination sign (J2000)
  17- 18  I2    deg     DEd       Declination (J2000)
  20- 21  I2    arcmin  DEm       Declination (J2000)
  23- 26  F4.1  arcsec  DEs       Declination (J2000)
  28- 31  F4.1  mag     rfmag     ?=- r_f_ magnitude (1)
  33- 36  F4.1  mag     bJmag     ?=- b_J_ magnitude (1)
  38- 41  I4    km/s    RV        Radial velocity
  43- 45  I3    km/s  e_RV        rms uncertainty on RV
  47- 66  A20   ---     Notes     Notes (2)
--------------------------------------------------------------------------------
Note (1): Photometry is from the APM digitized sky survey database;
     objects with no  photometry entries are either not detected or
     merged with nearby objects.
Note (2): Original six UCDs from Phillipps et al. (2001ApJ...560..201P) and
     Jones et al. (2006AJ....131..312J) are identified. Also identified are
     objects in common with
 * Mieske et al. (2002, Cat, J/A+A/383/823, F-NNNN = <FCOS F-NNNN> in Simbad)
 * Mieske et al. (2004, Cat. J/A+A/418/445, F-NNNN = <FCOS F-NNNN> in Simbad)
 * Dirsch et al. (2004,Cat. J/AJ/127?2114, NN:NN = <[DRG2004] NN:NN> in Simbad)
 * or Bergond et al. (2007, Cat. J/A+A/464/L21,
   GCNN.NN = <[BAL2007] gcNN.NN> in Simbad,
   UCD N = <[DJG2000] UCO N> in Simbad
--------------------------------------------------------------------------------

Byte-by-byte Description of file: table3.dat
--------------------------------------------------------------------------------
   Bytes Format Units   Label     Explanations
--------------------------------------------------------------------------------
   1-  3  I3    ---     FCC       FCC number (1)
   5-  6  I2    h       RAh       Right ascension (J2000)
   8-  9  I2    min     RAm       Right ascension (J2000)
  11- 15  F5.2  s       RAs       Right ascension (J2000)
      17  A1    ---     DE-       Declination sign (J2000)
  18- 19  I2    deg     DEd       Declination (J2000)
  21- 22  I2    arcmin  DEm       Declination (J2000)
  24- 27  F4.1  arcsec  DEs       Declination (J2000)
  29- 32  F4.1  mag     bJmag     ?=- b_J_ magnitude (1)
  34- 37  I4    km/s    RV        Radial velocity
      39  I1    ---   r_RV        Reference for RV (2)
  41- 47  F7.2  arcmin  x         Distance in alpha from the center of NGC1399
  49- 55  F7.2  arcmin  y         Distance in delta from the center of NGC1399
  57- 62  F6.2  arcmin  R         Radial distance from the center of NGC1399
  64- 79  A16   ---     Type      Morphological type (1)
--------------------------------------------------------------------------------
Note (1): FCC number and galaxy types are from Ferguson (1989, Cat.  VII/180).
Note (2): Sources for radial velocities as follows:
   1 = Drinkwater et al. (2001ApJ...548L.139D)
   2 = Karick (2005, Phd thesis, Melbourne University)
   3 = Drinkwater et al. (2000A&A...355..900D)
   4 = Mieske et al. (2002, Cat. J/A+A/383/823)
--------------------------------------------------------------------------------

History:
    From electronic version of the journal

================================================================================
(End)                                      Patricia Vannier [CDS]    31-Aug-2011
