## Dependency: Poppler for PDF Preview

The report preview feature uses the `pdf2image` library, which requires Poppler to be installed on your system.

**Installation Instructions:**

*   **Windows:**
    1.  Download the latest Poppler binary for Windows from [the official Poppler for Windows builds by OSGeo](http://blog.alivate.com.au/poppler-windows/) or another trusted source.
    2.  Extract the archive (e.g., to `C:\Program Files\poppler-version`).
    3.  Add the `bin` directory (e.g., `C:\Program Files\poppler-version\bin`) to your system's PATH environment variable.
*   **macOS (using Homebrew):**
    ```bash
    brew install poppler
    ```
*   **Linux (using apt - for Debian/Ubuntu):**
    ```bash
    sudo apt-get update
    sudo apt-get install poppler-utils
    ```
*   **Linux (using yum - for Fedora/CentOS):**
    ```bash
    sudo yum install poppler-utils
    ```

Please ensure Poppler is installed and accessible in your system's PATH for the PDF preview to work correctly.
