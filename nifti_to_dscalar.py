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

parser.add_argument("l_surface",
                    help="Left surface to map onto.")

parser.add_argument("r_surface",
                    help="Right surface to map onto.")

parser.add_argument("nifti", nargs="+",
                    help="Input NIFTI file(s)")

parser.add_argument("--overwrite", action="store_true",
                    help="If set, will overwrite output files.")

parser.add_argument("--output_name", "-o", nargs="+",
                    help="Output name (without .dscalar.nii).\nMust be same "
                         "length as nifti input, if provided.")

parser.add_argument("--method", "-m",
                    help="Method to use.\nUse 'enclosing' for labels.\n"
                         "Conflicts with ribbon-constrained, use "
                         "--rc_method\n."
                         "Default: 'trilinear'.",
                    choices=["trilinear", "cubic", "enclosing"],
                    default="default")

parser.add_argument("--rc_method",
                    help="Method to use for ribbon-constrained mapping.\n"
                         "Default: 'weighted_avg'.",
                    choices=["weighted_avg", "trilinear", "cubic",
                             "enclosing"],
                    default="weighted_avg")

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

args = parser.parse_args()

if bool(args.inner_surfaces is not None) ^ \
   bool(args.outer_surfaces is not None):

    print("ERROR: If one of inner/outer surfaces is provided, both must be!")
    exit(1)

# IMPORTANT NOTE:   This script uses the convention to pair L/R files in
#   two-item lists, where [0] is L, and [1] is R.

# DEFINE FUNCTIONS


def project(nifti, surfaces, output_name, surf_pial, surf_wm,
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
                    nifti, surfaces[i], temp_surfaces[i].name, f"-{method}"],
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
        for i in [0, 1]:

            cmd = ["wb_command", "-volume-to-surface-mapping",
                   nifti, surfaces[i], temp_surfaces[i].name,
                   "-ribbon-constrained", surf_wm[i], surf_pial[i]]

            # If interpolation method was changed, add that flag to the command
            #   otherwise, don't (adding an empty string upsets sp.run)
            if flag is not None:
                cmd = cmd.append(flag)

            if verbose:
                h = ["L", "R"][i]
                print(f"INFO:  Working on {h} hemisphere")

            # Actually run the command
            sp.run(cmd, check=True)

    sp.run(["wb_command", "-cifti-create-dense-scalar",
            output_name,
            "-left-metric", temp_surfaces[0].name,
            "-right-metric", temp_surfaces[1].name])


# MAIN LOOP

if args.verbose:
    print(f"INFO:  {dt.datetime.now()}")

# Check that # files and # of new names aligns
if args.output_name is not None:

    if len(args.nifti) == len(args.output_name):
        output_names = args.output_name
    else:
        print("ERROR: Length of nifti/name inputs does not match!")
        exit(1)

else:
    # Create list of Nones for loop - i.e. provide no new names
    output_names = [None] * len(args.nifti)


for file, oname in zip(args.nifti, output_names):

    if not os.path.isfile(file):

        print(f"ERROR: File {file} is not a regular file, not doing anything.")
        continue

    print(f"INFO:  Working on {file} ...")

    # Set output name to provided value, otherwise just replace '.nii.gz'
    #   extension with '.dscalar.nii'
    output_name = f"{oname}.dscalar.nii" if oname is not None else \
        re.sub("nii.gz$", "dscalar.nii", file)
    
    if os.path.exists(output_name) and not args.overwrite:
       
       print(f"ERROR: Requested output file {output_name} already exists, "
              "not doing anything.")
        
    else:

        project(file, 
                [args.l_surface, args.r_surface], 
                output_name,
                args.outer_surfaces, args.inner_surfaces,
                method=args.method, rc_method=args.rc_method,
                verbose=args.verbose)

if args.verbose:
    print(f"INFO:  {dt.datetime.now()}")
