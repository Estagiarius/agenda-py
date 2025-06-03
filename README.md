# TeacherAgenda

TeacherAgenda is a personal organization tool for teachers, built with Python and PyQt6. It helps teachers manage their schedules, tasks, and student information efficiently.

## Features

*   **Personal Journal & Calendar**: Keep track of daily notes, appointments, and important dates.
*   **Intelligent Question Bank**: Create, store, categorize, and filter questions for various subjects and difficulty levels.
*   **Taking Quizzes**: Generate quizzes from the question bank to test knowledge.

## Setting up the Development Environment

### Prerequisites

*   Python 3.10 or higher.

### Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/your-username/TeacherAgenda.git
    cd TeacherAgenda
    ```
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Running the Application from Source

To run the application directly from the source code (ensure you are in the project root directory):

```bash
python3 -m src.main
```
This method is recommended because it tells Python to treat the `src` directory as a package. This helps avoid `ModuleNotFoundError` that can occur with direct script execution (`python src/main.py`) when the application uses relative imports within the `src` package (e.g., `from src.ui.main_window import MainWindow`).

## Building the Application for Linux

A script is provided to build a standalone executable for Linux.

1.  Make the build script executable:
    ```bash
    chmod +x build_linux.sh
    ```
2.  Run the build script:
    ```bash
    ./build_linux.sh
    ```
    This will create a standalone executable file in the `dist/` directory.

## Running the Packaged Application

After building the application, navigate to the output directory and run the executable:

```bash
cd dist/TeacherAgenda
./TeacherAgenda
```
