J/A+A/625/A50       Ultra compact dwarf galaxies catalog        (Fahrion+, 2019)
================================================================================
Single metal-poor ultra compact dwarf galaxy at one kiloparsec distance from the
low-mass elliptical galaxy FCC 47.
    Fahrion K., Georgiev I., Hilker M., Lyubenova M., van de Ven G.,
    Alfaro-Cuello M., Corsini E.M., Sarzi M., McDermid R.M., de Zeeuw T.
    <Astron. Astrophys. 625, A50 (2019)>
    =2019A&A...625A..50F        (SIMBAD/NED BibCode)
================================================================================
ADC_Keywords: Galaxy catalogs ; Radial velocities ; Morphology
Keywords: galaxies: individual: NGC 1336 - galaxies: dwarf -
          galaxies: nuclei - galaxies: kinematics and dynamics

Abstract:
    Photometric surveys of galaxy clusters have revealed a large number of
    ultra compact dwarfs (UCDs) around predominantly massive elliptical
    galaxies. Their origin is still debated as some UCDs are considered to
    be the remnant nuclei of stripped dwarf galaxies while others seem to
    mark the high-mass end of the star cluster population.

    We aim to characterize the properties of a UCD found at very close
    projected distance (r_wproj_=1.1kpc) from the centre of the low-mass
    (M~10^10^M_{sun}_) early-type galaxy FCC 47. This is a serendipitous
    discovery from MUSE adaptive optics science verification data. We
    explore the potential origin of this UCD as either a massive cluster
    or the remnant nucleus of a dissolved galaxy.

    We used archival Hubble Space Telescope data to study the photometric
    and structural properties of FCC 47-UCD1. In the MUSE data, the UCD is
    unresolved, but we used its spectrum to determine the radial velocity
    and metallicity.

    The surface brightness of FCC 47-UCD1 is best described by a single
    King profile with low concentration C=Rt/Rc~10 and large effective
    radius (r_eff_=24pc). Its integrated magnitude and blue colour
    (Mg=-10.55mag, (g-z)=1.46mag) combined with a metallicity of
    [M/H]=-1.12+/-0.10dex and an age >8Gyr obtained from the full fitting
    of the MUSE spectrum suggests a stellar population mass of
    M*=4.87x10^6^M_{sun}_. The low S/N of the MUSE spectrum prevents
    detailed stellar population analysis. Due to the limited spectral
    resolution of MUSE, we can only give an upper limit on the velocity
    dispersion ({sigma}<17km/s), and consequently on its dynamical mass
    (M_dyn_<1.3x10^7^M_{sun}_).

    The origin of the UCD cannot be constrained with certainty. The low
    metallicity, old age, and magnitude are consistent with a star cluster
    origin, whereas the extended size is consistent with an origin as the
    stripped nucleus of a dwarf galaxy with a initial stellar mass of a
    few 10^8^M_{sun}_.

Description:
    File tableb1 contains a compilation of literature ultra compact dwarf
    galaxies. For each UCD, name, host name, coordinates, radial velocity,
    the projected distance to the host galaxy and the reference are given.

File Summary:
--------------------------------------------------------------------------------
 FileName      Lrecl  Records   Explanations
--------------------------------------------------------------------------------
ReadMe            80        .   This file
tableb1.dat       89      381   Table of literature UCDs
--------------------------------------------------------------------------------

See also:
         V/143    : Revised Bologna Catalog of M31 clusters, V.5 (Galleti+ 2012)
 J/A+A/416/917    : Revised Bologna Catalog of M31 globular clusters
                                                                (Galleti+, 2004)
 J/MNRAS/414/3699 : Study of hot stellar systems and galaxies (Misgeld+, 2011)
 J/A+A/472/111    : Centaurus Compact Object Survey (Mieske+, 2007)
 J/ApJ/812/34     : Properties of UCD candidates in M87/M49/M60 regions
                                                                 (Liu+, 2015)
 J/AJ/142/199     : Sizes and luminosities of stellar systems (Brodie+, 2011)

Byte-by-byte Description of file:tableb1.dat
--------------------------------------------------------------------------------
   Bytes Format Units   Label     Explanations
--------------------------------------------------------------------------------
   1- 19  A19   ---     Name      Name of the UCD
  21- 35  A15   ---     Host      Name of the host galaxy
  37- 38  I2    h       RAh       ? Right ascension (J2000)
  40- 41  I2    min     RAm       ? Right ascension (J2000)
  43- 47  F5.2  s       RAs       ? Right ascension (J2000)
      49  A1    ---     DE-       Declination sign (J2000)
  50- 51  I2    deg     DEd       ? Declination (J2000)
  53- 54  I2    arcmin  DEm       ? Declination (J2000)
  56- 60  F5.2  arcsec  DEs       ? Declination (J2000)
  62- 67  F6.1  km/s    RV        Radial velocity
  69- 74  F6.2  mag     VMAG      Absolute V band magnitude
  76- 80  F5.1  kpc     rproj     Projected distance to host
  82- 86  F5.2  pc      reff      Effective radius
  88- 89  I2    ---     Ref       [0/13]? Reference number (1)
--------------------------------------------------------------------------------
Note (1): Reference as follows:
       0 = This work
       1 = Mieske et al. (2008A&A...487..921M), some positions from
            Brodie et al. (2011AJ....142..199B, Cat. J/AJ/142/199) and
            Misgeld & Hilker (2011MNRAS.414.3699M, Cat. J/AJ/142/199)
       2 = Brodie et al. (2011AJ....142..199B, Cat. J/AJ/142/199)
       3 = Liu et al. (2015ApJ...812...34L, Cat. J/ApJ/812/34)
       4 = Norris & Kannappan (2011MNRAS.414..739N)
       5 = Maraston et al. (2003IAUJD...6E..18M)
       6 = Ma et al. (2017MNRAS.468.4513M)
       7 = Evstigneeva et al. (2007AJ....133.1722E)
       8 = Mieske et al. (2007A&A...472..111M, Cat. J/A+A/472/111)
       9 = Mieske et al. (2009A&A...498..705M)
      10 = Misgeld et al. (2011MNRAS.414.3699M, Cat. J/MNRAS/414/3699)
      11 = Galleti et al. (2004A&A...416..917G, Cat. J/A+A/416/917)
      12 = Sandoval et al. (2015ApJ...808L..32S)
      13 = Janz et al. (2016MNRAS.456..617J)
--------------------------------------------------------------------------------

Acknowledgements:
    Katja Fahrion, kfahrion(at)eso.org

================================================================================
(End)                                        Patricia Vannier [CDS]  03-Apr-2019
