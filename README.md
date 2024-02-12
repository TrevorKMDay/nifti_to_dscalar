# nifti_to_dscalar

This script uses the convention that, when paired, the order is always left,
right. For all methods, use `enclosing` for label values.

## Usage

At the most basic, all you need is two surfaces (left/right `.surf.gii`) and a
NIFTI (`.nii.gz`):

    python nifti_to_dscalar.py left.surf.gii right.surf.gii nifti.nii.gz

The NIFTI option is repeatable (to use the same surfaces for each one).

## Ribbon-enclosed

To use the `-ribbon-enclosed` mapping, simply supply the inner (WM) and outer
(pial) surface files. Two each: left, right. The default ribbon mapping is
weighted averaging, use `--rc_method` to change that.

## Full usage:

    usage: nifti_to_dscalar [-h] [--output_name OUTPUT_NAME [OUTPUT_NAME ...]]
                            [--method {trilinear,cubic,enclosing}]
                            [--rc_method {weighted_avg,trilinear,cubic,enclosing}]
                            [--inner_surfaces SURF SURF]
                            [--outer_surfaces SURF SURF] [--verbose]
                            l_surface r_surface nifti [nifti ...]

    Easily project .nii.gz files into surface space.
    Hemisphere order is always L->R.

    positional arguments:
    l_surface             Left surface to map onto.
    r_surface             Right surface to map onto.
    nifti                 Input NIFTI file(s)

    optional arguments:
    -h, --help            show this help message and exit
    --output_name OUTPUT_NAME [OUTPUT_NAME ...], -o OUTPUT_NAME [OUTPUT_NAME ...]
                            Output name (without .dscalar.nii).
                            Must be same length as nifti input, if provided.
    --method {trilinear,cubic,enclosing}, -m {trilinear,cubic,enclosing}
                            Method to use.
                            Use 'enclosing' for labels.
                            Conflicts with ribbon-constrained, use --rc_method
                            .Default: 'trilinear'.
    --rc_method {weighted_avg,trilinear,cubic,enclosing}
                            Method to use for ribbon-constrained mapping.
                            Default: 'weighted_avg'.
    --inner_surfaces SURF SURF, -wm SURF SURF
                            WM surfaces to use ribbon enclosed projection. L/R.
                            Must be used with --outer_surfaces.
    --outer_surfaces SURF SURF, -pial SURF SURF
                            Pial surfaces to use ribbon enclosed projection. L/R.
                            Must be used with --inner_surfaces
    --verbose, -v         Does what a --verbose flag usually does.

## More help

 - [Volume to surface mapping][1]
 - [CIFTI create dense scalar][2]


[1]: https://humanconnectome.org/software/workbench-command/-volume-to-surface-mapping
[2]: https://humanconnectome.org/software/workbench-command/-cifti-create-dense-scalar