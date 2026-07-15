J/ApJ/835/212  Wide-field spectrosc. survey of GCs in Virgo cluster  (Ko+, 2017)
================================================================================
To the edge of M87 and beyond: spectroscopy of intracluster globular clusters
and ultracompact dwarfs in the Virgo cluster.
    Ko Y., Hwang H.S., Lee M.G., Park H.S., Lim S., Sohn J., Jang I.S.,
    Hwang N., Park B.-G.
   <Astrophys. J., 835, 212-212 (2017)>
   =2017ApJ...835..212K    (SIMBAD/NED BibCode)
================================================================================
ADC_Keywords: Clusters, galaxy ; Photometry, ugriz ; Radial velocities ;
              Clusters, globular
Keywords: galaxies: clusters: individual: Virgo;
          galaxies: elliptical and lenticular, cD;
          galaxies: individual: M87; globular clusters: general;
          galaxies: kinematics and dynamics; galaxies: star clusters: general

Abstract:
    We present the results of a wide-field spectroscopic survey of
    globular clusters (GCs) in the Virgo cluster. We obtain spectra for
    201 GCs and 55 ultracompact dwarfs (UCDs) using Hectospec on the
    Multiple-Mirror Telescope and derive their radial velocities. We
    identify 46 genuine intracluster GCs (IGCs), not associated with any
    Virgo galaxies, using the 3D GMM test on the spatial and radial
    velocity distribution. They are located at a projected distance
    200kpc<~R<~500kpc from the center of M87. The radial velocity
    distribution of these IGCs shows two peaks, one at v_r_=1023km/s,
    associated with the Virgo main body, and another at v_r_=36km/s,
    associated with the infalling structure. The velocity dispersion of
    the IGCs in the Virgo main body is {sigma}_GC_~314km/s, which is
    smoothly connected to the velocity dispersion profile of M87 GCs but
    is much lower than that of dwarf galaxies in the same survey field,
    {sigma}_dwarf_~608km/s. The UCDs are more centrally concentrated on
    massive galaxies-M87, M86, and M84. The radial velocity dispersion of
    the UCD system is much smaller than that of dwarf galaxies. Our
    results confirm the large-scale distribution of Virgo IGCs indicated
    by previous photometric surveys. The color distribution of the
    confirmed IGCs shows a bimodality similar to that of M87 GCs. This
    indicates that most IGCs are stripped off dwarf galaxies and some off
    massive galaxies in the Virgo.

Description:
    We selected globular cluster (GC) candidates using the Next Generation
    Virgo Cluster Survey (NGVS; Ferrarese+ 2012ApJS..200....4F) archival
    images covering the central region of the Virgo cluster. The NGVS is a
    wide-field imaging survey of the Virgo cluster using MegaCam with a
    field of view of 1{deg}x1{deg} attached at the Canada-French-Hawaii
    Telescope.

    We carried out spectroscopic observation of GC candidates in the Virgo
    using the Hectospec mounted on the 6.5m Multiple-Mirror Telescope in
    queue mode under program ID 2014A-UAO-G18 (PI: Myung Gyoon Lee)
    between 2014 February and March (wavelength range: 3650{AA} to 9200{AA}).

File Summary:
--------------------------------------------------------------------------------
 FileName      Lrecl  Records   Explanations
--------------------------------------------------------------------------------
ReadMe            80        .   This file
table2.dat        76      635   Spectroscopic and photometric properties of
                                 foreground stars and background galaxies
table3.dat       119      633   Spectroscopic and photometric properties of
                                 the combined globular cluster (GC) sample
table4.dat       103      138   Spectroscopic and photometric properties of
                                 the combined ultracompact dwarf (UCD) sample
--------------------------------------------------------------------------------

