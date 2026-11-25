# DNFTM ModKit

[English](README.md) | [简体中文](README.zh-CN.md) | **繁體中文**

非官方的《Do Not Feed the Monkeys》（不要餵猴子，Fictiorama Studios，2018）模組工具包：執行時期的 mod loader、
安裝器、瀏覽器版籠子編輯器，以及用它做的兩個劇情籠子。

> 本專案與 Fictiorama Studios 及遊戲發行商無關，也未經其認可。你需要自己擁有這款遊戲（Windows，Steam 或 GOG）。
> 倉庫裡**沒有任何遊戲檔案**：沒有遊戲的 DLL、沒有擷取出來的圖片、沒有遊戲文字。loader 是在玩家自己的電腦上修改遊戲。

## 內容

| | 版本 | |
|---|---|---|
| ModLoader（`src/ModLoader`） | 0.5.10 | 執行時從遊戲的 `Mods` 資料夾載入籠子：新籠子、用自己的 PNG 和動畫做的場景、筆記本頁、瀏覽器網頁、新聞與結局插圖、獎品架上的物品。主選單會多一個「模组」頁。 |
| 安裝器（`src/Installer`） | 0.5.10 | 用 Mono.Cecil 把 loader 的掛鉤注入遊戲的 `Assembly-UnityScript.dll`，並保留備份；選 2 可還原。 |
| 編輯器（`editor/`） | 0.5.0 | 用 Chrome 或 Edge 開啟 `editor/index.html`。可以編輯 loader 支援的全部功能，會檢查會讓遊戲出錯的設定，並直接讀寫 `Mods` 資料夾。 |
| 飛蛾螢幕 Moth Screen（`data/MothScreen`） | 2.5 | 7 天劇情籠子：你看著一個被雇來找出女人住址的少年黑客的電腦桌面，聽他的麥克風。有搜尋、推理、打電話、聊天、上門和多種結局。英文與簡體中文。 |
| 下行中 Going Down（`data/LiftCam`） | 0.7 | 「假籠子」：公寓電梯的監視器。沒有關鍵詞，只能看。英文與簡體中文。 |

## 玩家

到 Releases 頁面下載 `DNFTM-Cages-<版本>.zip`，然後：

1. 把壓縮檔裡的**所有**檔案複製到遊戲資料夾（`dnftm.exe` 旁邊）。
2. 執行 `DNFTM-ModInstaller.exe`，輸入 `1`。第一行會顯示安裝器與 loader 的版本，例如
   `DNFTM Mod Installer 0.5.10 (ModLoader 0.5.10)`。
3. 啟動遊戲，主選單的筆記本上會多一個「模组」頁：勾選籠子後開**新遊戲**。

移除：再執行一次安裝器並輸入 `2`，然後刪掉 `Mods` 資料夾。

## 做籠子的人

下載 `DNFTM-ModKit-<版本>.zip`（安裝器、loader、兩個籠子、編輯器），或直接使用這個倉庫。
編輯器說明：`editor/README_编辑器说明.txt`（簡體中文）。

公開版編輯器**沒有場景預覽圖**（那是遊戲本身的美術）。如果你有這款遊戲，可以從自己的遊戲幾秒內重新產生完整的
catalog（逐步教學：`editor/README_從遊戲提取預覽圖.txt`）：

```bash
python -m pip install UnityPy Pillow opencc
python tools/build_catalog.py "<遊戲資料夾>/dnftm_Data" editor/catalog.js
```

產生的檔案請自己使用，不要散布：裡面有遊戲的圖片。

### loader 0.5.10 支援的 mod.json 功能

| 欄位 | 起始版本 | 用途 |
|---|---|---|
| `cages` `[{id, insertAt}]` | ≤ 0.5 | 註冊籠子（籠子 JSON 放在 `files/<id>.json`，文字放在 `merge/loc/{en,ch}.json`）。 |
| `sceneTemplates` `[{id, cloneFrom, keepCameras, art}]` | ≤ 0.5 | 複製遊戲的場景；`art` 用你自己的 PNG 建立鏡頭（物件、精靈圖、動畫、夜晚圖層）。 |
| `cameraEffects` `[{story, cloneFrom}]` | ≤ 0.5 | 籠子固定的鏡頭畫面風格。 |
| 圖片路徑 `mods/<Mod>/<檔名>` | 0.5 | 新聞、瀏覽器網頁、聊天頭像、結局、門口訪客使用你的 PNG。 |
| `diaryPages[].words / keep / actions` | 0.5.3 | 從遊戲籠子複製的筆記本頁：關鍵字對應字段、保留的圓圈與箭頭、電話／聊天按鈕。 |
| `diaryPages[].main / upper / copies` | 0.5.4 | 能在電話／聊天／任務中選的字、大寫人名、複製的方框與字段。 |
| `diaryPages[].selectors` | 0.5.5 | 推理：圓圈旁的「？」與三個答案。 |
| `diaryPages[].moves` | 0.5.6 | 移動頁面元素；`sx`／`sy` 可放大縮小（0.5.9）。 |
| `minLoader` | ≤ 0.5 | 玩家的 loader 太舊時，「模组」頁會提示更新。 |
| `prizes` `[{id, template, x, y, image, selected, popup}]` | 0.5.10 | 獎品在房間獎品架上的專屬物件（沒有的話，玩家收到獎品時遊戲會卡住）。 |

### 從原始碼建置

loader 與安裝器（需要 .NET 8 SDK；loader 和遊戲一樣以 .NET 3.5 為目標，並參照遊戲本身的 DLL，所以要指向你的遊戲）：

```bash
cd src/ModLoader && dotnet build -c Release -p:GameManaged="<遊戲資料夾>/dnftm_Data/Managed"
cd ../Installer  && dotnet build -c Release
```

兩者的版本號統一寫在 `src/Directory.Build.props`，必須和 `src/ModLoader/Hooks.cs` 裡的 `Version` 一致。

籠子（Python 3，需要 Pillow 和 numpy：`python -m pip install Pillow numpy`）。先建置到暫存資料夾，再複製到 `data/`
（建置腳本會讀取 `data/` 裡上一版的檔案，讓文字編號保持不變）：

```bash
python tools/build_moth.py /tmp/out     # -> /tmp/out/MothScreen
python tools/build_liftcam.py /tmp/out  # -> /tmp/out/LiftCam
```

發佈套件：`python tools/make_release.py 1.0`（任何版本號不一致都會停下）。

### 目錄

```
src/            ModLoader 與安裝器（C#）
editor/         瀏覽器編輯器（catalog.js 不含遊戲圖片）
tools/          籠子建置腳本、美術工具、catalog 提取、發佈腳本
data/           兩個籠子（放進遊戲 Mods 資料夾的樣子，附 STORY.md 劇情設定，有劇透！）
art_override/   兩個籠子的正式插圖（為本專案製作）
release/        玩家說明與這些倉庫檔案
```

## 授權

程式碼、編輯器、兩個籠子及其插圖以 MIT 授權釋出（見 `LICENSE`）。《Do Not Feed the Monkeys》及其素材屬於其權利人，
不包含在本專案中。
