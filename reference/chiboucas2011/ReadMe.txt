J/ApJ/737/86      UCD galaxies in the Coma cluster          (Chiboucas+, 2011)
================================================================================
Ultra-compact dwarfs in the Coma cluster.
    Chiboucas K., Tully R.B., Marzke R.O., Phillipps S., Price J., Peng E.W.,
    Trentham N., Carter D., Hammer D.
   <Astrophys. J., 737, 86 (2011)>
   =2011ApJ...737...86C
================================================================================
ADC_Keywords: Clusters, galaxy ; Galaxies, spectra ; Radial velocities ;
              Photometry, HST
Keywords: galaxies: clusters: individual (Coma) - galaxies: dwarf -
          galaxies: star clusters: general - globular clusters: general

Abstract:
    We have undertaken a spectroscopic search for ultra-compact dwarf
    galaxies (UCDs) in the dense core of the dynamically evolved, massive
    Coma cluster as part of the Hubble Space Telescope/Advanced Camera for
    Surveys (HST/ACS) Coma Cluster Treasury Survey. UCD candidates were
    initially chosen based on color, magnitude, degree of resolution
    within the ACS images, and the known properties of Fornax and Virgo
    UCDs. Follow-up spectroscopy with Keck/Low-Resolution Imaging
    Spectrometer confirmed 27 candidates as members of the Coma cluster, a
    success rate >60% for targeted objects brighter than M_R_=-12. Another
    14 candidates may also prove to be Coma members, but low
    signal-to-noise spectra prevent definitive conclusions.

Description:
    This work is part of the larger Hubble Space Telescope (HST)/ACS Coma
    Cluster Treasury Survey (Carter et al. 2008ApJS..176..424C), a
    two-passband imaging survey designed to cover 740arcmin^2^ in the Coma
    cluster to a depth of I_C_~26.6mag for point sources.

    To choose a sample of potential UCDs, we first identified point
    sources in the catalog of Adami et al. (2006, Cat. J/A+A/451/1159)
    based on their large ground-based Coma cluster CFHT/CFH12K survey.

    We use the Keck/LRIS in multi-object spectroscopy mode. Four masks
    were observed over two nights, 2008 April 2-3. Another two masks were
    observed 2009 March 28-30. Observations and data reduction are further
    described in Chiboucas et al. (2010, Cat. J/ApJ/723/251).

File Summary:
--------------------------------------------------------------------------------
 FileName   Lrecl  Records   Explanations
--------------------------------------------------------------------------------
ReadMe         80        .   This file
table2.dat    123       49   Targeted ultra-compact dwarf galaxies (UCD)
                             candidates
table3.dat    123       29  *UCD sample 2
table4.dat     58       27   Effective radii
--------------------------------------------------------------------------------
Note on table3.dat: The second round of observations based on our expanded
   candidate sample (93 lower surface brightness galaxies observed concurrently
   with the 2008 four masks).
--------------------------------------------------------------------------------

See also:
 J/MNRAS/411/2439 : Coma Treasury Survey. Structural parameters (Hoyos+, 2011)
 J/ApJ/723/251    : Keck/LRIS confirmation of Coma membership (Chiboucas+, 2010)
 J/ApJS/191/143   : HST/ACS Coma cluster survey. II. (Hammer+, 2010)
 J/MNRAS/404/1745 : Dwarf galaxies in Coma supercluster (Mahajan+, 2010)
 J/MNRAS/392/1265 : Faint red galaxies in Coma cluster (Smith+, 2009)
 J/A+A/451/1159   : BVRI imaging of the Coma cluster (Adami+, 2006)
 J/ApJS/137/279   : Spectroscopic Survey in Coma (Mobasher+, 2001)
 J/A+A/296/643    : Low Surface Brightness galaxies in Coma (Karachentsev+ 1995)

Byte-by-byte Description of file: table[23].dat
--------------------------------------------------------------------------------
   Bytes Format Units      Label   Explanations
