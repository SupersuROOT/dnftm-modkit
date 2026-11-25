using System;
using System.Collections.Generic;
using System.IO;
using TMPro;
using UnityEngine;

namespace DNFTMModLoader
{
    /// <summary>
    /// Which mods are ticked on the MODS page (Selected) and which mods the current save was started with (SaveMods).
    /// The game keeps a single save (game.save, replaced by every new game), so one list is enough.
    /// Stored in Mods/state.json.
    /// </summary>
    internal static class ModState
    {
        public static List<string> Selected = new List<string>();
        public static List<string> SaveMods = new List<string>();
        static string path;
        static bool loaded;

        public static void Load(IList<Hooks.ModInfo> installed)
        {
            if (loaded) return;
            loaded = true;
            path = Path.Combine(Path.Combine(Path.GetDirectoryName(Application.dataPath), "Mods"), "state.json");
            try
            {
                if (File.Exists(path))
                {
                    var o = MiniJson.Parse(File.ReadAllText(path)) as JsonObject;
                    Selected = Strings(o != null ? o["selected"] : null);
                    SaveMods = Strings(o != null ? o["save"] : null);
                    return;
                }
                // First run after upgrading from v0.3 (mods were always on): keep an existing save working.
                bool hasSave = File.Exists(Application.persistentDataPath + "/game.save");
                Selected = new List<string>();
                SaveMods = new List<string>();
                if (hasSave) foreach (var m in installed) SaveMods.Add(m.Folder);
                Write();
                Hooks.Log("Created Mods/state.json" + (hasSave ? " (existing save keeps all mods)" : ""));
            }
            catch (Exception e) { Hooks.Log("ERROR reading state.json: " + e.Message); }
        }

        static List<string> Strings(object v)
        {
            var list = new List<string>();
            var a = v as List<object>;
            if (a != null) foreach (var x in a) if (x is string) list.Add((string)x);
            return list;
        }

        public static void Write()
        {
            try
            {
                var o = new JsonObject();
                var sel = new List<object>(); foreach (var s in Selected) sel.Add(s);
                var sav = new List<object>(); foreach (var s in SaveMods) sav.Add(s);
                o["selected"] = sel;
                o["save"] = sav;
                if (Directory.Exists(Path.GetDirectoryName(path))) File.WriteAllText(path, MiniJson.Serialize(o));
            }
            catch (Exception e) { Hooks.Log("ERROR writing state.json: " + e.Message); }
        }
    }

    /// <summary>Adds a MODS option to the main menu notebook and a MODS page built from the game's own menu parts.</summary>
    internal static class ModMenu
    {
        public static void Build()
        {
            var menu = GameObject.Find("menu");
            if (menu == null || menu.GetComponent<MenuController>() == null) return;
            if (menu.GetComponent<ModMenuBuilder>() == null) menu.AddComponent<ModMenuBuilder>();
        }

        internal static bool Chinese { get { return PlayerPrefs.GetString("lang", "en") == "ch"; } }
        internal static string T(string zh, string en) { return Chinese ? zh : en; }
    }

    /// <summary>Builds the menu a couple of frames after start, once the language controller has applied its fonts.</summary>
    public class ModMenuBuilder : MonoBehaviour
    {
        int frames;
        bool built;
        Transform page;
        Transform menuMain;
        readonly List<GameObject> rows = new List<GameObject>();
        TextMeshPro saveInfo;
        GameObject optionText, titleText, infoText;
        string lastLang;

