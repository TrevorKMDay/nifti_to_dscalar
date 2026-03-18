# nifti_to_dscalar

This script wraps all the functions you need to move data between volume
(NIFTI) and surface (CIFTI) spaces. You need your data, and minimally, the 
midthickness files. 

This script uses the convention that, when paired, the order is always left,
right. For all methods, use `enclosing` for label values.

All methods depend on `wb_command` being available on your system. Currently,
there is no flag to supply a path.

## Shared options

    --midthickness SURF SURF, -M SURF SURF
                            Left and right midthickness files
                            Required for both directions.

    --inner_surfaces SURF SURF, -wm SURF SURF
                            WM surfaces to use ribbon enclosed projection. L/R.
                            Must be used with --outer_surfaces.
    --outer_surfaces SURF SURF, -pial SURF SURF
                            Pial surfaces to use ribbon enclosed projection. L/R.
                            Must be used with --inner_surfaces

    -h, --help            show this help message and exit
    --verbose, -v         Does what a --verbose flag usually does.
    --overwrite           If set, will overwrite output files.
    --output_name OUTPUT_NAME [OUTPUT_NAME ...], -o OUTPUT_NAME [OUTPUT_NAME ...]
                            Output name (without suffix).
                            Must be same length as input.

Use `--output_name` to set the prefixes. Must be the same length as the input
list. Automatically adds suffixes (`.dscalar.nii`, `.nii.gz` as appropriate).

If supplied, both `--inner_surfaces` and `--outer_surfaces` must be used,
both with two sets of surfaces files. These are used in both directions to
refine the projection, but both directions can be done without inner/outer
surfaces.

## Volume to CIFTI mapping

At the most basic, all you need is two surfaces (left/right `.surf.gii`) and a
NIFTI (`.nii.gz`):

    python nifti_to_dscalar.py \
        --midthickness left.surf.gii right.surf.gii \
        --to_dscalar   nifti.nii.gz

You can supply multiple NIFTIs to apply the same transformations too.

### Ribbon-enclosed

To use the `-ribbon-enclosed` mapping, simply supply the inner (WM) and outer
(pial) surface files. Two each: left, right. The default ribbon mapping is
weighted averaging, use `--rc_method` to change that.

### All options

    --to_dscalar NIFTI [NIFTI ...]
                            A list of NIFTI files to convert to surface.

    NIFTI to surface:
    --method {trilinear,cubic,enclosing}, -m {trilinear,cubic,enclosing}
                            Method to use.
                            Use 'enclosing' for labels.
                            Conflicts with ribbon-constrained, use --rc_method
                            .Default: 'trilinear'.
    --rc_method {weighted_avg,trilinear,cubic,enclosing}
                            Method to use for ribbon-constrained mapping.
                            Default: 'weighted_avg'.

## CIFTI to volume mapping

This script can also project `dscalar` and `dtseries` files to NIFTI space.
This requires the midthickness files as well, and a volume reference
(`--volume_ref`).

This method depends on FSL tools being installed on your system. There is
currently no option to pass an FSL path.

Additionally, currently, the subcortical data is not added to the output.

At the most basic:

    python nifti_to_dscalar.py -v \
        --to_nifti     ${path}/cope1.feat/tstat1.dtseries.nii \
        --midthickness 101915/101915.{L,R}.midthickness.32k_fs_LR.surf.gii \
        --volume_ref   101915/T1w.nii.gz

You can use the `--nearest_vertex` method (default, defaults to 2 mm, and
faster), or provide the
WM/pial (inner/outer) surfaces for a slower, but more accurate mapping.
Adding the `--*_surfaces` flags will overrule any use of the `--nearest_vertex`
flag.

(The use of 2 mm was arbitrary. Please suggest a better number.)

Example usage:

    python nifti_to_dscalar.py -v \
        --to_nifti       ${path}/cope1.feat/tstat1.dtseries.nii \
        --midthickness   101915/101915.{L,R}.midthickness.32k_fs_LR.surf.gii \
        --volume_ref     101915/T1w.nii.gz \
        --inner_surfaces 101915/101915.{L,R}.white.32k_fs_LR.surf.gii \
        --outer_surfaces 101915/101915.{L,R}.pial.32k_fs_LR.surf.gii \
        --output_name    tstat1_ribconst

## Applying a warp to the resulting NIFTI

Applying a warp to the new NIFTI is a common need, so this script supplies an
argument, `--apply_after_warp 0/1 warp_file ref suffix`. 

- The first 0/1 indicates whether to keep the unwarped file
    (i.e., 0 = delete it, 1 = keep both).
- The second argument is a warp file.
- The third argument is the volume reference (for dimensions and FOV)
- The fourth argument adds a suffix, suggested: `desc-warped` or
  `space-SPACE`. This is added to the `output_name`.

This argument requires FSL to be available on your path. There is currently no
option to supply a path to FSL.

Example usage:

    python nifti_to_dscalar.py -v \
        --to_nifti         ${path}/cope1.feat/tstat1.dtseries.nii \
        --midthickness     101915/101915.{L,R}.midthickness.32k_fs_LR.surf.gii \
        --volume_ref       101915/T1w.nii.gz \
        --inner_surfaces   101915/101915.{L,R}.white.32k_fs_LR.surf.gii \
        --outer_surfaces   101915/101915.{L,R}.pial.32k_fs_LR.surf.gii \
        --apply_after_warp 0 101915/xfms/acpc_dc2standard.nii.gz reference.nii.gz desc-warped \
        --output_name      test_rc

## To Do

1. Add subcortical and cerebellar to surface-to-nifti conversion.
2. Add flags to point to `wb_command` and `FSL`. 

## More help

- [Volume to surface mapping][1]
- [CIFTI create dense scalar][2]
- [CIFTI separate][3]
- [CIFTI metric (surface) to volume mapping][4]
- [FSL applywarp][5]

[1]: https://humanconnectome.org/software/workbench-command/-volume-to-surface-mapping
[2]: https://humanconnectome.org/software/workbench-command/-cifti-create-dense-scalar
[3]: https://humanconnectome.org/software/workbench-command/-cifti-separate
[4]: https://humanconnectome.org/software/workbench-command/-metric-to-volume-mapping
[5]: https://web.mit.edu/fsl_v5.0.10/fsl/doc/wiki/FNIRT(2f)UserGuide.html
