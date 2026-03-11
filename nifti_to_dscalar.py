import argparse as ap
import subprocess as sp
import re
import os
import tempfile as tf
import datetime as dt

parser = ap.ArgumentParser(prog="nifti_to_dscalar",
                           description="Easily project .nii.gz files into "
                                       "surface space.\n"
                                       "Hemisphere order is always L->R.",
                           formatter_class=ap.RawTextHelpFormatter)

# Which direction are we going?

conversion = parser.add_mutually_exclusive_group(required=True)

conversion.add_argument("--to_dscalar", nargs="+",
                        help="A list of NIFTI files to convert to surface.",
                        metavar="NIFTI")

conversion.add_argument("--to_nifti", nargs="+",
                        help="A list of surface files to convert to NIFTI.",
                        metavar="DSCALAR")

# Shared options

parser.add_argument("--overwrite", action="store_true",
                    help="If set, will overwrite output files.")

parser.add_argument("--output_name", "-o", nargs="+",
                    help="Output name (without suffix).\nMust be same "
                         "length as input.")

parser.add_argument("--midthickness", "-M", nargs=2,
                    help="Left and right midthickness files\nRequired for "
                         "both directions.",
                    required=True, metavar="SURF")

parser.add_argument("--inner_surfaces", "-wm", nargs=2,
                    help="WM surfaces to use ribbon enclosed projection. "
                         "L/R.\nMust be used with --outer_surfaces.",
                    default=[None, None],
                    metavar="SURF")

parser.add_argument("--outer_surfaces", "-pial", nargs=2,
                    help="Pial surfaces to use ribbon enclosed projection. "
                         "L/R.\nMust be used with --inner_surfaces",
                    default=[None, None],
                    metavar="SURF")

parser.add_argument("--verbose", "-v", action="store_true",
                    help="Does what a --verbose flag usually does.")

# Method-specific options

group_n2s = parser.add_argument_group("NIFTI to surface")

group_n2s.add_argument("--method", "-m",
                        help="Method to use.\nUse 'enclosing' for labels.\n"
                            "Conflicts with ribbon-constrained, use "
                            "--rc_method\n."
                            "Default: 'trilinear'.",
                        choices=["trilinear", "cubic", "enclosing"],
                        default="default")

group_n2s.add_argument("--rc_method",
                        help="Method to use for ribbon-constrained mapping.\n"
                            "Default: 'weighted_avg'.",
                        choices=["weighted_avg", "trilinear", "cubic",
                                "enclosing"],
                        default="weighted_avg")

group_s2n = parser.add_argument_group("Surface to NIFTI")

group_s2n.add_argument("--volume_ref", "-vol",
                       help="When projecting metric to volume, reference volume",
                       metavar="NIFTI")

group_s2n.add_argument("--nearest_vertex", nargs=1, default=2,
                       help="How far from the surface to map values to voxels,"
                            "in mm. Default: 2 mm.\n"
                            "This is overridden by using --*_surfaces")

group_s2n.add_argument("--apply_after_warp", nargs='+', metavar="NIFTI",
                       help="After doing the surface-to-volume conversion,"
                            "apply a warp (using FSL applywarp).\n"
                            "Three arguments:\n"
                            "  0/1: If 1, keep unwarped file\n"
                            "  [file]: Warp file to apply\n"
                            "  [name]: suffix to add, default: _desc-warped")

args = parser.parse_args()

# Give the midthickness files a better name
midsurfaces = args.midthickness
s2n_use_rc = False

if bool(args.inner_surfaces != [None, None]) ^ \
    bool(args.outer_surfaces != [None, None]):

    print("ERROR: If one of inner/outer surfaces is provided, both must be!")
    exit(1)

if args.inner_surfaces != [None, None] and args.outer_surfaces != [None, None]:

    print("INFO: Using ribbon-constrained method for surf-to-nifti.")
    print("INFO: This method takes longer than nearest-vertex (about 1 min).")

    # TO DO: Add method to modify -voxel-subdiv flag, although idk what it
    # does anyway. No plan to add legacy 'greedy' and 'thick columns' methods.

    # If the inner and outer surfaces are set, use the ribbon-constrained
    # surface-to-nifti option
    s2n_use_rc = True
    near_vtx_dist = None

else:

    near_vtx_dist = args.nearest_vertex[0]
    print("INFO: Using nearest-vertex method for surf-to-nifti, "
          f"distance: {near_vtx_dist}")

# IMPORTANT NOTE:   This script uses the convention to pair L/R files in
#   two-item lists, where [0] is L, and [1] is R.

