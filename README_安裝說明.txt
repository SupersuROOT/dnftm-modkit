Do Not Feed the Monkeys - Mod 工具包 v1.0（安裝器 0.5.10、ModLoader 0.5.10、編輯器 v0.5.0、兩個籠子）
=====================================================================

這是非官方的 fan mod 工具包，附帶兩個籠子：
  飛蛾螢幕 Moth Screen v2.5   7 天劇情籠子：監看一個菜鳥黑客的電腦桌面與麥克風（說明見 Mods\MothScreen\README_飛蛾螢幕.txt）
  下行中 Going Down v0.6.2    公寓電梯的監視器（說明見 Mods\LiftCam\README_下行中.txt）
做自己的籠子請用 Editor 資料夾裡的編輯器，說明見 Editor\README_编辑器说明.txt。
編輯器不含遊戲畫面；有遊戲的話可照 Editor\README_從遊戲提取預覽圖.txt 從自己的遊戲提取預覽圖。

安裝器執行時第一行會顯示自己的版本和旁邊 loader 的版本，例如「DNFTM Mod Installer 0.5.10 (ModLoader 0.5.10)」；
安裝完成會顯示「Installed ModLoader 0.5.10」。

從舊版升級：請把這個資料夾裡的「所有檔案」（包含 DNFTMModLoader.dll 和 DNFTM-ModInstaller.exe）
複製到遊戲資料夾，再執行一次安裝器並選 1。只複製 Mods 資料夾是不夠的。

怎麼確認裝好了：主選單「模组」頁下方會顯示「ModLoader 0.5.10」。
沒有顯示版本號，就表示遊戲還在用舊版 loader，新聞／網頁的 mod 圖片會是空白、網頁打不開。
模组需要較新的 loader 時，模组頁也會直接提示。

v0.5 新功能：mod 可以用自己的 PNG 當新聞照片、瀏覽器搜尋結果（新聞、百科、Metayou、地圖、網頁）、
聊天頭像、結局插圖與門口訪客。在 JSON 的圖片欄位寫 mods/<Mod資料夾>/<檔名（不含 .png）>，
例如 "image": "mods/MothScreen/web/news_arrest"。尺寸請比照遊戲：照片 110x80、網頁背景 376x157、
地圖 364x107、聊天頭像 18x17、門口訪客 120x210。

v0.5.1：可點擊的自訂物件改用遊戲能隱藏的碰撞框（隱藏中的物件不再點得到），
並加上和原版一樣的滑鼠懸停描邊（圖片四周請留 2～3 像素透明邊）。
做劇情籠子的提醒：場景的日期是在「上一個場景做完」時決定的。深夜場景如果跑過午夜，
「隔天」(nextDay) 會變成後天。每天早上的第一個場景請用 nextAvailable（編輯器裡的「下一個 hour 點」）。
v0.5.10：mod.json "prizes" 可以替籠子的獎品（禮物）在房間的獎品架上建立自己的物件：
  [{"id": 獎品id, "template": "coca", "x": -2.27, "y": -0.85, "image": "web/小圖", "selected": "web/選取圖", "popup": "web/說明大圖"}]
  沒有自己的物件時，收到獎品會卡住（說明視窗關不掉）。
v0.5.9：diaryPages 的 moves／copies 可以加 "sx"、"sy" 放大或縮小物件（例如更大的方框）。
v0.5.8：自訂物件在兩個循環動畫之間切換時，動畫不會從頭重播（動作更連貫）。
v0.5.7：自訂籠子的攝影機改名為 mod<籠子id>_<原名>（保留最後一個字母 A/B），
同時裝了好幾個從同一個場景範本複製的籠子時，右鍵切換主畫面不會再弄錯籠子。
v0.5.6：diaryPages "moves": [{"name": "來源頁物件名", "dx": 0.2, "dy": -0.1}] 可以移動來源頁的物件
（例如「？」或答案欄位和別的框重疊時）。注意：zone 的 "mainWord" 成立時遊戲會把選中的答案藏起來，
若想保留答案又要附帶加入另一個詞，請在答案關鍵字上寫 "addWords": ["另一個詞"]。
v0.5.5：筆記本推理「？」。diaryPages 寫 "selectors": {"diaryCircle4": ["答案1", "答案2", "答案3"]}，
會保留來源頁該圈的「？」與移除圖示，並把三個選項換成你的關鍵字。三個答案要放在該圈疊在一起的選擇欄位
（sayCheese：圈1 atico/sotano/garaje、圈4 vigilante/paparazzi/chofer、圈5 deportista/modelo/actriz…），
diaryConfig 的 zone 加 "selectableWords" 與 "wordSelector"（例如 {"atLeast": 3, "haveWord": "某詞"}），
可選 "mainWord"（選對後自動加入另一個詞）。
v0.5.4：筆記本「主要詞」。遊戲在打電話、聊天、回覆俱樂部任務信時，只能選筆記本上的主要詞
（isMain，原版是人名那類大寫的詞）；複製來的頁面沿用來源欄位的設定，所以大多數詞選不到。
diaryPages 可以寫 "main": ["關鍵字", ...]（或 ["*"] 全部）指定可選的詞，"upper": [...] 指定用大寫顯示的詞；
"copies": [{"from": "diaryCircle7", "name": "diaryCircle8", "dx": 2.5, "dy": 1.0}, ...] 可以把來源頁的
框、圈或欄位複製一份到別的位置（例如再多一個「號碼＋姓名」的電話框），新欄位名稱可以在 words 裡使用。
電話／聊天的對話節點若有 keywords（用筆記本回答），遊戲就不顯示 texts 選項，請加上 "none" 作為掛斷選項，
或在 texts 的選項裡用 "gotoKeywords" 轉到筆記本節點。
v0.5.3：筆記本頁可以加撥號／聊天按鈕：diaryPages 裡寫 "actions": {"新關鍵字": "來源頁上有按鈕的欄位"}，
會把來源頁的 diaryWord<欄位>Action 按鈕複製到新關鍵字旁邊（關鍵字要有 clickEvents，例如 callTo）。
另外，遊戲會在籠子畫面左下角寫白色的「RECORDING」等提示，自訂畫面的那個角落請用深色。
詳細模式下按 F9 可以直接解鎖錄影功能，方便測試 Shock.tv 投稿。
v0.5.2：模组頁顯示 loader 版本；mod.json 可以寫 "minLoader": "0.5.2"，版本不夠時模组頁會提示。

