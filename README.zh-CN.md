# DNFTM ModKit

[English](README.md) | **简体中文** | [繁體中文](README.zh-TW.md)

非官方的《Do Not Feed the Monkeys》（不要喂猴子，Fictiorama Studios，2018）模组工具包：运行时的 mod loader、
安装器、浏览器版笼子编辑器，以及用它做的两个剧情笼子。

> 本项目与 Fictiorama Studios 及游戏发行商无关，也未经其认可。你需要自己拥有这款游戏（Windows，Steam 或 GOG）。
> 仓库里**没有任何游戏文件**：没有游戏的 DLL、没有提取出来的图片、没有游戏文本。loader 是在玩家自己的电脑上修改游戏。

## 内容

| | 版本 | |
|---|---|---|
| ModLoader（`src/ModLoader`） | 0.5.10 | 运行时从游戏的 `Mods` 文件夹加载笼子：新笼子、用自己的 PNG 和动画做的场景、笔记本页、浏览器网页、新闻与结局插图、奖品架上的物品。主菜单会多一个「模组」页。 |
| 安装器（`src/Installer`） | 0.5.10 | 用 Mono.Cecil 把 loader 的钩子注入游戏的 `Assembly-UnityScript.dll`，并保留备份；选 2 可还原。 |
| 编辑器（`editor/`） | 0.5.0 | 用 Chrome 或 Edge 打开 `editor/index.html`。可以编辑 loader 支持的全部功能，会检查会让游戏出错的设置，并直接读写 `Mods` 文件夹。 |
| 飞蛾屏幕 Moth Screen（`data/MothScreen`） | 2.5 | 7 天剧情笼子：你看着一个被雇来找出女人住址的少年黑客的电脑桌面，听他的麦克风。有搜索、推理、打电话、聊天、上门和多种结局。英文与简体中文。 |
| 下行中 Going Down（`data/LiftCam`） | 0.6.2 | 「假笼子」：公寓电梯的监控摄像头。没有关键词，只能看。英文与简体中文。 |

## 玩家

到 Releases 页面下载 `DNFTM-Cages-<版本>.zip`，然后：

1. 把压缩包里的**所有**文件复制到游戏文件夹（`dnftm.exe` 旁边）。
2. 运行 `DNFTM-ModInstaller.exe`，输入 `1`。第一行会显示安装器与 loader 的版本，例如
   `DNFTM Mod Installer 0.5.10 (ModLoader 0.5.10)`。
3. 启动游戏，主菜单的笔记本上会多一个「模组」页：勾选笼子后开**新游戏**。

移除：再运行一次安装器并输入 `2`，然后删掉 `Mods` 文件夹。

## 做笼子的人

下载 `DNFTM-ModKit-<版本>.zip`（安装器、loader、两个笼子、编辑器），或直接使用这个仓库。
编辑器说明：`editor/README_编辑器说明.txt`。

公开版编辑器**没有场景预览图**（那是游戏本身的美术）。如果你有这款游戏，可以从自己的游戏几秒内重新生成完整的
catalog（分步教程，繁体中文：`editor/README_從遊戲提取預覽圖.txt`）：

```bash
python -m pip install UnityPy Pillow opencc
python tools/build_catalog.py "<游戏文件夹>/dnftm_Data" editor/catalog.js
```

生成的文件请自己使用，不要传播：里面有游戏的图片。

### loader 0.5.10 支持的 mod.json 功能

| 字段 | 起始版本 | 用途 |
|---|---|---|
| `cages` `[{id, insertAt}]` | ≤ 0.5 | 注册笼子（笼子 JSON 放在 `files/<id>.json`，文本放在 `merge/loc/{en,ch}.json`）。 |
| `sceneTemplates` `[{id, cloneFrom, keepCameras, art}]` | ≤ 0.5 | 复制游戏的场景；`art` 用你自己的 PNG 建立镜头（对象、精灵图、动画、夜晚图层）。 |
| `cameraEffects` `[{story, cloneFrom}]` | ≤ 0.5 | 笼子固定的镜头画面风格。 |
| 图片路径 `mods/<Mod>/<文件名>` | 0.5 | 新闻、浏览器网页、聊天头像、结局、门口访客使用你的 PNG。 |
| `diaryPages[].words / keep / actions` | 0.5.3 | 从游戏笼子复制的笔记本页：关键字对应字段、保留的圆圈与箭头、电话／聊天按钮。 |
| `diaryPages[].main / upper / copies` | 0.5.4 | 能在电话／聊天／任务中选的字、大写人名、复制的方框与字段。 |
| `diaryPages[].selectors` | 0.5.5 | 推理：圆圈旁的「？」与三个答案。 |
| `diaryPages[].moves` | 0.5.6 | 移动页面元素；`sx`／`sy` 可放大缩小（0.5.9）。 |
| `minLoader` | ≤ 0.5 | 玩家的 loader 太旧时，「模组」页会提示更新。 |
| `prizes` `[{id, template, x, y, image, selected, popup}]` | 0.5.10 | 奖品在房间奖品架上的专属对象（没有的话，玩家收到奖品时游戏会卡住）。 |

### 从源代码构建

loader 与安装器（需要 .NET 8 SDK；loader 和游戏一样以 .NET 3.5 为目标，并引用游戏本身的 DLL，所以要指向你的游戏）：

```bash
cd src/ModLoader && dotnet build -c Release -p:GameManaged="<游戏文件夹>/dnftm_Data/Managed"
cd ../Installer  && dotnet build -c Release
```

两者的版本号统一写在 `src/Directory.Build.props`，必须和 `src/ModLoader/Hooks.cs` 里的 `Version` 一致。

笼子（Python 3，需要 Pillow 和 numpy：`python -m pip install Pillow numpy`）。先构建到临时文件夹，再复制到 `data/`
（构建脚本会读取 `data/` 里上一版的文件，让文本编号保持不变）：

```bash
python tools/build_moth.py /tmp/out     # -> /tmp/out/MothScreen
python tools/build_liftcam.py /tmp/out  # -> /tmp/out/LiftCam
```

发布包：`python tools/make_release.py 1.0`（任何版本号不一致都会停下）。

### 目录

```
src/            ModLoader 与安装器（C#）
editor/         浏览器编辑器（catalog.js 不含游戏图片）
tools/          笼子构建脚本、美术工具、catalog 提取、发布脚本
data/           两个笼子（放进游戏 Mods 文件夹的样子，附 STORY.md 剧情设定，有剧透！）
art_override/   两个笼子的正式插图（为本项目制作）
release/        玩家说明与这些仓库文件
```

## 许可

代码、编辑器、两个笼子及其插图以 MIT 许可发布（见 `LICENSE`）。《Do Not Feed the Monkeys》及其素材属于其权利人，
不包含在本项目中。
