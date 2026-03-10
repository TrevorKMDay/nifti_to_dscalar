#!/bin/bash

dscalar=102109_tfMRI_LANGUAGE_level2_hp200_s4.dscalar.nii

wb_command -cifti-create-dense-from-template    \
    ${dscalar}                                  \
    test                                        \
    -metric CORTEX_LEFT  102109.L.midthickness.164k_fs_LR.surf.gii \
    -metric CORTEX_RIGHT 102109.R.midthickness.164k_fs_LR.surf.gii