        /// <summary>Texts follow the language picked in SETTINGS (the game swaps fonts itself).</summary>
        void ApplyTexts()
        {
            lastLang = PlayerPrefs.GetString("lang", "en");
            if (optionText != null) SetText(optionText, ModMenu.T("模组", "MODS"));
            if (titleText != null) SetText(titleText, ModMenu.T("模组", "MODS"));
            if (infoText != null)
            {
                string info = Hooks.AllMods.Count == 0
                    ? ModMenu.T("没有安装任何模组。把模组放进游戏文件夹的 Mods 里。", "No mods installed. Put mods in the game's Mods folder.")
                    : ModMenu.T("勾选要启用的模组，然后开始新游戏。", "Tick the mods to use, then start a NEW GAME.");
                var old = Hooks.ModsNeedingNewerLoader();
                if (old.Count > 0)
                    info += "\n" + ModMenu.T("需要更新 ModLoader：", "Needs a newer ModLoader: ") + string.Join(", ", old.ToArray())
                          + ModMenu.T("。请重新运行新版安装器。", ". Run the new installer again.");
                info += "\nModLoader " + Hooks.Version;
                SetText(infoText, info);
            }
            UpdateSaveInfo();
        }

        void UpdateSaveInfo()
        {
            if (saveInfo == null) return;
            var names = new List<string>();
            foreach (var m in Hooks.AllMods) if (ModState.SaveMods.Contains(m.Folder)) names.Add(m.Name);
            saveInfo.text = ModMenu.T("当前存档使用的模组：", "Current save uses: ") +
                (names.Count == 0 ? ModMenu.T("无（原版游戏）", "none (original game)") : string.Join(", ", names.ToArray()));
        }

        void Update()
        {
            if (!built)
            {
                if (++frames < 3) return;
                built = true;
                try { BuildUi(); } catch (Exception e) { Hooks.Log("ERROR building MODS menu: " + e); }
                return;
            }
            if (PlayerPrefs.GetString("lang", "en") != lastLang) ApplyTexts();
            // The game's own back arrow returns to the main page; hide ours when that happens.
            if (page != null && page.gameObject.activeSelf && menuMain != null && menuMain.gameObject.activeSelf) page.gameObject.SetActive(false);
        }

        static GameObject CloneUnder(Transform source, Transform parent, string name)
        {
            var go = (GameObject)Instantiate(source.gameObject);
            go.name = name;
            go.transform.SetParent(parent, false);
            go.transform.localPosition = source.localPosition;
            go.transform.localRotation = source.localRotation;
            go.transform.localScale = source.localScale;
            go.layer = source.gameObject.layer;
            // Our texts are set by code; the game's localisation component would overwrite them.
            var loc = go.GetComponent<locationText>();
            if (loc != null) DestroyImmediate(loc);
            return go;
        }

        static void SetText(GameObject go, string text)
        {
            var t = go.GetComponent<TextMeshPro>();
            if (t != null) t.text = text;
        }

