SELECT 
	
	-- Basic information 
	f1.object_id, f1.ra, f1.dec, f1.tract, f1.patch, f1.parent_id,
	
	-- Galactic extinction 
	f1.a_g, f1.a_r, f1.a_i, f1.a_z, f1.a_y,
	
	-- Photometry
	
	--- cmodel 
	---- Exp
	f1.g_cmodel_exp_flux, f1.r_cmodel_exp_flux, f1.i_cmodel_exp_flux, f1.z_cmodel_exp_flux, f1.y_cmodel_exp_flux,
	f1.g_cmodel_exp_fluxsigma, f1.r_cmodel_exp_fluxsigma, f1.i_cmodel_exp_fluxsigma, f1.z_cmodel_exp_fluxsigma, f1.y_cmodel_exp_fluxsigma,
	
	---- Dev
	f1.g_cmodel_dev_flux, f1.r_cmodel_dev_flux, f1.i_cmodel_dev_flux, f1.z_cmodel_dev_flux, f1.y_cmodel_dev_flux,
	f1.g_cmodel_dev_fluxsigma, f1.r_cmodel_dev_fluxsigma, f1.i_cmodel_dev_fluxsigma, f1.z_cmodel_dev_fluxsigma, f1.y_cmodel_dev_fluxsigma,
	
	---- Total
	f1.g_cmodel_flux, f1.r_cmodel_flux, f1.i_cmodel_flux, f1.z_cmodel_flux, f1.y_cmodel_flux,
	f1.g_cmodel_fluxsigma, f1.r_cmodel_fluxsigma, f1.i_cmodel_fluxsigma, f1.z_cmodel_fluxsigma, f1.y_cmodel_fluxsigma,
	f1.g_cmodel_mag, f1.r_cmodel_mag, f1.i_cmodel_mag, f1.z_cmodel_mag, f1.y_cmodel_mag,
	f1.g_cmodel_magsigma, f1.r_cmodel_magsigma, f1.i_cmodel_magsigma, f1.z_cmodel_magsigma, f1.y_cmodel_magsigma,
	
	---- fracDev
	f1.g_cmodel_fracdev, f1.r_cmodel_fracdev, f1.i_cmodel_fracdev, f1.z_cmodel_fracdev, f1.y_cmodel_fracdev,

	---- flag
	f1.g_cmodel_flag, f1.r_cmodel_flag, f1.i_cmodel_flag, f1.z_cmodel_flag, f1.y_cmodel_flag,
	
	--- PSF
	f2.g_psfflux_flux, f2.r_psfflux_flux, f2.i_psfflux_flux, f2.z_psfflux_flux, f2.y_psfflux_flux,
	f2.g_psfflux_fluxsigma, f2.r_psfflux_fluxsigma, f2.i_psfflux_fluxsigma, f2.z_psfflux_fluxsigma, f2.y_psfflux_fluxsigma,
	f2.g_psfflux_mag, f2.r_psfflux_mag, f2.i_psfflux_mag, f2.z_psfflux_mag, f2.y_psfflux_mag,
	f2.g_psfflux_magsigma, f2.r_psfflux_magsigma, f2.i_psfflux_magsigma, f2.z_psfflux_magsigma, f2.y_psfflux_magsigma,
	
	---- flag
	f2.g_psfflux_flag, f2.r_psfflux_flag, f2.i_psfflux_flag, f2.z_psfflux_flag, f2.y_psfflux_flag,
	
	--- Afterburner 
	---- Seeing
	f5.g_undeblended_convolvedflux_seeing, f5.r_undeblended_convolvedflux_seeing, f5.i_undeblended_convolvedflux_seeing,
	f5.z_undeblended_convolvedflux_seeing, f5.y_undeblended_convolvedflux_seeing,
	
	---- Seeing: 1".1; 6 pixel aperture
	f5.g_undeblended_convolvedflux_2_20_flux, f5.r_undeblended_convolvedflux_2_20_flux, f5.i_undeblended_convolvedflux_2_20_flux,
	f5.z_undeblended_convolvedflux_2_20_flux, f5.y_undeblended_convolvedflux_2_20_flux,
	f5.g_undeblended_convolvedflux_2_20_fluxsigma, f5.r_undeblended_convolvedflux_2_20_fluxsigma, f5.i_undeblended_convolvedflux_2_20_fluxsigma,
	f5.z_undeblended_convolvedflux_2_20_fluxsigma, f5.y_undeblended_convolvedflux_2_20_fluxsigma,

	---- Seeing: 1".4; 6 pixel aperture
	f5.g_undeblended_convolvedflux_3_20_flux, f5.r_undeblended_convolvedflux_3_20_flux, f5.i_undeblended_convolvedflux_3_20_flux,
	f5.z_undeblended_convolvedflux_3_20_flux, f5.y_undeblended_convolvedflux_3_20_flux,
	f5.g_undeblended_convolvedflux_3_20_fluxsigma, f5.r_undeblended_convolvedflux_3_20_fluxsigma, f5.i_undeblended_convolvedflux_3_20_fluxsigma,
	f5.z_undeblended_convolvedflux_3_20_fluxsigma, f5.y_undeblended_convolvedflux_3_20_fluxsigma,
	
	---- flag
	f5.g_undeblended_convolvedflux_2_deconv, f5.r_undeblended_convolvedflux_2_deconv, f5.i_undeblended_convolvedflux_2_deconv, 
	f5.z_undeblended_convolvedflux_2_deconv, f5.y_undeblended_convolvedflux_2_deconv,
	f5.g_undeblended_convolvedflux_3_deconv, f5.r_undeblended_convolvedflux_3_deconv, f5.i_undeblended_convolvedflux_3_deconv, 
	f5.z_undeblended_convolvedflux_3_deconv, f5.y_undeblended_convolvedflux_3_deconv,
	f5.g_undeblended_convolvedflux_2_20_flag, f5.r_undeblended_convolvedflux_2_20_flag, f5.i_undeblended_convolvedflux_2_20_flag, 
	f5.z_undeblended_convolvedflux_2_20_flag, f5.y_undeblended_convolvedflux_2_20_flag,
	f5.g_undeblended_convolvedflux_3_20_flag, f5.r_undeblended_convolvedflux_3_20_flag, f5.i_undeblended_convolvedflux_3_20_flag, 
	f5.z_undeblended_convolvedflux_3_20_flag, f5.y_undeblended_convolvedflux_3_20_flag,
	
	-- Flags
	---- pixel flags
	f1.g_pixelflags, f1.r_pixelflags, f1.i_pixelflags, f1.z_pixelflags, f1.y_pixelflags, 
	
	---- pixel edge
	f1.g_pixelflags_edge, f1.r_pixelflags_edge, f1.i_pixelflags_edge, f1.z_pixelflags_edge, f1.y_pixelflags_edge, 

	---- pixel interpolated
	f1.g_pixelflags_interpolated, f1.r_pixelflags_interpolated, f1.i_pixelflags_interpolated, f1.z_pixelflags_interpolated, 
	f1.y_pixelflags_interpolated,

	---- pixel saturated
	f1.g_pixelflags_saturated, f1.r_pixelflags_saturated, f1.i_pixelflags_saturated, f1.z_pixelflags_saturated, 
	f1.y_pixelflags_saturated,

	---- pixel cr
	f1.g_pixelflags_cr, f1.r_pixelflags_cr, f1.i_pixelflags_cr, f1.z_pixelflags_cr, f1.y_pixelflags_cr, 

	---- pixel bad
	f1.g_pixelflags_bad, f1.r_pixelflags_bad, f1.i_pixelflags_bad, f1.z_pixelflags_bad, f1.y_pixelflags_bad, 

	---- pixel suspect
	f1.g_pixelflags_suspect, f1.r_pixelflags_suspect, f1.i_pixelflags_suspect, f1.z_pixelflags_suspect, f1.y_pixelflags_suspect, 

	---- pixel clipped 
	f1.g_pixelflags_clipped, f1.r_pixelflags_clipped, f1.i_pixelflags_clipped, f1.z_pixelflags_clipped, 
	f1.y_pixelflags_clipped,

	---- pixel reject 
	f1.g_pixelflags_rejected, f1.r_pixelflags_rejected, f1.i_pixelflags_rejected, f1.z_pixelflags_rejected,
	f1.y_pixelflags_rejected,

	---- pixel inexact psf
	f1.g_pixelflags_inexact_psf, f1.r_pixelflags_inexact_psf, f1.i_pixelflags_inexact_psf, 
	f1.z_pixelflags_inexact_psf, f1.y_pixelflags_inexact_psf,
	
	---- pixel interpolated center
	f1.g_pixelflags_interpolatedcenter, f1.r_pixelflags_interpolatedcenter, f1.i_pixelflags_interpolatedcenter, 
	f1.z_pixelflags_interpolatedcenter, f1.y_pixelflags_interpolatedcenter,

	---- pixel saturated center
	f1.g_pixelflags_saturatedcenter, f1.r_pixelflags_saturatedcenter, f1.i_pixelflags_saturatedcenter, f1.z_pixelflags_saturatedcenter, 
	f1.y_pixelflags_saturatedcenter,

	---- pixel cr center
	f1.g_pixelflags_crcenter, f1.r_pixelflags_crcenter, f1.i_pixelflags_crcenter, f1.z_pixelflags_crcenter, f1.y_pixelflags_crcenter, 
	
	---- pixel suspect center
	f1.g_pixelflags_suspectcenter, f1.r_pixelflags_suspectcenter, f1.i_pixelflags_suspectcenter, f1.z_pixelflags_suspectcenter, 
	f1.y_pixelflags_suspectcenter, 
	
	---- pixel clipped center
	f1.g_pixelflags_clippedcenter, f1.r_pixelflags_clippedcenter, f1.i_pixelflags_clippedcenter, f1.z_pixelflags_clippedcenter, 
	f1.y_pixelflags_clippedcenter,	
	
	---- pixel reject center
	f1.g_pixelflags_rejectedcenter, f1.r_pixelflags_rejectedcenter, f1.i_pixelflags_rejectedcenter, f1.z_pixelflags_rejectedcenter,
	f1.y_pixelflags_rejectedcenter,

	---- pixel inexact psf center
	f1.g_pixelflags_inexact_psfcenter, f1.r_pixelflags_inexact_psfcenter, f1.i_pixelflags_inexact_psfcenter, 
	f1.z_pixelflags_inexact_psfcenter, f1.y_pixelflags_inexact_psfcenter,

	---- pixel bright object 
	f1.g_pixelflags_bright_object, f1.r_pixelflags_bright_object, f1.i_pixelflags_bright_object, 
	f1.z_pixelflags_bright_object, f1.y_pixelflags_bright_object, 
	
	---- pixel bright object center
	f1.g_pixelflags_bright_objectcenter, f1.r_pixelflags_bright_objectcenter, f1.i_pixelflags_bright_objectcenter, 
	f1.z_pixelflags_bright_objectcenter, f1.y_pixelflags_bright_objectcenter, 
	
	-- Meta information 
	---- input count
	f1.g_inputcount_value, f1.r_inputcount_value, f1.i_inputcount_value, f1.z_inputcount_value, f1.y_inputcount_value, 
	
	---- extendedness
	f1.g_extendedness_value, f1.r_extendedness_value, f1.i_extendedness_value, f1.z_extendedness_value, f1.y_extendedness_value,
	f1.g_extendedness_flag, f1.r_extendedness_flag, f1.i_extendedness_flag, f1.z_extendedness_flag, f1.y_extendedness_flag,
	
	---- background 
	f1.g_localbackground_flux, f1.r_localbackground_flux, f1.i_localbackground_flux, f1.z_localbackground_flux, f1.y_localbackground_flux 
	
	
