import subprocess
import shutil
import tempfile
from pathlib import Path


# ============================================================
# SETTINGS
# ============================================================

CERTIFICATES_FOLDER = Path(r"C:\Users\gnimt\Downloads\certificates")

SIZE_LIMIT_MB = 2
SIZE_LIMIT_BYTES = SIZE_LIMIT_MB * 1024 * 1024

# Change this if your Ghostscript version/path is different
GS_COMMAND = r"C:\Program Files\gs\gs10.08.0\bin\gswin64c.exe"


# ============================================================
# CHECK GHOSTSCRIPT
# ============================================================

def check_ghostscript():

    if Path(GS_COMMAND).exists():

        print("Ghostscript found:")
        print(GS_COMMAND)
        print()

        return True

    print()
    print("=" * 70)
    print("ERROR: Ghostscript executable not found")
    print("=" * 70)
    print(GS_COMMAND)
    print()

    return False


# ============================================================
# COMPRESS PDF
# ============================================================

def compress_pdf(input_pdf, output_pdf):

    # Temporary folder used by Ghostscript
    temp_dir = Path(tempfile.gettempdir())

    temp_output = temp_dir / (
        f"{input_pdf.stem}_compressed_temp.pdf"
    )

    # Remove old temporary file
    if temp_output.exists():

        try:
            temp_output.unlink()

        except Exception:
            pass

    print(f"  Temporary file:")
    print(f"  {temp_output}")

    command = [
        GS_COMMAND,

        "-sDEVICE=pdfwrite",

        "-dCompatibilityLevel=1.4",

        # Compression quality
        "-dPDFSETTINGS=/ebook",

        "-dNOPAUSE",
        "-dBATCH",
        "-dQUIET",

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

        # Ghostscript failed
        if result.returncode != 0:

            print()
            print("  Ghostscript ERROR:")

            if result.stderr:
                print(result.stderr)

            return False

        # Check temporary output
        if not temp_output.exists():

            print("  ERROR: Ghostscript did not create the output file.")

            return False

        if temp_output.stat().st_size == 0:

            print("  ERROR: Ghostscript created an empty file.")

            return False

        # Remove existing compressed file
        if output_pdf.exists():

            try:

                output_pdf.unlink()

            except PermissionError:

                print()
                print(
                    f"  ERROR: Cannot replace {output_pdf.name}"
                )

                print(
                    "  Make sure the compressed PDF is not open."
                )

                return False

        # Copy temporary PDF to certificates folder
        try:

            shutil.copy2(
                temp_output,
                output_pdf
            )

        except PermissionError:

            print()
            print("  ERROR: Windows denied writing the output file.")
            print(f"  Destination: {output_pdf}")

            return False

        # Remove temporary file
        try:
            temp_output.unlink()
        except Exception:
            pass

        return True

    except Exception as e:

        print()
        print(f"  ERROR: {e}")

        return False


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 70)
    print("PDF CERTIFICATE COMPRESSION")
    print("=" * 70)
    print()

    # Check Ghostscript
    if not check_ghostscript():
        return

    # Check folder
    if not CERTIFICATES_FOLDER.exists():

        print("ERROR: Certificates folder does not exist:")
        print(CERTIFICATES_FOLDER)

        return

    print("Input/output folder:")
    print(CERTIFICATES_FOLDER)
    print()

    # Find PDFs
    pdf_files = list(
        CERTIFICATES_FOLDER.glob("*.pdf")
    )

    if not pdf_files:

        print("No PDF files found.")

        return

    print(f"Found {len(pdf_files)} PDF files.")
    print("-" * 70)

    compressed_count = 0
    skipped_count = 0
    failed_count = 0

    for pdf in pdf_files:

        # Don't process already compressed PDFs
        if pdf.stem.endswith("_compressed"):
            continue

        original_size = pdf.stat().st_size

        original_size_mb = (
            original_size / (1024 * 1024)
        )

        # Skip files <= 2 MB
        if original_size <= SIZE_LIMIT_BYTES:

            print(
                f"SKIPPED  | {pdf.name} | "
                f"{original_size_mb:.2f} MB"
            )

            skipped_count += 1

            continue

        # Output filename
        output_pdf = (
            CERTIFICATES_FOLDER /
            f"{pdf.stem}_compressed.pdf"
        )

        print()
        print(
            f"COMPRESS | {pdf.name} | "
            f"{original_size_mb:.2f} MB"
        )

        print(
            f"  Output will be:"
        )

        print(
            f"  {output_pdf}"
        )

        # Compress
        success = compress_pdf(
            pdf,
            output_pdf
        )

        if not success:

            print("  FAILED")

            failed_count += 1

            continue

        # Get compressed size
        compressed_size = output_pdf.stat().st_size

        compressed_size_mb = (
            compressed_size / (1024 * 1024)
        )

        reduction = (
            (1 - compressed_size / original_size)
            * 100
        )

        # Check whether compression actually reduced size
        if compressed_size < original_size:

            print(
                f"  SUCCESS | "
                f"{compressed_size_mb:.2f} MB | "
                f"Reduced by {reduction:.1f}%"
            )

            compressed_count += 1

        else:

            print(
                "  NO REDUCTION | "
                "Compressed file is not smaller."
            )

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

    print(f"Compressed : {compressed_count}")
    print(f"Skipped    : {skipped_count}")
    print(f"Failed     : {failed_count}")

    print()
    print("Compressed files are located in:")
    print(CERTIFICATES_FOLDER)

    print("=" * 70)


if __name__ == "__main__":
    main()
