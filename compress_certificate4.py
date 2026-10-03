import subprocess
import shutil
import tempfile
from pathlib import Path


# ============================================================
# SETTINGS
# ============================================================

CERTIFICATES_FOLDER = Path(
    r"C:\Users\gnimt\Downloads\certificates"
)

# FINAL compressed PDF must be BELOW this size
TARGET_SIZE_MB = 2
TARGET_SIZE_BYTES = TARGET_SIZE_MB * 1024 * 1024

# Ghostscript
GS_COMMAND = r"C:\Program Files\gs\gs10.08.0\bin\gswin64c.exe"


# ============================================================
# COMPRESSION SETTINGS
# ============================================================

# We try these progressively.
#
# /ebook  = better quality
# /screen = stronger compression
#
# After that, custom image resolution is used.

COMPRESSION_LEVELS = [

    {
        "name": "ebook",
        "settings": [
            "-dPDFSETTINGS=/ebook"
        ]
    },

    {
        "name": "screen",
        "settings": [
            "-dPDFSETTINGS=/screen"
        ]
    },

    {
        "name": "custom_120dpi",
        "settings": [
            "-dDownsampleColorImages=true",
            "-dColorImageResolution=120",
            "-dColorImageDownsampleType=/Bicubic",

            "-dDownsampleGrayImages=true",
            "-dGrayImageResolution=120",
            "-dGrayImageDownsampleType=/Bicubic",

            "-dDownsampleMonoImages=true",
            "-dMonoImageResolution=150",
            "-dMonoImageDownsampleType=/Subsample"
        ]
    },

    {
        "name": "custom_96dpi",
        "settings": [
            "-dDownsampleColorImages=true",
            "-dColorImageResolution=96",
            "-dColorImageDownsampleType=/Bicubic",

            "-dDownsampleGrayImages=true",
            "-dGrayImageResolution=96",
            "-dGrayImageDownsampleType=/Bicubic",

            "-dDownsampleMonoImages=true",
            "-dMonoImageResolution=120",
            "-dMonoImageDownsampleType=/Subsample"
        ]
    }
]


# ============================================================
# COMPRESS PDF
# ============================================================

