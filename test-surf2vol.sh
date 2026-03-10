#!/bin/bash

# dscalar=102109_tfMRI_LANGUAGE_level2_hp200_s4.dscalar.nii

# wb_command -cifti-separate                      \
#     ${dscalar}                                  \
#     COLUMN                                      \
#     -metric CORTEX_LEFT  cortex_L.func.gii   \
#     -metric CORTEX_RIGHT cortex_R.func.gii

# for i in L R ; do

#     echo "Starting ${i}"

#     wb_command -metric-to-volume-mapping            \
#         cortex_${i}.func.gii                        \
#         102109.${i}.midthickness.32k_fs_LR.surf.gii    \
#         T1w.nii.gz                                  \
#         test_${i}.nii.gz                            \
#         -ribbon-constrained                         \
#             102109.${i}.white.32k_fs_LR.surf.gii    \
#             102109.${i}.pial.32k_fs_LR.surf.gii

# done

# fslmaths test_L.nii.gz -add test_R.nii.gz test.nii.gz

# Do this with somebody that has both vol and surf

dscalar=101915/tfMRI_LANGUAGE_hp200_s4_level2.feat/GrayordinatesStats/cope4.feat/tstat1.dtseries.nii

echo "Separating"
wb_command -cifti-separate                      \
    ${dscalar}                                  \
    COLUMN                                      \
    -metric CORTEX_LEFT  101915/cortex_L.func.gii   \
    -metric CORTEX_RIGHT 101915/cortex_R.func.gii

for i in L R ; do

    echo "Starting ${i}"

    wb_command -metric-to-volume-mapping                    \
        101915/cortex_${i}.func.gii                         \
        101915/101915.${i}.midthickness.32k_fs_LR.surf.gii  \
        101915/T1w.nii.gz                                   \
        101915/test_${i}.nii.gz                             \
        -ribbon-constrained                                 \
            101915/101915.${i}.white.32k_fs_LR.surf.gii     \
            101915/101915.${i}.pial.32k_fs_LR.surf.gii

done

fslmaths 101915/test_L.nii.gz -add 101915/test_R.nii.gz 101915/test.nii.gz