See also:
 V/147 : The SDSS Photometric Catalogue, Release 12 (Alam+, 2015)
 J/AJ/90/1681    : The Virgo Cluster Catalog (VCC) (Binggeli+, 1985)
 J/A+AS/139/393  : Young Massive Star Clusters. II. (Larsen, 1999)
 J/A+A/383/823   : Radial velocities of UCOs in Fornax (Mieske+, 2002)
 J/A+A/464/L21   : Velocities of globular clusters in Fornax (Bergond+, 2007)
 J/ApJ/655/144   : ACS Virgo Cluster Survey. XIII. (Mei+, 2007)
 J/A+A/477/L9    : Globular clusters around NGC 1399 (Schuberth+, 2008)
 J/MNRAS/396/1075  : GC in nearby dwarf galaxies. II (Georgiev+, 2009)
 J/ApJS/180/54     : GC candidates in ACS Virgo survey. (Jordan+, 2009)
 J/ApJS/182/216    : Surface photometry of Virgo ellipticals (Kormendy+, 2009)
 J/MNRAS/402/803   : M31 globular cluster system (Peacock+, 2010)
 J/A+A/513/A52   : Velocities of NGC 1399 globular clusters (Schuberth+, 2010)
 J/AJ/142/199    : Sizes and luminosities of stellar systems (Brodie+, 2011)
 J/A+A/531/A4    : Ultra compact dwarfs and globulars in Hya I (Misgeld+, 2011)
 J/ApJS/197/33   : The M87 globular cluster system (Strader+, 2011)
 J/ApJ/748/29    : Spectroscopy of M87 globular clusters (Romanowsky+, 2012)
 J/ApJS/215/22   : The Extended Virgo Cluster Catalog (EVCC) (Kim+, 2014)
 J/ApJ/802/30    : NGVS VI. Ultra-compact dwarfs in M87 (Zhang+, 2015)
 J/MNRAS/455/820 : M87 globular cluster candidates catalog (Oldham+, 2016)
 J/ApJS/227/12   : NGVS XXV. Virgo globular clusters photometry (Powalka+, 2016)

Byte-by-byte Description of file: table2.dat
--------------------------------------------------------------------------------
   Bytes Format Units   Label  Explanations
--------------------------------------------------------------------------------
   1-  4 A4     ---     S/G    "STAR" or "GAL"
   5-  7 I03    ---     Seq    Running sequence number within S/G class
   9- 18 F10.6  deg     RAdeg  Right Ascension in decimal degrees (J2000)
  20- 28 F9.6   deg     DEdeg  Declination in decimal degrees (J2000)
  30- 35 F6.3   mag     imag   [17.1/21] CFHT/MegaCam i band AB magnitude
  37- 41 F5.3   mag   e_imag   [0/0.007] Error in imag
  43- 47 F5.3   mag     g-r    [0.3/1] The (g-r) color index
  49- 53 F5.3   mag   e_g-r    Error in g-r
  55- 59 F5.3   mag     g-i    [0.6/1.7] The (g-i) color index
  61- 65 F5.3   mag   e_g-i    Error in g-i
  67- 72 I6     km/s    HRV    [-295/240245] Heliocentric radial velocity
  74- 76 I3     km/s  e_HRV    [4/431] Error in HRV
--------------------------------------------------------------------------------

Byte-by-byte Description of file: table3.dat
--------------------------------------------------------------------------------
   Bytes Format Units   Label     Explanations
--------------------------------------------------------------------------------
   1-  6 A6     ---     ID        Identification (1)
   8- 17 F10.6  deg     RAdeg     Right Ascension in decimal degrees (J2000)
  19- 27 F9.6   deg     DEdeg     Declination in decimal degrees (J2000)
  29- 34 F6.3   mag     imag      [17.8/23.5] i band AB magnitude
  36- 40 F5.3   mag   e_imag      [0.001/0.02]? Error in imag
  42- 46 F5.3   mag     g-r       [0.3/0.9]? The (g-r) color index
  48- 52 F5.3   mag   e_g-r       ? Error in g-r
  54- 58 F5.3   mag     g-i       [0.6/1.3]? The (g-i) color index
  60- 64 F5.3   mag   e_g-i       ? Error in g-i
  66- 68 A3     ---   r_phot      Source of photometry (2)
  70- 73 I4     km/s    HRV       [-728/2777] Heliocentric radial velocity
  75- 77 I3     km/s  e_HRV       [5/114] Error in HRV
  79- 81 A3     ---   r_HRV       Source of HRV (2)
  83- 85 F3.1   pc      rh        [1.3/9.2]? Half-light radius
  87- 89 F3.1   pc    E_rh        [0/1.5]? Upper error in rh
  91- 93 F3.1   pc    e_rh        [0/1.1]? Lower error in rh
  95- 97 A3     ---   r_rh        ? Source of rh (2)
  99-111 A13    ---     Gal1      Host galaxy determined by Mclust method (3)
 113-119 A7     ---     Gal2      Host galaxy determined by Rv cut method
