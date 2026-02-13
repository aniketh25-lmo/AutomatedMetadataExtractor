import PyInstaller.__main__

PyInstaller.__main__.run([
    "run_scraper.py",
    "--name=FacultyScraper",
    "--onefile",
    "--windowed",
    "--clean",

    "--hidden-import=selenium",
    "--hidden-import=webdriver_manager",
    "--hidden-import=webdriver_manager.chrome",
    "--hidden-import=pandas",
    "--hidden-import=openpyxl",

    "--add-data=portable_scraper;portable_scraper",

    "--icon=icon.ico"
])