if args.apply_after_warp is not None:

    # Check whether to keep file
    if args.apply_after_warp[0] == '1':
        keep_unwarped = True
    elif args.apply_after_warp[0] == '0':
        keep_unwarped = False
    else:
        print(f"Invalid option \'{args.apply_after_warp[0]}\' to "
              "--apply_after_warp, first option must be "
              "0 or 1.")

    # There's probably a neater way to do this
    if len(args.apply_after_warp) == 2:
        warp_file = args.apply_after_warp[1]
        warp_suffix = "_desc-warped"
    elif len(args.apply_after_warp) == 3:
        warp_file = args.apply_after_warp[1]
        warp_suffix = args.apply_after_warp[2]
    else:
        print("Must supply 2 or 3 arguments to --apply_after_warp, supplied"
              f"{len(args.apply_after_warp)}")


# DEFINE FUNCTIONS


def project_n2s(nifti, midsurfaces, output_name, surf_pial, surf_wm,
                method=None, rc_method=None, verbose=False):

    temp_surfaces = [tf.NamedTemporaryFile(suffix=".func.gii"),
                     tf.NamedTemporaryFile(suffix=".func.gii")]

    if verbose:
        print(f"INFO:  Temporary surfaces: {[t.name for t in temp_surfaces]}")

    if surf_pial == [None, None] and surf_wm == [None, None]:

        # IF NO INNER/OUTER SURFACE WAS PROVIDED, USE REGULAR MAPPING

        print(f"INFO:  Using method {method}")

        # The default value for method is "default" to skip the warning when
        #   using ribbon-constrained. Replace that with 'trilinear'.
        method = "trilinear" if method == "default" else method

        if args.rc_method is not None:
            print("WARNING: Ribbon-constrained method was set to "
                  f"'{rc_method}', being ignored. Use --method")

        # Do mapping for L/R
        for i in [0, 1]:

            sp.run(["wb_command", "-volume-to-surface-mapping",
                    nifti, midsurfaces[i], temp_surfaces[i].name, f"-{method}"],
                   check=True)

    else:

        # IF INNER/OUTER SURFACES WERE PROVIDED, USE RIBBON-CONSTRAINED

        print("INFO:  Using ribbon constrained mapping (takes longer)")
        print(f"INFO:  Using method '{rc_method}'")

        if method is not None and method != "default":
            print(f"WARNING: Method was set to '{method}', being ignored. Use "
                  "--rc_method")

        # No flag if using default method, otherwise use '-interpolate METHOD'
        flag = None if rc_method == "weighted_avg" else \
            f"-interpolate {rc_method}"

        # Do mapping for L/R
        for i, LR in zip([0, 1], ["L", "R"]):

            cmd = ["wb_command", "-volume-to-surface-mapping",
                   nifti, midsurfaces[i], temp_surfaces[i].name,
                   "-ribbon-constrained", surf_wm[i], surf_pial[i]]

            # If interpolation method was changed, add that flag to the command
            #   otherwise, don't (adding an empty string upsets sp.run)
            if flag is not None:
                cmd = cmd.append(flag)

            if verbose:
                print(f"INFO:  Working on {LR} hemisphere")

            # Actually run the command
            sp.run(cmd, check=True)

    sp.run(["wb_command", "-cifti-create-dense-scalar",
            output_name,
            "-left-metric", temp_surfaces[0].name,
            "-right-metric", temp_surfaces[1].name])

def project_s2n(metric, midsurfaces, volume_template, output_name,
                near_vtx_dist=None,
                inner_surfaces=None, outer_surfaces=None, verbose=False):

    # Extract the surfaces from the CIFTI file into two new files
    temp_surfaces = [tf.NamedTemporaryFile(suffix=".func.gii"),
                     tf.NamedTemporaryFile(suffix=".func.gii")]

    sep_command = ["wb_command", "-cifti-separate",
                   metric, "COLUMN",
                   "-metric", "CORTEX_LEFT", temp_surfaces[0].name,
                   "-metric", "CORTEX_RIGHT", temp_surfaces[1].name]

    if verbose:
        print(" ".join(sep_command))

    sp.run(sep_command)

    # For each L/R extracted cortex, convert it to a nifti

    temp_niftis = [tf.NamedTemporaryFile(suffix=".nii.gz"),
                     tf.NamedTemporaryFile(suffix=".nii.gz")]

    for i, LR in zip([0, 1], ["L", "R"]):

        if verbose:
            print(f"INFO:  Working on {LR} hemisphere")

        m2v_cmd = ["wb_command", "-metric-to-volume-mapping",
               temp_surfaces[i].name, midsurfaces[i], volume_template,
               temp_niftis[i].name]

        if near_vtx_dist is not None:

            # Using nearest vertex method
            m2v_cmd = m2v_cmd + ["-nearest-vertex", str(near_vtx_dist)]

        else:

            # Append the L/R inner/outer surfaces accordingly
            m2v_cmd = m2v_cmd + \
                ["-ribbon-constrained", inner_surfaces[i], outer_surfaces[i]]

        if verbose:
            print(m2v_cmd)

        sp.run(m2v_cmd)


    # Add the L/R niftis back into one.
    # TO DO: This is probably possible with wb_command to reduce dependencies
    sp.run(["fslmaths", temp_niftis[0].name,
            "-add", temp_niftis[1].name,
            output_name])


