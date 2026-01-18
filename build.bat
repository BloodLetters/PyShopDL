pyinstaller main.py ^
  --name PyShopDL ^
  --onefile ^
  --noconsole ^
  --add-data "qss;qss" ^
  --add-data "Assets;Assets" ^
  --add-data "config.json;."