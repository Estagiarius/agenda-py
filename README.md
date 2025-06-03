# agenda-pessoal
Uma agenda pessoal, construida para você.

## Features

### Personal Journal & Calendar
(Assuming any existing content for these features should be preserved above this new section)

### Intelligent Question Bank
The application now includes an Intelligent Question Bank feature. This allows users to:
*   **Create Questions**: Add new questions with text, subject, difficulty level, multiple-choice options (optional), and an answer.
*   **Store Questions**: Questions are stored within the application (currently in-browser memory).
*   **Categorize Questions**: Each question is categorized by subject and difficulty.
*   **Filter Questions**: Users can filter the displayed questions by subject and/or difficulty.

**How to Access the Question Bank:**
1.  Open `index.html` in your browser.
2.  Click on the "Question Bank" link in the navigation bar.

**Testing:**
Unit tests for the question management logic can be run by opening `tests/test-runner.html` in a browser.

#### Taking Quizzes
The application now allows you to test your knowledge by taking quizzes generated from the questions stored in the Question Bank.

**How to Take a Quiz:**
1.  Navigate to the "Take a Quiz" section using the link in the navigation bar.
2.  **Configure Your Quiz:**
    *   Specify the desired number of questions.
    *   Optionally, filter questions by a specific subject.
    *   Optionally, filter questions by difficulty level (Easy, Medium, Hard).
3.  Click "Start Quiz."
4.  **Answering Questions:**
    *   The quiz will present one question at a time.
    *   For multiple-choice questions, select your answer using the radio buttons.
    *   Navigate using "Next Question" and "Previous Question" buttons.
5.  **Submitting and Viewing Results:**
    *   Click "Submit Quiz" on the last question or when you're ready.
    *   Your score (total correct and percentage) will be displayed.
    *   A detailed review allows you to see each question, your answer, and the correct answer, highlighting correct/incorrect responses.
6.  From the results page, you can choose to "Take Another Quiz" (which resets the current quiz state and takes you to the configuration screen) or go "Back to Question Bank."

**Note:** Quizzes are currently generated from the questions available in the in-browser session. Adding questions to the Question Bank will make them available for future quizzes.