--------------------------------------------------------------------------------
   1-  6  A6    ---        Mmb     Membership status (1)
   8- 14  I7    ---        ID      [10355/8039100] Identification number (as in
                                   Chiboucas et al. 2010, Cat. J/ApJ/723/251),
                                   <[CTM2010] NNNNNNN> in Simbad
      15  A1    ---      f_ID      [f] f: object was observed in two masks
  17- 21  F5.2  mag        Rmag    [21.06/23.99]? R-band magnitude
  23- 27  F5.2  mag        Imag.c  ? F814W magnitude corrected (2)
  29- 33  F5.2  mag        Imag    [21.27/24.27]? HST/ACS F814W magnitude
  35- 38  F4.2  mag        B-V     ? B-V color index within a 3" aperture
  40- 43  F4.2  mag        g-i     ? g-i color index within a 2.25" aperture
  45- 49  F5.2 mag/arcsec2 mu0     [20/24]? Central surface brightness, R
  51- 55  F5.2 mag/arcsec2 <mu>e   ? Mean effective surface brightness, F814W
  57- 67  F11.7 deg        RAdeg   Right ascension in decimal degrees (J2000)
  69- 78  F10.7 deg        DEdeg   Declination in decimal degrees (J2000)
  80- 81  I2    ---        Field   [1/25]? ACS field
  83- 86  I4    ---        xpos    [181/4085]? x position in ACS field
  88- 91  I4    ---        ypos    [89/4102]? y position in ACS field
  93- 97  I5    km/s       czabs   [-200/81397]? Absorption radial velocity
  99-101  I3    km/s     e_czabs   [25/154]? czabs uncertainty (3)
 103-107  F5.2  aW/m2/nm   Rfx     [2.1/16.5]? Relative flux
                                   (in 10^-16^erg/s/cm2/{AA})
 109-112  F4.1  ---        S/N     [1.6/23.6]? Signal to noise ratio per {AA}
                                   around 5000{AA}
 114-119  I6    km/s       czem    [44454/161089]? Emission radial velocity
 121-123  I3    km/s     e_czem    [6/112]? czem uncertainty
--------------------------------------------------------------------------------
Note (1): Membership type as follows:
  Mem    = member. We assume that objects with radial velocities between
           4000km/s<V_r_<10000km/s, within 3{sigma} of the cluster mean, and
           with S/N>5 are cluster members. The spectra for the 19 confirmed
           UCDs in table2 are shown in figures 2-4. The spectra for the 8
           members in sample 2 (table 3) are shown in Figure 5.
  Uncert = highly uncertain member
  Bckgrd = Background galaxy
  Stars  = Foreground star
  Failed = Spectra with too low S/N to even attempt redshift measurements
Note (2): Kron magnitudes corrected for light loss due to the finite size of the
          Kron aperture as compared to the ACS PSF (Hammer et al.
          2010ApJS..191..143H).
Note (3): Includes measurement uncertainty and uncertainty in wavelength
          calibration shifts based on sky lines.
--------------------------------------------------------------------------------

Byte-by-byte Description of file: table4.dat
--------------------------------------------------------------------------------
  Bytes Format Units   Label  Explanations
--------------------------------------------------------------------------------
  1-  7  I7    ---    ID      [81669/2000005] Identification number
      8  A1    ---  f_ID      [b] flags a source outside ACS coverage (1)
 10- 14  F5.1  pc     ReGAL   [4.8/125.5]? GALFIT effective radius
 16- 19  F4.1  pc   e_ReGAL   [2.3/18.8]? ReGAL uncertainty
 21- 23  F3.1  ---    n       [1.7/7.9]? Sersic index
 25- 29  F5.2  mag    Imag    [21.29/23.17]? HST/ACS F814W magnitude
 31- 34  F4.2  ---    b/a     [0.64/1]? GALFIT minor to major axis ratio (2)
 36- 39  A4    ---    ---     [King ] ISHAPE profile
 41- 43  I3    ---    Mod     [30/100]? ISHAPE fitting King number
 45- 48  F4.1  pc     ReISH   [6/68.1]? ISHAPE effective radius
 50- 53  F4.1  pc   e_ReISH   [2.4/12.2]? ReISH uncertainty
 55- 58  F4.2  ---    b/aISH  [0.68/1]? ISHAPE minor to major axis ratio (2)
--------------------------------------------------------------------------------
Note (1): This object is outside of our ACS coverage. Although this object has
          been observed in archival WFPC2 images, the larger pixel scale makes
          size measurements for such small objects impossible.
Note (2): Typical uncertainties in b/a were 0.07 and 0.05 for Galfit and Ishape,
          respectively. However, for such small objects, we don't consider the
          axial ratio measurements to be very reliable.
--------------------------------------------------------------------------------

History:
    From electronic version of the journal

================================================================================
(End)                                     Emmanuelle Perret [CDS]    09-Jan-2013