def compress_pdf(input_pdf):

    original_size = input_pdf.stat().st_size

    temp_dir = Path(tempfile.gettempdir())

    # Try each compression level
    for level in COMPRESSION_LEVELS:

        level_name = level["name"]

        print(
            f"  Trying compression: {level_name}"
        )

        temp_output = temp_dir / (
            f"{input_pdf.stem}_"
            f"{level_name}_temp.pdf"
        )

        # Remove previous temporary file
        if temp_output.exists():

            try:
                temp_output.unlink()
            except Exception:
                pass

        command = [
            GS_COMMAND,

            "-sDEVICE=pdfwrite",

            "-dCompatibilityLevel=1.4",

            "-dNOPAUSE",
            "-dBATCH",
            "-dQUIET",

            "-dAutoRotatePages=/None",

            *level["settings"],

            f"-sOutputFile={temp_output}",

            str(input_pdf)
        ]

        try:

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False
            )

        except Exception as e:

            print(
                f"  ERROR running Ghostscript: {e}"
            )

            continue

        # Ghostscript error
        if result.returncode != 0:

            print(
                f"  Ghostscript failed at {level_name}"
            )

            if result.stderr:
                print(result.stderr)

            continue

        # Check output
        if not temp_output.exists():

            print(
                "  Ghostscript did not create output."
            )

            continue

        compressed_size = temp_output.stat().st_size

        compressed_size_mb = (
            compressed_size / (1024 * 1024)
        )

        print(
            f"  Result: {compressed_size_mb:.2f} MB"
        )

        # TARGET ACHIEVED
        if compressed_size < TARGET_SIZE_BYTES:

            print(
                f"  TARGET ACHIEVED: "
                f"{compressed_size_mb:.2f} MB"
            )

            return temp_output

        # Not small enough
        print(
            f"  Still above {TARGET_SIZE_MB} MB"
        )

        # Remove temporary file before next attempt
        try:
            temp_output.unlink()
        except Exception:
            pass

    return None


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 70)
    print("PDF CERTIFICATE COMPRESSION")
    print("=" * 70)
    print()

    # --------------------------------------------------------
    # Check Ghostscript
    # --------------------------------------------------------

    if not Path(GS_COMMAND).exists():

        print("ERROR: Ghostscript not found:")
        print(GS_COMMAND)
        print()

        return

    print("Ghostscript:")
    print(GS_COMMAND)

    print()

    # --------------------------------------------------------
    # Check certificate folder
    # --------------------------------------------------------

    if not CERTIFICATES_FOLDER.exists():

        print(
            "ERROR: Certificates folder does not exist:"
        )

        print(CERTIFICATES_FOLDER)

        return

    print("Certificate folder:")
    print(CERTIFICATES_FOLDER)

    print()

    # --------------------------------------------------------
    # Find PDFs
    # --------------------------------------------------------

    pdf_files = list(
        CERTIFICATES_FOLDER.glob("*.pdf")
    )

    if not pdf_files:

        print("No PDF files found.")

        return

    print(
        f"Found {len(pdf_files)} PDF files."
    )

    print("-" * 70)

    compressed_count = 0
    skipped_count = 0
    failed_count = 0

    # --------------------------------------------------------
    # Process PDFs
    # --------------------------------------------------------

    for pdf in pdf_files:

        # Don't process compressed PDFs
        if pdf.stem.endswith("_compressed"):

            continue

        original_size = pdf.stat().st_size

        original_size_mb = (
            original_size / (1024 * 1024)
        )

        # ----------------------------------------------------
        # Skip files already below 2 MB
        # ----------------------------------------------------

        if original_size < TARGET_SIZE_BYTES:

            print(
                f"SKIPPED  | {pdf.name} | "
                f"{original_size_mb:.2f} MB"
            )

            skipped_count += 1

            continue

        print()

        print(
            f"COMPRESS | {pdf.name} | "
            f"{original_size_mb:.2f} MB"
        )

        # ----------------------------------------------------
        # Compress
        # ----------------------------------------------------

        temp_result = compress_pdf(pdf)

        if temp_result is None:

            print()
            print(
                "  FAILED: Could not reduce below "
                f"{TARGET_SIZE_MB} MB."
            )

            failed_count += 1

            continue

        # ----------------------------------------------------
        # Final destination
        # ----------------------------------------------------

        output_pdf = (
            CERTIFICATES_FOLDER /
            f"{pdf.stem}_compressed.pdf"
        )

        # Remove existing output
        if output_pdf.exists():

            try:

                output_pdf.unlink()

            except PermissionError:

                print(
                    "  ERROR: Existing compressed file "
                    "is open or protected."
                )

                try:
                    temp_result.unlink()
                except Exception:
                    pass

                failed_count += 1

                continue

        # ----------------------------------------------------
        # Copy to certificates folder
        # ----------------------------------------------------

        try:

            shutil.copy2(
                temp_result,
                output_pdf
            )

        except Exception as e:

            print(
                f"  ERROR copying final file: {e}"
            )

            try:
                temp_result.unlink()
            except Exception:
                pass

            failed_count += 1

            continue

        # ----------------------------------------------------
        # Remove temporary file
        # ----------------------------------------------------

        try:
            temp_result.unlink()
        except Exception:
            pass

        # ----------------------------------------------------
        # Verify final file
        # ----------------------------------------------------

        final_size = output_pdf.stat().st_size

        final_size_mb = (
            final_size / (1024 * 1024)
        )

        reduction = (
            (1 - final_size / original_size)
            * 100
        )

        # ----------------------------------------------------
        # Final verification
        # ----------------------------------------------------

        if final_size < TARGET_SIZE_BYTES:

            print(
                f"  SUCCESS | "
                f"{final_size_mb:.2f} MB | "
                f"Reduced by {reduction:.1f}%"
            )

            compressed_count += 1

        else:

            print(
                f"  ERROR: Final file is still "
                f"{final_size_mb:.2f} MB"
            )

            # Remove file that doesn't meet target
            try:
                output_pdf.unlink()
            except Exception:
                pass

            failed_count += 1

    # ========================================================
    # SUMMARY
    # ========================================================

    print()
    print("=" * 70)
    print("COMPRESSION COMPLETE")
    print("=" * 70)

    print(
        f"Compressed : {compressed_count}"
    )

    print(
        f"Skipped    : {skipped_count}"
    )

    print(
        f"Failed     : {failed_count}"
    )

    print()

    print(
        "Compressed files are located in:"
    )

    print(CERTIFICATES_FOLDER)

    print("=" * 70)


if __name__ == "__main__":
    main()
