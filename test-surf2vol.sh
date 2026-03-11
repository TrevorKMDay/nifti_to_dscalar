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

for cope in {1..6} ; do

    dscalar=101915/tfMRI_LANGUAGE_hp200_s4_level2.feat/GrayordinatesStats/cope${cope}.feat/tstat1.dtseries.nii

    echo "Separating ${cope}"
    wb_command -cifti-separate                      \
        "${dscalar}"                                \
        COLUMN                                      \
        -metric CORTEX_LEFT  "101915/cope-${cope}_L.func.gii"   \
        -metric CORTEX_RIGHT "101915/cope-${cope}_R.func.gii"

    for LR in L R ; do

        echo "Starting ${cope} ${LR}"

        wb_command -metric-to-volume-mapping                        \
            "101915/cope-${cope}_${LR}.func.gii"                       \
            101915/101915.${LR}.midthickness.32k_fs_LR.surf.gii     \
            101915/T1w.nii.gz                                       \
            "101915/test_${cope}_${LR}.nii.gz"                         \
            -ribbon-constrained                                     \
                101915/101915.${LR}.white.32k_fs_LR.surf.gii        \
                101915/101915.${LR}.pial.32k_fs_LR.surf.gii

    done

    fslmaths \
        "101915/test_${cope}_L.nii.gz"         \
        -add "101915/test_${cope}_R.nii.gz"    \
        "101915/cope_${cope}.nii.gz"

done