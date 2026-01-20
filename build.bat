pyinstaller main.py ^
  --name PyShopDL ^
  --onefile ^
  --noconsole ^
  --icon "Assets/icon.ico" ^
  --add-data "qss;qss" ^
  --add-data "Assets;Assets" ^
  --add-data "config.json;." ^
  --distpath "build"