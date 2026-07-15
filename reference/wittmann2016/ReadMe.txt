J/MNRAS/459/4450    Peculiar compact stellar systems in Fornax (Wittmann+, 2016)
================================================================================
Peculiar compact stellar systems in the Fornax cluster.
    Wittmann C., Lisker T., Pasquali A., Hilker M., Grebel E.K.
   <Mon. Not. R. Astron. Soc., 459, 4450-4466 (2016)>
   =2016MNRAS.459.4450W    (SIMBAD/NED BibCode)
================================================================================
ADC_Keywords: Clusters, galaxy ; Radial velocities ; Morphology
Keywords: galaxies: clusters: individual: Fornax - galaxies: dwarf -
          galaxies: nuclei; galaxies: peculiar -
          galaxies: star clusters: general - galaxies: structure

Abstract:
    We search for hints to the origin and nature of compact stellar
    systems in the magnitude range of ultracompact dwarf galaxies in deep
    wide-field imaging data of the Fornax cluster core. We visually
    investigate a large sample of 355 spectroscopically confirmed cluster
    members with V-band equivalent magnitudes brighter than -10mag for
    faint extended structures. Our data reveal peculiar compact stellar
    systems, which appear asymmetric or elongated from their outer light
    distribution. We characterize the structure of our objects by
    quantifying their core concentration, as well as their outer asymmetry
    and ellipticity. For the brighter objects of our sample we also
    investigate their spatial and phase-space distribution within the
    cluster. We argue that the distorted outer structure alone that is
    seen for some of our objects, is not sufficient to decide whether
    these systems have a star cluster or a galaxy origin. However, we find
    that objects with low core concentration and high asymmetry (or high
    ellipticity) are primarily located at larger cluster-centric distances
    as compared to the entire sample. This supports the hypothesis that at
    least some of these objects may originate from tidally stripped
    galaxies.

Description:
    The data are fully characterized by Lisker et al. (2016, A&A,
    submitted). They were acquired in 2008 and 2010 with the WFI at the
    ESO/MPG 2.2m telescope (programmes 082.A-9016 and 084.A-9014, PI A.
    Pasquali, Guaranteed Time of the Max Planck Institute for Astronomy).
    We used a transparent filter that nearly equals the no-filter
    throughput (>10 per cent in the range 350-900nm) and thus provides
    a high signal-to-noise ratio.

File Summary:
--------------------------------------------------------------------------------
 FileName      Lrecl  Records   Explanations
--------------------------------------------------------------------------------
ReadMe            80        .   This file
table1.dat        69      904   Compilation of compact stellar systems known to
                                 be Fornax cluster members, based on previous
                                 publications
table3.dat        71      355   Parameter catalogue for the working sample of
                                 spectroscopically confirmed Fornax cluster
                                 members with m_Ve_<21.5mag
--------------------------------------------------------------------------------

Byte-by-byte Description of file: table1.dat
--------------------------------------------------------------------------------
   Bytes Format Units   Label     Explanations
--------------------------------------------------------------------------------
   1-  3  I3    ---     Seq       [1/904] Sequential number
   5-  6  I2    h       RAh       Right ascension (J2000)
   8-  9  I2    min     RAm       Right ascension (J2000)
  11- 15  F5.2  s       RAs       Right ascension (J2000)
      17  A1    ---     DE-       Declination sign (J2000)
  18- 19  I2    deg     DEd       Declination (J2000)
  21- 22  I2    arcmin  DEm       Declination (J2000)
  24- 27  F4.1  arcsec  DEs       Declination (J2000)
  29- 57  A29   ---     Simbad    Object identifier of the SIMBAD database,
                                   referring to the publication the object
                                   was taken from
  59- 62  I4    km/s    HV        Heliocentric velocity with the smallest error
                                   from all compiled velocities for an object
  64- 66  I3    km/s  e_HV        rms uncertainty in HV
  68- 69  I2    ---   r_HV        Literature source for the adopted velocity (1)
--------------------------------------------------------------------------------
Note (1): References as follows:
   1 = Schuberth et al. (2010, Cat. J/A+A/513/A52)
   2 = Dirsch et al. (2004, Cat. J/AJ/127/2114)
   3 = Bergond et al. (2007, Cat. J/A+A/464/L21)
   4 = Firth et al. (2007, Cat. J/MNRAS/382/1342)
   5 = Gregg et al. (2009, Cat. J/AJ/137/498)
   6 = Mieske et al. (2004, Cat. J/A+A/418/445)
   7 = Mieske et al. (2002, Cat. J/A+A/383/823)
   8 = Firth et al. (2008MNRAS.389.1539F)
   9 = Kissler-Patig et al. (1999AJ....117.1206K)
  10 = Drinkwater et al. (2000PASA...17..227D)
  11 = Kissler-Patig et al. (1998AJ....115..105K)
--------------------------------------------------------------------------------

Byte-by-byte Description of file: table3.dat
--------------------------------------------------------------------------------
   Bytes Format Units   Label     Explanations
--------------------------------------------------------------------------------
   1-  3  I3    ----    Seq       [1/904] Sequential number
   5- 10  F6.3  mag     Vemag     Apparent V-equivalent magnitude
  12- 16  F5.3  mag   e_Vemag     rms uncertainty on Vemag
      18  I1    ---   f_Vemag     [1/2] Magnitude flag (1)
  20- 24  F5.3  ---     CC        Core concentration (uncorrected values)
  26- 30  F5.3  ---     CCcorr    PSF-corrected core concentration
  32- 38  F7.3  ---     RA        ?=-99 Residual asymmetry
  40- 46  F7.3  ---   e_RA        ?=-99 rms uncertainty on RA
  48- 54  F7.3  ---     Ell       ?=-99 Ellipticity
  56- 62  F7.3  ---   e_Ell       ?=-99 rms uncertainty on Ell
  64- 65  I2    ---     Sub       ? Subsample (2)
  67- 68  I2    ---     SubAlt    ? Alternative subsample (2)
  70- 71  I2    ---     Region    PSF-region of the object
--------------------------------------------------------------------------------
Note (1): Magnitude flag as follows:
   1 = mag and e_mag obtained from SExtractor
   2 = mag and e_mag obtained from PSF-fitting
Note (2): Subsamples as follows:
   1 = cc+ra
   2 = cc+RA
   3 = CC+RA
   4 = cc+EL
   0 = SUB: object not part of any subsample
--------------------------------------------------------------------------------

History:
    From electronic version of the journal

================================================================================
(End)                                      Patricia Vannier [CDS]    27-Sep-2017