def apply_warp(in_file, warp_file, out_file, keep=False):

    # applywarp \
    #     -i "${i}" \
    #     -r 101915/xfms/acpc_dc2standard.nii.gz \
    #     -w 101915/xfms/acpc_dc2standard.nii.gz \
    #     -o "${i//.nii.gz/_warped.nii.gz}" \
    #     --interp=nn

    # TO DO: add more interpolation options
    cmd = ["applywarp", "-i", in_file, "-r", warp_file, "-o", out_file,
           "-w", warp_file, "--interp=nn"]

    sp.run(cmd)

    if not keep:
        print(f"Removing file {in_file} as requested")
        os.remove(in_file)


# MAIN LOOP

if args.to_dscalar is not None:

    method = "to_dscalar"
    source_files = args.to_dscalar

elif args.to_nifti is not None:

    method = "to_nifti"
    source_files = args.to_nifti

    if args.volume_ref is None:
        print("ERROR: A volume reference (--volume_ref) must be supplied if "
              "using the surface-to-nifti method.")
        exit(1)

if args.verbose:
    print(f"INFO:  {dt.datetime.now()}")

# Check that # files and # of new names aligns
if args.output_name is not None:

    if len(source_files) == len(args.output_name):
        output_names = args.output_name
    else:
        print("ERROR: Length of nifti/name inputs does not match!")
        exit(1)

else:
    # Create list of Nones for loop - i.e. provide no new names
    output_names = [None] * len(source_files)


for file, oname in zip(source_files, output_names):

    if not os.path.isfile(file):

        print(f"ERROR: File {file} is not a regular file, not doing anything.")
        continue

    print(f"INFO:  Working on {file} ...")

    if method == "to_dscalar":

        print(f"INFO: Doing NIFTI to surface")

        # Set output name to provided value, otherwise just replace '.nii.gz'
        #   extension with '.dscalar.nii'
        output_name = f"{oname}.dscalar.nii" if oname is not None else \
            re.sub("nii.gz$", "dscalar.nii", file)

        if os.path.exists(output_name) and not args.overwrite:

            print(f"ERROR: Requested output file {output_name} already "
                    "exists, not doing anything.")

        else:

            project_n2s(file, midsurfaces, output_name,
                        args.outer_surfaces, args.inner_surfaces,
                        method=args.method, rc_method=args.rc_method,
                        verbose=args.verbose)

    elif method == "to_nifti":

        print("INFO: Doing surface to dscalar")

        if near_vtx_dist is not None:
            print("INFO: Using nearest-vertex mapping, distance:"
                  f"{near_vtx_dist} mm.")

        # Set output name to provided value, otherwise just replace '.nii.gz'
        #   extension with '.dscalar.nii'
        output_name = f"{oname}.nii.gz" if oname is not None else \
            re.sub(".[a-z]*.nii$", ".nii.gz", file)

        if os.path.exists(output_name) and not args.overwrite:

            print(f"ERROR: Requested output file {output_name} already "
                    "exists, not doing anything.")

        else:

            project_s2n(file, midsurfaces,
                        near_vtx_dist=near_vtx_dist,
                        inner_surfaces=args.inner_surfaces,
                        outer_surfaces=args.outer_surfaces,
                        volume_template=args.volume_ref,
                        output_name=output_name,
                        verbose=args.verbose)

        if args.apply_after_warp is not None:


            output_name2 = f"{oname}{warp_suffix}.nii.gz"

            if os.path.exists(output_name2) and not args.overwrite:

                print(f"ERROR: Requested warped file {output_name2} already "
                        "exists, not doing anything.")

            else:

                print(f"Applying warp {warp_file}")
                apply_warp(output_name, warp_file, output_name2, keep_unwarped)

if args.verbose:
    print(f"INFO:  {dt.datetime.now()}")