給做 mod 的人：在 Mods 資料夾放一個空的 verbose.txt，ModLoader.log 會記錄更多資訊，
而且遊戲中按 F8 會依序直接打開目前 mod 籠子的每個瀏覽器搜尋結果（不用先收集關鍵字），
方便檢查自訂網頁、百科、Metayou 頁和圖片。

v0.4 起，安裝 mod 不會再改變原版遊戲：
  * 主選單筆記本上多了一個「模组 / MODS」選項，進去勾選要玩的 mod，再按「新遊戲」。
  * 沒有勾選任何 mod 時，就是 100% 原版遊戲。
  * 「繼續遊戲 / 讀取遊戲」會自動使用那份存檔開始時勾選的 mod。
  * 從 v0.3 升級時如果已經有存檔，第一次啟動會把現有的 mod 都視為那份存檔的 mod，舊存檔不會壞掉。

* 夜讀者的場景美術借用遊戲內 Red Fred 的客廳；幽靈房間是全自訂美術。
* 支援簡體中文與英文介面。遊戲的中文字型只有簡體字，所以 mod 的中文是簡體。
* 新的關鍵字可以寫進筆記本，也可以用瀏覽器搜尋。
* 範例籠子會插在攝影機清單最前面（需要先在「模组」頁勾選）。


安裝方式
--------
1. 先備份你的存檔（保險起見）。
2. 解壓縮後，把 DNFTM-NightReader-v0.1 資料夾「裡面」的所有檔案和 Mods 資料夾，
   複製到遊戲資料夾，也就是 dnftm.exe 所在的資料夾。
   Steam 版通常在：C:\Program Files (x86)\Steam\steamapps\common\Do Not Feed the Monkeys
   GOG 版請在 GOG Galaxy 裡按「管理安裝 → 顯示資料夾」找到。
3. 雙擊執行 DNFTM-ModInstaller.exe，輸入 1 後按 Enter（安裝）。
4. 啟動遊戲，在主選單點「模组」，勾選想玩的 mod，按左下的箭頭返回，再選「新遊戲」。

安裝器會：
  * 備份 dnftm_Data\Managed\Assembly-UnityScript.dll（備份檔名為 .dnftm-backup）
  * 在這個 DLL 裡加上幾個呼叫點，讓遊戲讀取 Mods 資料夾（含 mod 圖片）
  * 複製 DNFTMModLoader.dll 到 dnftm_Data\Managed

需要 .NET Framework 4.7.2 以上；Windows 10/11 已內建。


解除安裝
--------
執行 DNFTM-ModInstaller.exe，輸入 2。原始 DLL 會被還原成和安裝前一模一樣的檔案。
也可以在 Steam / GOG 裡「驗證遊戲檔案完整性」。

只想暫時不玩 mod：在主選單「模组」頁取消勾選，再開新遊戲即可。
要讓某個 mod 完全不被載入：把 Mods 底下該資料夾改名，在名稱前加上底線，例如 _NightReader。


注意事項
--------
* 有 mod 的存檔，在移除 mod 之後可能無法正常讀取，請另外備份。
* Steam / GOG 更新遊戲或驗證檔案之後，需要重新執行安裝器。
* 出問題時請查看 Mods\ModLoader.log。


Mod 資料夾格式（給想自己做籠子的人）
------------------------------------
Mods\<你的Mod>\
  mod.json            註冊新籠子、場景模板、攝影機特效、筆記本頁
  files\<路徑>        新增或取代遊戲的 JSON 檔（例如 files\nightReader.json）
  merge\<路徑>        把 JSON 深度合併進遊戲原本的檔案（例如 merge\loc\ch.json 語言包）
JSON 檔案裡可以寫 // 註解。
