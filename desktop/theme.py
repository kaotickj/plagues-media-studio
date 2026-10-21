"""Visual system for Plague's Media Studio desktop."""

STYLE = """
QMainWindow, QDialog, QWidget#Workspace {
    background: #0A121D;
    color: #ECF4F7;
}
QWidget { color: #ECF4F7; font-family: 'Segoe UI', 'Noto Sans', sans-serif; font-size: 13px; }
QLabel#Eyebrow { color: #59E2CB; font-weight: 700; font-size: 11px; letter-spacing: 1px; }
QLabel#BrandTitle { color: #FFFFFF; font-size: 25px; font-weight: 750; }
QLabel#BrandSubtitle { color: #AAC0CE; font-size: 12px; }
QLabel#SectionTitle { color: #F6FAFC; font-size: 17px; font-weight: 700; }
QLabel#CardLabel { color: #A7BDCA; font-size: 12px; font-weight: 650; }
QLabel#Muted, QLabel#HelpText { color: #A9BDCA; }
QLabel#StatusText { color: #C9D8E1; font-size: 12px; }
QLabel#FormatHint { color: #8CA6B7; font-size: 12px; }
QFrame#Panel { background: #132130; border: 1px solid #314657; border-radius: 16px; }
QFrame#InnerCard { background: #182B3B; border: 1px solid #355266; border-radius: 12px; }
QFrame#DropZone { background: #102637; border: 2px dashed #3B7E87; border-radius: 13px; }
QFrame#DropZone[dragging="true"] { background: #184253; border-color: #60ECD2; }
QFrame#HeaderLine { background: #243947; max-height: 1px; min-height: 1px; }
QFrame#StatusPill { background: #193F3E; border: 1px solid #2F8881; border-radius: 12px; }
QFrame#MissingPill { background: #453123; border: 1px solid #B77849; border-radius: 12px; }
QPushButton { background: #213648; color: #F0F8FC; border: 1px solid #466278; border-radius: 9px;
    padding: 10px 15px; min-height: 22px; font-weight: 650; }
QPushButton:hover { background: #305268; border-color: #63BFB6; }
QPushButton:pressed { background: #152C3A; }
QPushButton:focus { border: 2px solid #6DEFD9; }
QPushButton:disabled { color: #8097A5; background: #1A2B38; border-color: #314453; }
QPushButton#Primary { background: #34C7B3; color: #061A23; border: 1px solid #4EEAD5;
    font-weight: 800; font-size: 14px; min-height: 30px; }
QPushButton#Primary:hover { background: #69E9D3; }
QPushButton#Primary:disabled { background: #3D746F; color: #C1D7D6; border-color: #477E79; }
QPushButton#Quiet { background: transparent; border: 1px solid #3A556A; }
QPushButton#Danger { background: #453039; border: 1px solid #996072; }
QPushButton#Danger:hover { background: #633E4D; }
QComboBox, QLineEdit { background: #0E202E; color: #F4FCFF; border: 1px solid #476477;
    border-radius: 8px; padding: 10px; min-height: 20px; selection-background-color: #197F83; }
QComboBox:hover, QLineEdit:hover { border-color: #65D2C0; }
QComboBox::drop-down { border: none; width: 25px; }
QComboBox QAbstractItemView { background: #152A3A; border: 1px solid #65B3B0;
    color: white; selection-background-color: #236A76; padding: 6px; }
QTreeWidget { background: #0E1C2A; color: #EDF4F8; alternate-background-color: #152736;
    border: 1px solid #334A5C; border-radius: 10px; padding: 5px; outline: none; }
QTreeWidget::item { padding: 9px 6px; border-bottom: 1px solid #253B4B; }
QTreeWidget::item:selected { background: #1F5664; color: white; }
QTreeWidget::item:hover { background: #244251; }
QHeaderView::section { background: #172C3D; color: #AFCAD4; padding: 10px;
    font-weight: 700; border: 0; border-bottom: 1px solid #496171; }
QProgressBar { border: 1px solid #446474; background: #0C1B29;
    color: white; border-radius: 7px; height: 19px; text-align: center; font-weight: 650; }
QProgressBar::chunk { background: #35CDBB; border-radius: 6px; }
QPlainTextEdit { background: #081622; color: #AEE3D5; border: 1px solid #365567;
    border-radius: 9px; padding: 10px; font-family: 'Consolas', 'DejaVu Sans Mono', monospace; font-size: 12px; }
QMenuBar { background: #0E1A27; color: #DFEEF6; padding: 4px; }
QMenuBar::item:selected, QMenu::item:selected { background: #295262; }
QMenu { background: #142838; border: 1px solid #4B697A; padding: 6px; }
QStatusBar { background: #0C1823; color: #A7BEC9; border-top: 1px solid #2E4858; }
QToolTip { color: white; background: #213B4A; border: 1px solid #4C9E9D; padding: 6px; }
QSplitter::handle { background: transparent; }
QScrollBar:vertical { background: #122633; width: 11px; }
QScrollBar::handle:vertical { background: #456879; border-radius: 5px; min-height: 22px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
"""