FROM
	s18a_wide.forced AS f1
	LEFT JOIN s18a_wide.forced2 AS f2 USING (object_id)
	LEFT JOIN s18a_wide.forced5 AS f5 USING (object_id)
	
WHERE

	f1.isprimary = True
AND f1.nchild = 0
	
	-- Rough FDFC cuts
AND f1.g_inputcount_value >= 4
AND f1.r_inputcount_value >= 4
AND f1.i_inputcount_value >= 5
AND f1.z_inputcount_value >= 6
AND f1.y_inputcount_value >= 6

    -- Extended objects
AND f1.g_extendedness_value < 1
AND f1.r_extendedness_value < 1
AND f1.i_extendedness_value < 1
AND f1.z_extendedness_value < 1

	-- PSF magnitude limited 
AND f2.i_psfflux_mag >= 17.5
AND f2.i_psfflux_mag <= 19.5
AND (f2.g_psfflux_mag - f2.r_psfflux_mag) > 0.50
AND (f2.g_psfflux_mag - f2.r_psfflux_mag) < 0.75
AND (f2.r_psfflux_mag - f2.i_psfflux_mag) > 0.18
AND (f2.r_psfflux_mag - f2.i_psfflux_mag) < 0.40
AND (f2.i_psfflux_mag - f2.z_psfflux_mag) > 0.05
AND (f2.i_psfflux_mag - f2.z_psfflux_mag) < 0.35

	-- Detected in all five bands
AND f1.merge_peak_g is True
AND (f1.merge_peak_r is True OR merge_peak_r2 is True)
AND (f1.merge_peak_i is True OR merge_peak_i2 is True)
AND f1.merge_peak_z is True
AND f1.merge_peak_y is True

	-- Pixel flag
AND f1.g_pixelflags is not True
AND f1.r_pixelflags is not True
AND f1.i_pixelflags is not True
AND f1.z_pixelflags is not True