        void BuildUi()
        {
            menuMain = transform.Find("menuMain");
            var options = transform.Find("menuOptions");
            if (menuMain == null || options == null) { Hooks.Log("MODS menu: menu pages not found."); return; }

            // ---- option on the main page (copy of SETTINGS: text + hand-drawn oval)
            var srcText = menuMain.Find("menuMainOption4");
            var srcCircle = menuMain.Find("menuMainOption4Circle");
            var opt = CloneUnder(srcText, menuMain, "menuMainOptionMods");
            var basePos = new Vector3(-136f, 33f, srcText.localPosition.z);
            opt.transform.localPosition = basePos;
            optionText = opt;
            var mto = opt.GetComponent<menuTextOption>();
            if (mto != null) mto.type = "mods"; // keeps the hover effect, no built-in action
            opt.AddComponent<ModMenuClick>().onClick = ShowPage;
            if (srcCircle != null)
            {
                var circle = CloneUnder(srcCircle, menuMain, "menuMainOptionModsCircle");
                circle.transform.localPosition = basePos + (srcCircle.localPosition - srcText.localPosition);
                circle.transform.localPosition = new Vector3(circle.transform.localPosition.x, circle.transform.localPosition.y, srcCircle.localPosition.z);
            }

            // ---- MODS page (layout copied from the SETTINGS page)
            var pageGo = new GameObject("menuMods");
            page = pageGo.transform;
            page.SetParent(transform, false);
            page.localPosition = options.localPosition;
            page.localRotation = options.localRotation;
            page.localScale = options.localScale;
            pageGo.layer = options.gameObject.layer;

            var title = CloneUnder(options.Find("menuOption1"), page, "modsTitle");
            titleText = title;

            var labelSrc = options.Find("menuOption2");
            var boxSrc = options.Find("menuOption2_1");
            var installed = Hooks.AllMods;
            int max = Math.Min(installed.Count, 6);
            for (int i = 0; i < max; i++)
            {
                var mod = installed[i];
                float y = labelSrc.localPosition.y - 12f * i;
                var label = CloneUnder(labelSrc, page, "modsLabel" + i);
                label.transform.localPosition = new Vector3(labelSrc.localPosition.x, y, labelSrc.localPosition.z);
                string name = mod.Name.Length > 18 ? mod.Name.Substring(0, 17) + ".." : mod.Name;
                SetText(label, name);
                var box = CloneUnder(boxSrc, page, "modsCheck" + i);
                box.transform.localPosition = new Vector3(boxSrc.localPosition.x, y + (boxSrc.localPosition.y - labelSrc.localPosition.y), boxSrc.localPosition.z);
                var builtIn = box.GetComponent<menuCheckBox>();
                if (builtIn != null) DestroyImmediate(builtIn);
                var toggle = box.AddComponent<ModToggle>();
                toggle.folder = mod.Folder;
                rows.Add(label);
            }

            var info = CloneUnder(labelSrc, page, "modsInfo");
            info.transform.localPosition = new Vector3(labelSrc.localPosition.x, labelSrc.localPosition.y - 12f * 6.4f, labelSrc.localPosition.z);
            var infoTmp = info.GetComponent<TextMeshPro>();
            if (infoTmp != null) infoTmp.fontSize = infoTmp.fontSize * 0.6f;
            infoText = info;
            var save = CloneUnder(info.transform, page, "modsSaveInfo");
            save.transform.localPosition = info.transform.localPosition + new Vector3(0, -8f, 0);
            saveInfo = save.GetComponent<TextMeshPro>();

            var back = options.Find("back");
            if (back != null) CloneUnder(back, page, "back"); // same arrow and action as the SETTINGS page

            ApplyTexts();
            pageGo.SetActive(false);
            Hooks.Log("MODS menu ready (" + installed.Count + " mod(s)).");
        }

        void ShowPage()
        {
            var mc = GetComponent<MenuController>();
            if (mc != null) { try { mc.click(); } catch { } }
            foreach (var n in new[] { "menuCredits", "menuShortcuts", "menuMain", "menuNew", "menuLoad", "menuOptions", "menuExit" })
            {
                var t = transform.Find(n);
                if (t != null) t.gameObject.SetActive(false);
            }
            UpdateSaveInfo();
            page.gameObject.SetActive(true);
        }
    }

    /// <summary>Left-click handler for cloned menu texts (the game reacts on mouse-up while hovering).</summary>
    public class ModMenuClick : MonoBehaviour
    {
        public Action onClick;
        void OnMouseOver() { if (Input.GetMouseButtonUp(0) && onClick != null) onClick(); }
    }

    /// <summary>Checkbox on the MODS page; the tick is the game's own "check" sprite.</summary>
    public class ModToggle : MonoBehaviour
    {
        public string folder;
        Transform check;

        void Start()
        {
            check = transform.Find("check");
            if (check != null) check.gameObject.SetActive(ModState.Selected.Contains(folder));
        }

        void OnMouseOver()
        {
            if (!Input.GetMouseButtonUp(0)) return;
            bool on = !ModState.Selected.Contains(folder);
            if (on) ModState.Selected.Add(folder); else ModState.Selected.Remove(folder);
            ModState.Write();
            if (check != null) check.gameObject.SetActive(on);
            var mc = GetComponentInParent<MenuController>();
            if (mc != null) { try { mc.click(); } catch { } }
        }
    }
}
