J/ApJ/899/140    632 Gaia Ultracompact Dwarf galaxy candidates   (Voggel+, 2020)
================================================================================
A Gaia-based catalog of candidate stripped nuclei and luminous globular clusters
in the halo of Centaurus A.
    Voggel K.T., Seth A.C., Sand D.J., Hughes A., Strader J., Crnojevic D.,
    Caldwell N.
   <Astrophys. J., 899, 140 (2020)>
   =2020ApJ...899..140V
================================================================================
ADC_Keywords: Clusters, globular; Galaxies; Optical; Photometry; Colors
Keywords: Globular star clusters ; Elliptical galaxies ;
          Ultracompact dwarf galaxies ; Galaxy kinematics ; Star clusters ;
          Galaxy nuclei

Abstract:
    Tidally stripped galaxy nuclei and luminous globular clusters (GCs)
    are important tracers of the halos and assembly histories of nearby
    galaxies, but are difficult to reliably identify with typical
    ground-based imaging data. In this paper we present a new method to
    find these massive star clusters using Gaia DR2, focusing on the
    massive elliptical galaxy Centaurus A (Cen A). We show that stripped
    nuclei and GCs are partially resolved by Gaia at the distance of Cen A,
    showing characteristic astrometric and photometric signatures. We use
    this selection method to produce a list of 632 new candidate luminous
    clusters in the halo of Cen A out to a projected radius of 150kpc.
    Adding in broadband photometry and visual examination improves the
    accuracy of our classification. In a spectroscopic pilot program we
    have confirmed five new luminous clusters, which includes the 7th and
    10th most luminous GC in Cen A. Three of the newly discovered GCs are
    further away from Cen A than all previously known GCs. Several of
    these are compelling candidates for stripped nuclei. We show that our
    novel Gaia selection method retains at least partial utility out to
    distances of ~25Mpc and hence is a powerful tool for finding and
    studying star clusters in the sparse outskirts of galaxies in the
    local universe.


File Summary:
--------------------------------------------------------------------------------
 FileName   Lrecl  Records  Explanations
--------------------------------------------------------------------------------
ReadMe         80        .  This file
table2.dat     83      632  List of Gaia ultra compact dwarf (UCD) candidates
table3.dat     75       14  List of MIKE spectroscopic targets of Gaia-based
                             UCD candidates
table4.dat     54       57  List of the 57 previously confirmed UCDs that were
                             used to assess completeness in Figure 1
--------------------------------------------------------------------------------

See also:
 I/345          : Gaia DR2 (Gaia Collaboration, 2018)
 J/ApJS/150/367 : Globular clusters in NGC 5128 (Peng+, 2004)
 J/AJ/132/2187  : MCT1 photometry of NGC 5128 globular clusters (Harris+, 2006)
 J/AJ/134/494   : NGC5128 globular clusters UBVRICMT1 phot. & RV (Woodley+,2007)
 J/MNRAS/386/1443 : 2dF study of globular clusters in NGC 5128 (Beasley+, 2008)
 J/A+A/523/A48  : Gaia photometry (Jordi+, 2010)
 J/AJ/139/1871  : Kinematics of globulars in NGC 5128 (Woodley+, 2010)
 J/ApJ/708/1335 : Spectroscopy of globulars in NGC 5128 (Woodley+, 2010)
 J/AJ/142/199   : Sizes and luminosities of stellar systems (Brodie+, 2011)
 J/AJ/143/84    : New candidate globular clusters in NGC 5128 (Harris+, 2012)
 J/ApJ/760/87   : Globular clusters of M60 with HST (Strader+, 2012)
 J/AJ/145/101   : Updated nearby galaxy catalog (Karachentsev+, 2013)
 J/MNRAS/445/2385 : HST/ACS Coma Cluster Survey. X. (den Brok+, 2014)
 J/MNRAS/441/3570 : Nuclear star clusters 228 spiral galaxies (Georgiev+, 2014)
 J/MNRAS/443/1151 : AIMSS Project. I. Compact Stellar Systems (Norris+, 2014)
 J/ApJ/812/34   : Properties UCD candidates in M87/M49/M60 regions (Liu+, 2015)
 J/MNRAS/457/2122 : Nuclear star clusters photometric masses (Georgiev+, 2016)
 J/A+A/586/A102 : UCDs in the halo of NGC1399 (Voggel+, 2016)
 J/MNRAS/469/3444 : Survey Centaurus A's Baryonic Structures II. (Taylor+, 2017)
 J/ApJ/858/102  : Gemini/NIFS and HST obs. of the galaxy M59-UCD3 (Ahn+, 2018)
 J/ApJ/878/18   : NGVS. XXIII. Nuclear star clusters (Sanchez-Janssen+, 2019)

