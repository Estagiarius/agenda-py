import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QToolBar, QTextEdit, QAction, QActionGroup,
    QApplication, QStyle, QSizePolicy
)
from PyQt6.QtGui import (
    QFont, QTextCharFormat, QTextCursor, QTextListFormat, QIcon, QKeySequence
)
from PyQt6.QtCore import Qt, pyqtSignal


class RichTextEditorWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("RichTextEditorWidget")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0) # No external margins
        main_layout.setSpacing(0) # No spacing between toolbar and textedit

        self.toolbar = QToolBar()
        self.toolbar.setIconSize(Qt.GlobalColor.black.size()) # A reasonable default icon size
        main_layout.addWidget(self.toolbar)

        self.text_edit = QTextEdit()
        self.text_edit.setAcceptRichText(True)
        main_layout.addWidget(self.text_edit)

        self._setup_toolbar_actions()

        # Connect signals for updating toolbar state
        self.text_edit.currentCharFormatChanged.connect(self._update_format_actions_state)
        self.text_edit.cursorPositionChanged.connect(self._update_alignment_actions_state)

    def _get_icon(self, standard_pixmap):
        # This method is kept for direct use of standard pixmaps if a theme icon is not desired or available.
        # However, QIcon.fromTheme will use standardIcon as a fallback if the theme name isn't found,
        # so explicitly calling this might become less necessary.
        return self.style().standardIcon(standard_pixmap)

    def _setup_toolbar_actions(self):
        fallback_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton) # Neutral fallback

        # --- Text Style Actions ---
        self.action_bold = QAction("Bold", self)
        self.action_bold.setIcon(QIcon.fromTheme("format-text-bold", fallback_icon))
        self.action_bold.setShortcut(QKeySequence.StandardKey.Bold)
        self.action_bold.setCheckable(True)
        self.action_bold.triggered.connect(self._format_bold)
        self.toolbar.addAction(self.action_bold)

        self.action_italic = QAction("Italic", self)
        self.action_italic.setIcon(QIcon.fromTheme("format-text-italic", fallback_icon))
        self.action_italic.setShortcut(QKeySequence.StandardKey.Italic)
        self.action_italic.setCheckable(True)
        self.action_italic.triggered.connect(self._format_italic)
        self.toolbar.addAction(self.action_italic)

        self.action_underline = QAction("Underline", self)
        self.action_underline.setIcon(QIcon.fromTheme("format-text-underline", fallback_icon))
        self.action_underline.setShortcut(QKeySequence.StandardKey.Underline)
        self.action_underline.setCheckable(True)
        self.action_underline.triggered.connect(self._format_underline)
        self.toolbar.addAction(self.action_underline)

        self.toolbar.addSeparator()

        # --- Alignment Actions ---
        self.action_group_alignment = QActionGroup(self)
        self.action_group_alignment.setExclusive(True)

        self.action_align_left = QAction("Align Left", self)
        self.action_align_left.setIcon(QIcon.fromTheme("format-justify-left", fallback_icon))
        self.action_align_left.setCheckable(True)
        self.action_align_left.triggered.connect(lambda: self._format_align(Qt.AlignmentFlag.AlignLeft))
        self.toolbar.addAction(self.action_align_left)
        self.action_group_alignment.addAction(self.action_align_left)

        self.action_align_center = QAction("Align Center", self)
        self.action_align_center.setIcon(QIcon.fromTheme("format-justify-center", fallback_icon))
        self.action_align_center.setCheckable(True)
        self.action_align_center.triggered.connect(lambda: self._format_align(Qt.AlignmentFlag.AlignCenter))
        self.toolbar.addAction(self.action_align_center)
        self.action_group_alignment.addAction(self.action_align_center)

        self.action_align_right = QAction("Align Right", self)
        self.action_align_right.setIcon(QIcon.fromTheme("format-justify-right", fallback_icon))
        self.action_align_right.setCheckable(True)
        self.action_align_right.triggered.connect(lambda: self._format_align(Qt.AlignmentFlag.AlignRight))
        self.toolbar.addAction(self.action_align_right)
        self.action_group_alignment.addAction(self.action_align_right)

        self.action_align_justify = QAction("Align Justify", self)
        self.action_align_justify.setIcon(QIcon.fromTheme("format-justify-fill", fallback_icon))
        self.action_align_justify.setCheckable(True)
        self.action_align_justify.triggered.connect(lambda: self._format_align(Qt.AlignmentFlag.AlignJustify))
        self.toolbar.addAction(self.action_align_justify)
        self.action_group_alignment.addAction(self.action_align_justify)

        self.toolbar.addSeparator()

        # --- List Actions ---
        self.action_bullet_list = QAction("Bullet List", self)
        self.action_bullet_list.setIcon(QIcon.fromTheme("format-list-bulleted", fallback_icon))
        self.action_bullet_list.triggered.connect(lambda: self._format_list(QTextListFormat.Style.ListDisc))
        self.toolbar.addAction(self.action_bullet_list)

        self.action_numbered_list = QAction("Numbered List", self)
        self.action_numbered_list.setIcon(QIcon.fromTheme("format-list-numbered", fallback_icon))
        self.action_numbered_list.triggered.connect(lambda: self._format_list(QTextListFormat.Style.ListDecimal))
        self.toolbar.addAction(self.action_numbered_list)

        # Set initial state for alignment (usually left)
        self.action_align_left.setChecked(True)


    def _format_bold(self):
        self.text_edit.setFontWeight(QFont.Weight.Bold if self.action_bold.isChecked() else QFont.Weight.Normal)

    def _format_italic(self):
        self.text_edit.setFontItalic(self.action_italic.isChecked())

    def _format_underline(self):
        self.text_edit.setFontUnderline(self.action_underline.isChecked())

    def _format_align(self, alignment: Qt.AlignmentFlag):
        self.text_edit.setAlignment(alignment)
        # Ensure the correct action in the group is checked
        if alignment == Qt.AlignmentFlag.AlignLeft: self.action_align_left.setChecked(True)
        elif alignment == Qt.AlignmentFlag.AlignCenter: self.action_align_center.setChecked(True)
        elif alignment == Qt.AlignmentFlag.AlignRight: self.action_align_right.setChecked(True)
        elif alignment == Qt.AlignmentFlag.AlignJustify: self.action_align_justify.setChecked(True)


    def _format_list(self, style: QTextListFormat.Style):
        cursor = self.text_edit.textCursor()
        if not cursor.hasSelection():
            # If no selection, create a new list item or toggle current block's list type
            cursor.beginEditBlock()
            block_format = cursor.blockFormat()
            current_list = cursor.currentList()

            if current_list: # Already in a list
                if current_list.format().style() == style: # Same style, remove list
                    # This is more complex: need to iterate blocks and remove list format
                    # For simplicity now, we'll just re-apply, which might not remove it as expected
                    # A proper "remove list" would be a separate action or more logic here
                    cursor.createList(style) # Re-applying might just re-indent or do nothing
                else: # Different style, change it
                    current_list.setFormatStyle(style)
            else: # Not in a list, create one
                 cursor.createList(style)
            cursor.endEditBlock()
        else:
            # Selection exists, apply list to selected blocks
            cursor.createList(style)

        self.text_edit.setFocus()


    def _update_format_actions_state(self, fmt: QTextCharFormat):
        self.action_bold.setChecked(fmt.fontWeight() == QFont.Weight.Bold)
        self.action_italic.setChecked(fmt.fontItalic())
        self.action_underline.setChecked(fmt.fontUnderline())

    def _update_alignment_actions_state(self):
        alignment = self.text_edit.alignment()
        if alignment == Qt.AlignmentFlag.AlignLeft: self.action_align_left.setChecked(True)
        elif alignment == Qt.AlignmentFlag.AlignCenter: self.action_align_center.setChecked(True)
        elif alignment == Qt.AlignmentFlag.AlignRight: self.action_align_right.setChecked(True)
        elif alignment == Qt.AlignmentFlag.AlignJustify: self.action_align_justify.setChecked(True)
        else: # Default or mixed alignment in selection
            # Uncheck all or check left by default if no specific match
            # For exclusive group, one should remain checked; QActionGroup handles this if one is set.
             # If the alignment is mixed or not one of the specific ones, uncheck all.
            current_checked = self.action_group_alignment.checkedAction()
            if current_checked:
                 # Temporarily disable exclusive behavior to uncheck the action
                self.action_group_alignment.setExclusive(False)
                current_checked.setChecked(False)
                self.action_group_alignment.setExclusive(True)
            # Optionally, set a default (e.g., left) if nothing specific matches
            # self.action_align_left.setChecked(True)


    # --- Public Interface Methods ---
    def setHtml(self, html: str):
        self.text_edit.setHtml(html)

    def toHtml(self) -> str:
        return self.text_edit.toHtml()

    def setPlaceholderText(self, text: str):
        self.text_edit.setPlaceholderText(text)

    def setReadOnly(self, read_only: bool):
        self.text_edit.setReadOnly(read_only)
        self.toolbar.setVisible(not read_only) # Hide toolbar in read-only mode

if __name__ == '__main__':
    app = QApplication(sys.argv)
    editor = RichTextEditorWidget()
    editor.setPlaceholderText("Digite seu texto aqui...")
    editor.setWindowTitle("Editor de Texto Rico")
    editor.setMinimumSize(500, 300)
    editor.show()

    # Example of setting HTML content
    # editor.setHtml("<p>Este é um <b>texto</b> de <i>exemplo</i> com <u>sublinhado</u>.</p>"
    #                "<ul><li>Item 1</li><li>Item 2</li></ul>"
    #                "<ol><li>Item A</li><li>Item B</li></ol>")

    sys.exit(app.exec())