--------------------------------------------------------------------------------
Note (1): GCNNN for sources from this study or HNNNNN/TNNNNN for sources from
          Strader et al. (2011, J/ApJS/197/33; <[SRB2011] {HT}NNNNN> in Simbad)
          or SNNNN for sources from Hanes+, 2001, J/ApJ/559/812;
          <[SFH81] NNNN> in Simbad.
Note (2): Reference as follows:
    K16 = this study.
    S11 = Strader et al. (2011, J/ApJS/197/33).
    J09 = Jordan et al. (2009, J/ApJS/180/54).
          The magnitudes of this study and S11 are CFHT/MegaCam AB
          and dereddened SDSS AB magnitudes, respectively.
Note (3): The Mclust subgroup that a given UCD belongs to is in parentheses.
--------------------------------------------------------------------------------

Byte-by-byte Description of file: table4.dat
--------------------------------------------------------------------------------
   Bytes Format Units   Label  Explanations
--------------------------------------------------------------------------------
   1-  9 A9     ---     ID     Identification (1)
  11- 20 F10.6  deg     RAdeg  Right Ascension in decimal degrees (J2000)
  22- 30 F9.6   deg     DEdeg  Declination in decimal degrees (J2000)
  32- 37 F6.3   mag     imag   [17.5/22.3] i band AB magnitude
  39- 43 F5.3   mag   e_imag   [0.001/0.02]? Error in imag
  45- 49 F5.3   mag     g-r    [0.4/0.8]? The (g-r) color index
  51- 55 F5.3   mag   e_g-r    ? Error in g-r
  57- 61 F5.3   mag     g-i    [0.6/1.2]? The (g-i) color index
  63- 67 F5.3   mag   e_g-i    ? Error in g-i
  69- 71 A3     ---   r_phot   Source of photometry (2)
  73- 76 I4     km/s    HRV    [-416/2419] Heliocentric radial velocity
  78- 80 I3     km/s  e_HRV    [2/146] Error in HRV
  82- 84 A3     ---   r_HRV    Source of HRV (2)
  86- 89 F4.1   pc      rh     [0.6/40.2]? Half-light radius
  91- 93 F3.1   pc    E_rh     [0/8.4]? Upper error in rh
  95- 97 F3.1   pc    e_rh     [0/8.4]? Lower error in rh
  99-101 A3     ---   r_rh     ? Source of rh (2)
 103-103 A1     ---     Mcl    [A-C] Mclust subgroup that a given UCD belongs to
--------------------------------------------------------------------------------
Note (1): UCDNN for sources from this study or M87UCD-NN for sources from
          Zhang et al. (2015, J/ApJ/802/30; <[ZPC2015] M87UCD NN> in Simbad) or
          SNNNN for sources from Hanes+, 2001, J/ApJ/559/812;
          <[SFH81] NNNN> in Simbad or HNNNNN/TNNNNN for sources from
          Strader et al. (2011, J/ApJS/197/33; <[SRB2011] {HT}NNNNN> in Simbad).
Note (2): Reference as follows:
    K16 = this study.
    Z15 = Zhang et al. (2015, J/ApJ/802/30).
    J09 = Jordan et al. (2009, J/ApJS/180/54).
          The magnitudes of this study and Z15 are CFHT/MegaCam AB and
          dereddened SDSS AB magnitudes, respectively.
--------------------------------------------------------------------------------

History:
    From electronic version of the journal

================================================================================
(End)                  Prepared by [AAS], Emmanuelle Perret [CDS]    31-Aug-2017