Byte-by-byte Description of file: table2.dat
--------------------------------------------------------------------------------
   Bytes Format Units Label     Explanations
--------------------------------------------------------------------------------
   1-  8 A8     ---   KV19      KV19 sequential identifier
  10- 22 F13.9  deg   RAdeg     [198/205] Right Ascension (J2000)
  24- 37 F14.10 deg   DEdeg     [-46/-40] Declination (J2000)
  39- 43 F5.2   ---   AEN       [0.26/15.42] Gaia DR2 Astrometric Excess Noise
  45- 49 F5.2   mag   Gmag      [11.23/19.0] Gaia DR2 Gmag
  51- 54 F4.2   ---   BP-RP     [1.4/4.97] Gaia DR2 BP/RP Excess Factor
  56- 59 F4.2   mag   u-r       [0.41/3.41]? u-r color (1)
  61- 65 F5.2   mag   r-z       [-0.55/0.91]? r-z color (1)
  67- 71 F5.2   mag   rmag      [14.23/18.21]? r band magnitude (1)
  73- 76 F4.2   ---   Votes     [1/5]? final visual assessment score
  78- 81 F4.2   ---   CL        [0/5.08]? Cluster Likelihood
  83- 83 A1     ---   Rank      Rank
--------------------------------------------------------------------------------
Note (1): Colors and magnitudes from Taylor+, 2017, J/MNRAS/469/3444
    if available, and are all extinction corrected.
--------------------------------------------------------------------------------

Byte-by-byte Description of file: table3.dat
--------------------------------------------------------------------------------
   Bytes Format Units   Label  Explanations
--------------------------------------------------------------------------------
   1-  1 A1     ---     Label  New confirmed UCD labels
   3- 10 A8     ---     KV19   KV19 sequential identifier
  12- 22 F11.7  deg     RAdeg  [199/204] Right Ascension (J2000)
  24- 34 F11.7  deg     DEdeg  [-46/-41] Declination (J2000)
  36- 40 F5.2   mag     gmag   [15.18/18.3] apparent g band magnitude
  42- 47 F6.2   mag     gMAG   [-10.32/-9.61]? absolute g band magnitude
  49- 53 F5.1   km/s    RVel   [-95.2/719.2] Radial Velocity
  55- 58 F4.1   km/s  e_RVel   [1.2/32.7] Uncertainty in RVel
  60- 63 F4.1   ---     S/N    [5.2/23] Signal to noise
  65- 70 F6.4   ---     CL     [0.0001/5.08]? Cluster Likelihood
  72- 75 F4.2   ---     Votes  [1/3.75]? final visual assessment score
--------------------------------------------------------------------------------

Byte-by-byte Description of file: table4.dat
--------------------------------------------------------------------------------
   Bytes Format Units Label     Explanations
--------------------------------------------------------------------------------
   1-  8 A8     ---   Name      Taylor+, 2017, J/MNRAS/469/3444 designation
  10- 19 F10.6  deg   RAdeg     [200/202] Right Ascension (J2000)
  21- 30 F10.6  deg   DEdeg     [-44/-42] Declination (J2000)
  32- 36 F5.2   mag   Gmag      [17.39/19.54] Gaia DR2 G band magnitude
  38- 43 F6.3   ---   AEN       [1.76/15.29] Gaia DR2 Astrometric Excess Noise
  45- 48 F4.2   ---   BP-RP     [1.78/3.1] Gaia DR2 BP/RP Excess Factor
  50- 54 F5.2   mag   gmag      [17.02/18.77] g' band mag from Taylor+
--------------------------------------------------------------------------------

History:
    From electronic version of the journal

================================================================================
(End)                          Prepared by [AAS], Coralie Fix [CDS], 21-Oct-2021
