從自己的遊戲提取編輯器預覽圖（教學）
====================================

公開發佈的編輯器不含遊戲畫面：新增籠子時挑選的場景預覽、素材分頁裡的背景和角色圖，
都是《Do Not Feed the Monkeys》本身的美術，不能公開散布。
沒有預覽圖時編輯器照樣能用，只是會顯示「没有预览图」的灰框。

如果你有這款遊戲，可以從自己的遊戲重新產生完整的 catalog.js，大約 5 分鐘。
產生的檔案只給自己用，請不要再上傳或散布。


需要的東西
----------
* 已安裝的遊戲（Steam 或 GOG，Windows 版）。
* Python 3（免費）。
* 工具包裡的 tools\build_catalog.py。


步驟（Windows）
---------------
1. 安裝 Python
   到 https://www.python.org/downloads/ 下載 Python 3（3.10 以上都可以）並安裝。
   安裝畫面第一頁請勾選「Add python.exe to PATH」。

2. 安裝提取需要的三個套件
   按 Win 鍵，輸入 cmd，開啟「命令提示字元」，輸入下面這一行後按 Enter：

       py -m pip install UnityPy Pillow opencc

   看到 Successfully installed 就完成了。

3. 找到遊戲資料夾裡的 dnftm_Data
   Steam：在遊戲上按右鍵 → 管理 → 瀏覽本機檔案。
   GOG Galaxy：遊戲頁 → 管理安裝 → 顯示資料夾。
   打開的資料夾裡有 dnftm.exe 和 dnftm_Data，我們要的是 dnftm_Data 的完整路徑，
   例如 C:\Program Files (x86)\Steam\steamapps\common\Do Not Feed the Monkeys\dnftm_Data
   （在檔案總管的網址列點一下，就能複製路徑）。

4. 執行提取
   在命令提示字元先切換到工具包資料夾（有 Editor 和 tools 的那一層），例如：

       cd /d D:\DNFTM-ModKit

   然後執行（把引號裡換成你在第 3 步複製的路徑）：

       py tools\build_catalog.py "C:\...\Do Not Feed the Monkeys\dnftm_Data" Editor\catalog.js

   幾秒後最後一行會出現類似 glyphs 2607 t2s 1149 images 991 cages 47 的訊息，
   Editor\catalog.js 就換成含預覽圖的完整版了（約 1.6 MB，原本的公開版約 0.3 MB）。

5. 重新開啟 Editor\index.html
   瀏覽器若還顯示灰框，按 Ctrl+F5 強制重新整理。


常見問題
--------
* 「py 不是內部或外部命令」：安裝 Python 時沒有勾選加入 PATH。重新執行安裝程式，選 Modify，
  勾選 Add Python to environment variables；或改用 python 代替 py。
* 「No module named UnityPy」：第 2 步沒有成功，再執行一次，並確認沒有出現紅色錯誤。
* 「FileNotFoundError ... level3」：路徑要指到 dnftm_Data 資料夾本身，不是遊戲資料夾或 dnftm.exe。
* 想換回公開版：重新解壓工具包裡的 Editor\catalog.js 即可。
* 安裝 opencc 出錯：改裝相容版 py -m pip install opencc-python-reimplemented，再執行第 4 步。
* Linux：步驟相同，把 py 換成 python3，路徑用 / 分隔。
