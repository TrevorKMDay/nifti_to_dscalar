#!/bin/bash

python nifti_to_dscalar.py -v \
    -wm   sub-BLFU100619_ses-BLFU1_space-fsLR_den-32k_hemi-{L,R}_white.surf.gii \
    -pial sub-BLFU100619_ses-BLFU1_space-fsLR_den-32k_hemi-{L,R}_pial.surf.gii \
    sub-BLFU100619_ses-BLFU1_space-fsLR_den-32k_hemi-{L,R}_desc-hcp_midthickness.surf.gii \
    sub-BLFU100619_ses-BLFU1_con-CmS_stat-tstat.nii.gz
