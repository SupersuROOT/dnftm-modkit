using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using UnityEngine;

namespace DNFTMModLoader
{
    /// <summary>
    /// Entry points called from code the installer injects into Assembly-UnityScript.dll.
    ///
    /// Injected pattern (prefix) for each file-reading method M(string name):
    ///     if (Hooks.HandlesX(name)) return Hooks.X(name);
    ///     ...original body...
    ///
    /// Mod folder layout (game root / Mods / &lt;ModName&gt;):
    ///     mod.json            optional: { "name": "...", "cages": [ { "id": "myCage", "insertAt": 0 } ] }
    ///     files/&lt;path&gt;       new or replacement file, e.g. files/myCage.json, files/external/myCage/myCage_DIA1.json
    ///     merge/&lt;path&gt;       JSON deep-merged into the game's file, e.g. merge/loc/ch.json, merge/externalFiles.json
    /// Folders whose name starts with '_' or '.' are ignored (an easy way to disable a mod).
    /// </summary>
    public static class Hooks
    {
        internal const string Version = "0.5.10";

        static bool initialized;
        /// <summary>Extra diagnostics in ModLoader.log; enabled by an empty file Mods/verbose.txt.</summary>
        internal static bool Verbose;
        static string modsRoot;
        /// <summary>Every installed mod folder.</summary>
        static readonly List<ModInfo> allMods = new List<ModInfo>();
        /// <summary>Mods applied right now: none in the main menu (original game), the save's mods in the game scene.</summary>
        static List<ModInfo> mods = new List<ModInfo>();
        internal static IList<ModInfo> AllMods { get { return allMods; } }
        static readonly Dictionary<string, string> cache = new Dictionary<string, string>();

        [ThreadStatic] static bool inOriginal;

        internal sealed class CageEntry
        {
            public string Id;
            public int InsertAt;
        }

        /// <summary>
        /// A diary (notebook) page for a new cage, cloned from an existing cage's page.
        /// Words maps newKeywordId -> existing slot id on the source page (diaryWord&lt;slot&gt;).
        /// Keep lists other children of the source page to keep (circles, arrows...); everything else is removed.
        /// </summary>
        internal sealed class DiaryPage
        {
            public string Story;
            public string CloneFrom;
            public readonly Dictionary<string, string> Words = new Dictionary<string, string>();
            public readonly List<string> Keep = new List<string>();
            /// <summary>New keyword id -> slot id on the source page whose button (diaryWord&lt;slot&gt;Action: the phone/chat
            /// icon next to a phone number or contact) is copied next to the keyword's own slot.</summary>
            public readonly Dictionary<string, string> Actions = new Dictionary<string, string>();
            /// <summary>Keywords whose slot is a "main" word (keywordInterface.isMain): only main words can be picked when
            /// answering a phone call, chat or Club mission with the notebook. Null = keep the source slots' flags.</summary>
            public HashSet<string> Main;
            /// <summary>Main keywords drawn in capitals like the game's names; other main words keep their case.</summary>
            public readonly HashSet<string> Upper = new HashSet<string>();
            /// <summary>Extra page parts copied from the source page (e.g. a second phone box): name, source child, offset.</summary>
            public readonly List<PageCopy> Copies = new List<PageCopy>();
            /// <summary>Deduction "?" per circle: circle -> the three keywords offered (the game's own word selector).
            /// Keeps diaryCircleN(Selector|iconPosition) and points the selector's option buttons at these keywords.</summary>
            public readonly Dictionary<string, List<string>> Selectors = new Dictionary<string, List<string>>();
            /// <summary>Source page children to shift (every child with that name), e.g. a selector that overlaps a box.</summary>
            public readonly List<PageCopy> Moves = new List<PageCopy>();
        }

        /// <summary>Sx/Sy (0.5.9): optional scale factors (default 1), e.g. a bigger box frame.</summary>
        internal sealed class PageCopy { public string From, Name; public float Dx, Dy, Sx = 1f, Sy = 1f; }

        static float ToF(object o)
        {
            var n = o as JsonNumber; float f;
            return n != null && float.TryParse(n.Text, System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out f) ? f : 0f;
        }

        /// <summary>Like ToF, but a missing value means "unchanged" (1).</summary>
        static float ToScale(object o) { return o is JsonNumber ? ToF(o) : 1f; }

        /// <summary>
        /// A cage scene template "Story&lt;Id&gt;" derived from an existing one ("Story&lt;CloneFrom&gt;").
        /// KeepCameras trims the camera nodes (children A, B, ...) so the template matches the
        /// "cameras" count of the cage script; the game allocates per-camera arrays from that count
        /// but iterates the template's children when saving.
        /// </summary>
        internal sealed class SceneTemplate
        {
            public string Id;
            public string CloneFrom;
            public int KeepCameras;
            /// <summary>Optional custom art: { "cameras": [ { "clear": bool, "objects": [...] } ] }.</summary>
            public JsonObject Art;
            public string ModDir;
        }

        internal sealed class ModInfo
        {
            public string Folder { get { return Path.GetFileName(Dir); } }
            public string Name;
            public string Dir;
            /// <summary>Optional "minLoader" in mod.json: the oldest ModLoader version the mod works with.</summary>
            public string MinLoader;
            public readonly List<CageEntry> Cages = new List<CageEntry>();
            public readonly List<DiaryPage> DiaryPages = new List<DiaryPage>();
            public readonly List<SceneTemplate> SceneTemplates = new List<SceneTemplate>();
            /// <summary>new cage id -> existing cage id whose fixed camera effect (storyEffects/&lt;id&gt;) to copy.</summary>
            public readonly Dictionary<string, string> CameraEffects = new Dictionary<string, string>();
            /// <summary>0.5.10: prizes (gifts) that get their own object on the prize shelf.</summary>
            public readonly List<ModPrize> Prizes = new List<ModPrize>();
        }

        /// <summary>
        /// A cage prize with its own shelf object. The game shows a prize by activating the scene object
        /// prizeHolderItems/&lt;prize id&gt; and reads that object's prizeInterface.popupBackground for the info popup;
        /// a prize without such an object throws there and leaves the popup stuck. The loader copies an original
        /// prize object (Template), renames it to the prize id, moves it to X/Y/Z (prizeHolderItems local units)
        /// and replaces its art: Image (shelf picture), Selected (hover version, optional), Popup (the 289x183
        /// popup picture, drawn from its bottom-left corner like the game's).
        /// </summary>
        internal sealed class ModPrize
        {
            public string Id, Template = "coca", Image, Selected, Popup;
            public float X, Y, Z = -21f;
        }

        // ------------------------------------------------------------------ init

        static void EnsureInit()
        {
            if (initialized) return;
            initialized = true;
            try
            {
                modsRoot = Path.Combine(Path.GetDirectoryName(Application.dataPath), "Mods");
                ResetLog();
                Verbose = File.Exists(Path.Combine(modsRoot, "verbose.txt"));
                Log("DNFTMModLoader " + Version + " - mods folder: " + modsRoot);
                if (!Directory.Exists(modsRoot))
                {
                    Log("No Mods folder; nothing to load.");
                    return;
                }
                var dirs = Directory.GetDirectories(modsRoot);
                Array.Sort(dirs, StringComparer.OrdinalIgnoreCase);
                foreach (string dir in dirs)
                {
                    string name = Path.GetFileName(dir);
                    if (name.StartsWith("_") || name.StartsWith(".")) { Log("Skipping disabled mod folder " + name); continue; }
                    var mod = new ModInfo { Name = name, Dir = dir };
                    string manifest = Path.Combine(dir, "mod.json");
                    if (File.Exists(manifest))
                    {
                        try
                        {
                            var m = MiniJson.Parse(File.ReadAllText(manifest)) as JsonObject;
                            if (m != null)
                            {
                                if (m["name"] is string) mod.Name = (string)m["name"];
                                if (m["minLoader"] is string) mod.MinLoader = (string)m["minLoader"];
                                var cages = m["cages"] as List<object>;
                                if (cages != null)
                                {
                                    foreach (object c in cages)
                                    {
                                        var co = c as JsonObject;
                                        if (co == null || !(co["id"] is string)) continue;
                                        int at = 0;
                                        if (co["insertAt"] is JsonNumber) int.TryParse(((JsonNumber)co["insertAt"]).Text, out at);
                                        mod.Cages.Add(new CageEntry { Id = (string)co["id"], InsertAt = at });
                                    }
                                }
                                var templates = m["sceneTemplates"] as List<object>;
                                if (templates != null)
                                {
                                    foreach (object t in templates)
                                    {
                                        var to = t as JsonObject;
                                        if (to == null || !(to["id"] is string) || !(to["cloneFrom"] is string)) continue;
                                        int keep = 0;
                                        if (to["keepCameras"] is JsonNumber) int.TryParse(((JsonNumber)to["keepCameras"]).Text, out keep);
                                        mod.SceneTemplates.Add(new SceneTemplate { Id = (string)to["id"], CloneFrom = (string)to["cloneFrom"], KeepCameras = keep, Art = to["art"] as JsonObject, ModDir = dir });
                                    }
                                }
                                var effects = m["cameraEffects"] as List<object>;
                                if (effects != null)
                                {
                                    foreach (object e in effects)
                                    {
                                        var eo = e as JsonObject;
                                        if (eo != null && eo["story"] is string && eo["cloneFrom"] is string)
                                            mod.CameraEffects[(string)eo["story"]] = (string)eo["cloneFrom"];
                                    }
                                }
                                var prizes = m["prizes"] as List<object>;
                                if (prizes != null)
                                    foreach (object e in prizes)
                                    {
                                        var po = e as JsonObject;
                                        if (po == null || !(po["id"] is string)) continue;
                                        var pr = new ModPrize { Id = (string)po["id"], Image = po["image"] as string, Selected = po["selected"] as string,
                                                                Popup = po["popup"] as string, X = ToF(po["x"]), Y = ToF(po["y"]) };
                                        if (po["template"] is string) pr.Template = (string)po["template"];
                                        if (po["z"] is JsonNumber) pr.Z = ToF(po["z"]);
                                        mod.Prizes.Add(pr);
                                    }
                                var pages = m["diaryPages"] as List<object>;
                                if (pages != null)
                                {
                                    foreach (object p in pages)
                                    {
                                        var po = p as JsonObject;
                                        if (po == null || !(po["story"] is string) || !(po["cloneFrom"] is string)) continue;
                                        var page = new DiaryPage { Story = (string)po["story"], CloneFrom = (string)po["cloneFrom"] };
                                        var words = po["words"] as JsonObject;
                                        if (words != null) foreach (string k in words.Keys) if (words[k] is string) page.Words[k] = (string)words[k];
                                        var keep = po["keep"] as List<object>;
                                        if (keep != null) foreach (object k in keep) if (k is string) page.Keep.Add((string)k);
                                        var acts = po["actions"] as JsonObject;
                                        if (acts != null) foreach (string k in acts.Keys) if (acts[k] is string) page.Actions[k] = (string)acts[k];
                                        var mainList = po["main"] as List<object>;
                                        if (mainList != null) { page.Main = new HashSet<string>(); foreach (object k in mainList) if (k is string) page.Main.Add((string)k); }
                                        var upper = po["upper"] as List<object>;
                                        if (upper != null) foreach (object k in upper) if (k is string) page.Upper.Add((string)k);
                                        var sels = po["selectors"] as JsonObject;
                                        if (sels != null)
                                            foreach (string circle in sels.Keys)
                                            {
                                                var lst = new List<string>();
                                                var arr = sels[circle] as List<object>;
                                                if (arr != null) foreach (object k in arr) if (k is string) lst.Add((string)k);
                                                page.Selectors[circle] = lst;
                                            }
                                        var moves = po["moves"] as List<object>;
                                        if (moves != null)
                                            foreach (object c in moves)
                                            {
                                                var mo = c as JsonObject;
                                                if (mo == null || !(mo["name"] is string)) continue;
                                                page.Moves.Add(new PageCopy { Name = (string)mo["name"], Dx = ToF(mo["dx"]), Dy = ToF(mo["dy"]), Sx = ToScale(mo["sx"]), Sy = ToScale(mo["sy"]) });
                                            }
                                        var copies = po["copies"] as List<object>;
                                        if (copies != null)
                                            foreach (object c in copies)
                                            {
                                                var co = c as JsonObject;
                                                if (co == null || !(co["from"] is string) || !(co["name"] is string)) continue;
                                                page.Copies.Add(new PageCopy { From = (string)co["from"], Name = (string)co["name"], Dx = ToF(co["dx"]), Dy = ToF(co["dy"]), Sx = ToScale(co["sx"]), Sy = ToScale(co["sy"]) });
                                            }
                                        mod.DiaryPages.Add(page);
                                    }
                                }
                            }
                        }
                        catch (Exception e) { Log("ERROR reading " + manifest + ": " + e.Message); }
                    }
                    allMods.Add(mod);
                    Log("Loaded mod '" + mod.Name + "' (" + name + "), cages: " + mod.Cages.Count);
                }
            }
            catch (Exception e)
            {
                Log("ERROR during init: " + e);
            }
        }

        // ------------------------------------------------------------------ main.Awake

        /// <summary>Called from MenuController.startNewGame: the new save uses the mods ticked on the MODS page.</summary>
        public static void OnStartNewGame(object menuController)
        {
            EnsureInit();
            ModState.SaveMods = new List<string>(ModState.Selected);
            ModState.Write();
            Log("New game with mods: " + (ModState.SaveMods.Count == 0 ? "(none, original game)" : string.Join(", ", ModState.SaveMods.ToArray())));
        }

        static void SetActive(List<ModInfo> list)
        {
            mods = list;
            cache.Clear();
        }

        public static void OnMainAwake(object mainInstance)
        {
            EnsureInit();
            ModState.Load(allMods);
            if (GameObject.Find("Game") != null)
            {
                var active = new List<ModInfo>();
                foreach (var m in allMods) if (ModState.SaveMods.Contains(m.Folder)) active.Add(m);
                SetActive(active);
            }
            else
            {
                SetActive(new List<ModInfo>()); // menus always show the original game
                try { ModMenu.Build(); } catch (Exception e) { Log("ERROR building MODS menu: " + e); }
            }
            Log("main.Awake (" + (GameObject.Find("Game") != null ? "game" : "menu") + "): " + mods.Count + " of " + allMods.Count + " mod(s) active.");
            if (Verbose && GameObject.Find("Game") != null && mods.Count > 0 && GameObject.Find("DNFTMModDebugKeys") == null)
            {
                var keys = new GameObject("DNFTMModDebugKeys");
                UnityEngine.Object.DontDestroyOnLoad(keys);
                keys.AddComponent<ModDebugKeys>().Cages = ActiveCageIds();
            }
            foreach (var mod in mods)
            {
                foreach (var tpl in mod.SceneTemplates)
                {
                    try { BuildSceneTemplate(tpl); }
                    catch (Exception e) { Log("ERROR building scene template 'Story" + tpl.Id + "': " + e); }
                }
                foreach (var kv in mod.CameraEffects)
                {
                    try { BuildCameraEffect(kv.Key, kv.Value); }
                    catch (Exception e) { Log("ERROR building camera effect for '" + kv.Key + "': " + e); }
                }
                foreach (var page in mod.DiaryPages)
                {
                    try { BuildDiaryPage(page); }
                    catch (Exception e) { Log("ERROR building diary page for '" + page.Story + "': " + e); }
                }
                foreach (var prize in mod.Prizes)
                {
                    try { BuildPrize(mod, prize); }
                    catch (Exception e) { Log("ERROR building prize '" + prize.Id + "': " + e); }
                }
            }
        }

        /// <summary>
        /// Adds Story&lt;id&gt; under Stories/Scenaries. Runs in main.Awake, before main.Start caches
        /// and hides every Scenaries child, so the game treats it like a built-in template.
        /// </summary>
        static void BuildSceneTemplate(SceneTemplate tpl)
        {
            GameObject stories = GameObject.Find("Stories");
            if (stories == null) return; // not the game scene
            Transform scenaries = stories.transform.Find("Scenaries");
            if (scenaries == null) { Log("Stories/Scenaries not found; skipping template " + tpl.Id); return; }
            if (scenaries.Find("Story" + tpl.Id) != null) return;
            Transform source = scenaries.Find("Story" + tpl.CloneFrom);
            if (source == null) { Log("Template 'Story" + tpl.CloneFrom + "' not found; cannot build Story" + tpl.Id); return; }

            var clone = (GameObject)UnityEngine.Object.Instantiate(source.gameObject);
            clone.name = "Story" + tpl.Id;
            clone.transform.SetParent(scenaries, false);
            clone.transform.localPosition = source.localPosition;
            clone.transform.localRotation = source.localRotation;
            clone.transform.localScale = source.localScale;
            clone.SetActive(source.gameObject.activeSelf);

            int removed = 0;
            if (tpl.KeepCameras > 0)
            {
                var extra = new List<GameObject>();
                for (int i = tpl.KeepCameras; i < clone.transform.childCount; i++) extra.Add(clone.transform.GetChild(i).gameObject);
                foreach (var go in extra) { UnityEngine.Object.DestroyImmediate(go); removed++; }
            }
            // The monitor tells cameras apart by GameObject name (ledInterface.OnMouseOver, selectedCameraInterface
            // .show/interchange): two mod cages cloned from the same template had equal camera names, so right-clicking
            // one while the other was the main view swapped/closed it instead of opening the thumbnail (0.5.7).
            // Keep the last character: the game reads it as the camera letter (A/B).
            for (int i = 0; i < clone.transform.childCount; i++)
            {
                Transform cam = clone.transform.GetChild(i);
                cam.name = "mod" + tpl.Id + "_" + cam.name;
            }
            var artCams = tpl.Art != null ? tpl.Art["cameras"] as List<object> : null;
            if (artCams != null)
            {
                for (int i = 0; i < artCams.Count && i < clone.transform.childCount; i++)
                {
                    var camDef = artCams[i] as JsonObject;
                    if (camDef == null) continue;
                    try { ModArt.BuildCamera(clone.transform.GetChild(i), camDef, tpl.ModDir, tpl.Id, i); }
                    catch (Exception e) { Log("ERROR building custom art for Story" + tpl.Id + " camera " + (i + 1) + ": " + e); }
                }
            }
            Log("Built scene template 'Story" + tpl.Id + "' from 'Story" + tpl.CloneFrom + "' (" + clone.transform.childCount + " camera(s), removed " + removed + ").");
        }

        /// <summary>
        /// Gives a cage a fixed camera look by copying storyEffects/&lt;cloneFrom&gt; to storyEffects/&lt;story&gt;.
        /// Without one, the game picks a random effect per new game (some are black and white).
        /// </summary>
        static void BuildCameraEffect(string story, string cloneFrom)
        {
            GameObject effects = GameObject.Find("storyEffects");
            if (effects == null) return;
            if (effects.transform.Find(story) != null) return;
            Transform source = effects.transform.Find(cloneFrom);
            if (source == null) { Log("Camera effect 'storyEffects/" + cloneFrom + "' not found."); return; }
            var clone = (GameObject)UnityEngine.Object.Instantiate(source.gameObject);
            clone.name = story;
            clone.transform.SetParent(effects.transform, false);
            clone.transform.localPosition = source.localPosition;
            clone.SetActive(source.gameObject.activeSelf);
            Log("Built camera effect 'storyEffects/" + story + "' from '" + cloneFrom + "'.");
        }

        const string DiaryRoot = "diaryObject/diaryStory";

        /// <summary>Clones diary&lt;cloneFrom&gt; into diary&lt;story&gt; inside the game scene (only in the scene that has the diary).</summary>
        static void BuildDiaryPage(DiaryPage page)
        {
            GameObject game = GameObject.Find("Game");
            if (game == null) return; // menu scenes have no diary
            Transform story = game.transform.Find(DiaryRoot);
            if (story == null) { Log("Diary container not found; skipping page for " + page.Story); return; }
            if (story.Find("diary" + page.Story) != null) return; // already built in this scene

            Transform source = story.Find("diary" + page.CloneFrom);
            if (source == null) { Log("Diary page 'diary" + page.CloneFrom + "' not found; cannot build page for " + page.Story); return; }

            var clone = (GameObject)UnityEngine.Object.Instantiate(source.gameObject);
            clone.name = "diary" + page.Story;
            clone.transform.SetParent(story, false);
            clone.transform.localPosition = source.localPosition;
            clone.transform.localRotation = source.localRotation;
            clone.transform.localScale = source.localScale;
            clone.SetActive(source.gameObject.activeSelf);

            // extra parts copied from the page itself (a second box with its word slots), before slots are renamed
            var copied = new HashSet<string>();
            foreach (var cp in page.Copies)
            {
                Transform src = clone.transform.Find(cp.From);
                if (src == null) { Log("WARNING: diary copy source '" + cp.From + "' not found on diary" + page.CloneFrom + "."); continue; }
                // instantiate under the page: keywordInterface.Awake looks at transform.parent
                var dup = (GameObject)UnityEngine.Object.Instantiate(src.gameObject, clone.transform, false);
                dup.name = cp.Name;
                dup.transform.localRotation = src.localRotation;
                dup.transform.localScale = Vector3.Scale(src.localScale, new Vector3(cp.Sx, cp.Sy, 1f));
                dup.transform.localPosition = src.localPosition + new Vector3(cp.Dx, cp.Dy, 0f);
                dup.SetActive(src.gameObject.activeSelf);
                copied.Add(cp.Name);
            }

            // moved parts of the source page (all children with the name; the sayCheese page has duplicate names)
            foreach (var mv in page.Moves)
            {
                int n = 0;
                foreach (Transform ch in clone.transform)
                    if (ch.name == mv.Name)
                    {
                        ch.localPosition += new Vector3(mv.Dx, mv.Dy, 0f);
                        if (mv.Sx != 1f || mv.Sy != 1f) ch.localScale = Vector3.Scale(ch.localScale, new Vector3(mv.Sx, mv.Sy, 1f));
                        n++;
                    }
                if (n == 0) Log("WARNING: diary move target '" + mv.Name + "' not found on diary" + page.CloneFrom + ".");
            }

            // deduction selectors: keep the "?" object and the remove-icon position, re-point the option buttons
            foreach (var sel in page.Selectors)
            {
                Transform selector = clone.transform.Find(sel.Key + "Selector");
                if (selector == null) { Log("WARNING: diary selector '" + sel.Key + "Selector' not found on diary" + page.CloneFrom + "."); continue; }
                copied.Add(selector.name);
                copied.Add(sel.Key + "iconPosition");
                int n = 0;
                foreach (Transform opt in selector)
                {
                    var kd = opt.GetComponent<keywordInterfaceDiary>();
                    if (kd == null) continue;
                    if (n < sel.Value.Count) { kd.id = sel.Value[n]; kd.zone = sel.Key; }
                    n++;
                }
                if (n != sel.Value.Count) Log("WARNING: selector " + sel.Key + " has " + n + " option buttons but " + sel.Value.Count + " keywords were given.");
            }

            // slot id on the source page -> new keyword id
            var slotToWord = new Dictionary<string, string>();
            foreach (var kv in page.Words) slotToWord["diaryWord" + kv.Value] = "diaryWord" + kv.Key;

            // Phone/chat buttons: copy the source page's button for each listed keyword, placed beside its slot with
            // the same offset as on the source page. keywordInterface finds it by name ("<word object name>Action").
            var made = new HashSet<string>();
            foreach (var kv in page.Actions)
            {
                string slot;
                if (!page.Words.TryGetValue(kv.Key, out slot)) { Log("WARNING: diary action for '" + kv.Key + "' has no word slot."); continue; }
                Transform srcAction = clone.transform.Find("diaryWord" + kv.Value + "Action"), srcWord = clone.transform.Find("diaryWord" + kv.Value);
                Transform target = clone.transform.Find("diaryWord" + slot);
                if (srcAction == null || srcWord == null || target == null) { Log("WARNING: diary action source 'diaryWord" + kv.Value + "Action' not found on diary" + page.CloneFrom + "."); continue; }
                var btn = (GameObject)UnityEngine.Object.Instantiate(srcAction.gameObject);
                btn.name = "diaryWord" + kv.Key + "Action";
                btn.transform.SetParent(clone.transform, false);
                btn.transform.localRotation = srcAction.localRotation;
                btn.transform.localScale = srcAction.localScale;
                btn.transform.localPosition = target.localPosition + (srcAction.localPosition - srcWord.localPosition);
                btn.SetActive(srcAction.gameObject.activeSelf);
                made.Add(btn.name);
            }

            var children = new List<Transform>();
            foreach (Transform child in clone.transform) if (!made.Contains(child.name)) children.Add(child);
            int renamed = 0, removed = 0;
            foreach (Transform child in children)
            {
                string newName;
                if (slotToWord.TryGetValue(child.name, out newName)) { child.name = newName; renamed++; SetMain(child, newName.Substring("diaryWord".Length), page); }
                else if (!page.Keep.Contains(child.name) && !copied.Contains(child.name))
                {
                    // Hide and rename instead of destroying: components on the page (e.g. diaryCircleFeedback)
                    // keep references to sibling objects and throw if those are destroyed.
                    child.gameObject.SetActive(false);
                    child.name = "_unused_" + child.name;
                    removed++;
                }
            }
            Log("Built diary page 'diary" + page.Story + "' from 'diary" + page.CloneFrom + "': " + renamed + " word slot(s), " + made.Count + " button(s), hid " + removed + " unused child(ren).");
            if (renamed != page.Words.Count) Log("WARNING: some word slots were not found on diary" + page.CloneFrom + "; check 'words' in mod.json.");
        }

        /// <summary>Main words can be chosen in calls, chats and Club missions. relatedCircle is cleared so the game
        /// does not add the "remove" cross of the source page's word selectors.</summary>
        static void SetMain(Transform slot, string keyword, DiaryPage page)
        {
            if (page.Main == null) return;
            var kw = slot.GetComponent<keywordInterface>();
            if (kw == null) return;
            kw.isMain = page.Main.Contains(keyword) || page.Main.Contains("*");
            kw.stillLowercase = !page.Upper.Contains(keyword);
            kw.relatedCircle = string.Empty;
            // a deduction answer keeps its circle: the game puts the "remove" cross next to it so the player can choose again
            foreach (var sel in page.Selectors) if (sel.Value.Contains(keyword)) { kw.relatedCircle = sel.Key; kw.isMain = true; }
        }

        internal static List<string> ActiveCageIds()
        {
            var ids = new List<string>();
            foreach (var mod in mods) foreach (var c in mod.Cages) ids.Add(c.Id);
            return ids;
        }

        // ------------------------------------------------------------------ images (main.loadImage, newspaper)

        /// <summary>
        /// Replaces Resources.Load(path) in main.loadImage and NewspapperController.generateNews.
        /// A path containing "mods/&lt;ModFolder&gt;/&lt;file&gt;" (also after a prefix the game adds, such as
        /// "endingsImg/" or "door/") is read from Mods/&lt;ModFolder&gt;/&lt;file&gt;.png; anything else is the game's own resource.
        /// Every browser image (news, wiki, Metayou, map, web pages), chat avatar, ending picture, door guest
        /// and newspaper photo goes through here, so mods can use their own PNG files.
        /// </summary>
        static readonly HashSet<string> loggedImages = new HashSet<string>();

        /// <summary>True when version a (e.g. "0.5.2") is lower than version b.</summary>
        internal static bool OlderThan(string a, string b)
        {
            string[] x = a.Split('.'), y = b.Split('.');
            for (int i = 0; i < Math.Max(x.Length, y.Length); i++)
            {
                int p = 0, q = 0;
                if (i < x.Length) int.TryParse(x[i], out p);
                if (i < y.Length) int.TryParse(y[i], out q);
                if (p != q) return p < q;
            }
            return false;
        }

        internal static List<string> ModsNeedingNewerLoader()
        {
            var list = new List<string>();
            foreach (var m in allMods) if (!string.IsNullOrEmpty(m.MinLoader) && OlderThan(Version, m.MinLoader)) list.Add(m.Name + " (" + m.MinLoader + ")");
            return list;
        }

        static Transform FindSceneObject(string name)
        {
            var go = GameObject.Find(name);
            if (go != null) return go.transform;
            foreach (var t in Resources.FindObjectsOfTypeAll<Transform>())
                if (t.name == name && t.gameObject.scene.IsValid()) return t;
            return null;
        }

        static void BuildPrize(ModInfo mod, ModPrize p)
        {
            if (GameObject.Find("Game") == null) return;
            Transform items = FindSceneObject("prizeHolderItems");
            if (items == null) { Log("WARNING: prizeHolderItems not found; prize '" + p.Id + "' not built."); return; }
            if (items.Find(p.Id) != null) return;
            Transform tpl = items.Find(p.Template);
            if (tpl == null) { Log("WARNING: prize template '" + p.Template + "' not found; prize '" + p.Id + "' not built."); return; }
            var go = (GameObject)UnityEngine.Object.Instantiate(tpl.gameObject, items, false);
            go.name = p.Id;
            go.transform.localPosition = new Vector3(p.X, p.Y, p.Z);
            Sprite img = ModArt.ModSprite(mod.Dir, p.Image, new Vector2(0.5f, 0.5f));
            Sprite sel = string.IsNullOrEmpty(p.Selected) ? img : ModArt.ModSprite(mod.Dir, p.Selected, new Vector2(0.5f, 0.5f));
            Sprite pop = ModArt.ModSprite(mod.Dir, p.Popup, Vector2.zero);
            var sr = go.GetComponent<SpriteRenderer>();
            if (sr != null && sel != null) sr.sprite = sel;
            Transform bg = go.transform.Find("prizeBg");
            if (bg != null && bg.GetComponent<SpriteRenderer>() != null && img != null) bg.GetComponent<SpriteRenderer>().sprite = img;
            var col = go.GetComponent<BoxCollider>();
            if (col != null && sel != null) { col.size = new Vector3(sel.bounds.size.x, sel.bounds.size.y, col.size.z); col.center = Vector3.zero; }
            int set = 0;
            foreach (var mb in go.GetComponents<MonoBehaviour>())
            {
                if (mb == null) continue;
                var f = mb.GetType().GetField("popupBackground");
                if (f != null && pop != null) { f.SetValue(mb, pop); set++; }
            }
            // The game finds shelf objects with GameObject.Find, which skips inactive objects; it caches the original
            // prizes in main.objects while they are still active (prizeController.Start). Register ours the same way.
            bool cached = false;
            try
            {
                var mainType = Type.GetType("main, Assembly-UnityScript");
                var setObject = mainType == null ? null : mainType.GetMethod("setObject", new[] { typeof(string), typeof(GameObject) });
                if (setObject != null) { setObject.Invoke(null, new object[] { "prizeHolderItems/" + p.Id, go }); cached = true; }
            }
            catch (Exception e) { Log("WARNING: cannot register prize object '" + p.Id + "': " + e.Message); }
            if (!cached) Log("WARNING: prize object '" + p.Id + "' not registered; the game may not find it.");
            go.SetActive(false);
            Log("Prize '" + p.Id + "' on the shelf at (" + p.X + ", " + p.Y + "), copied from '" + p.Template + "'" + (set == 0 ? " (WARNING: popup picture not set)" : "") + ".");
        }

        public static UnityEngine.Object LoadImageResource(string path)
        {
            if (path != null)
            {
                int i = path.IndexOf("mods/", StringComparison.OrdinalIgnoreCase);
                if (i >= 0)
                {
                    EnsureInit();
                    var tex = modsRoot == null ? null : ModArt.FindModImage(modsRoot, path.Substring(i + 5));
                    if (tex != null)
                    {
                        if (loggedImages.Add(path)) Log("Image from Mods: " + path + " (" + tex.width + "x" + tex.height + ")");
                        return tex;
                    }
                    Log("WARNING: image not found in Mods: " + path);
                }
            }
            return Resources.Load(path);
        }

        // ------------------------------------------------------------------ main.getResourceFile

        public static bool HandlesResourceFile(string name)
        {
            if (inOriginal || name == null) return false;
            EnsureInit();
            if (mods.Count == 0) return false;
            string key = Normalize(name);
            if (key == "genericconfig.json" && AnyCages()) return true;
            foreach (var mod in mods)
            {
                if (FindFile(mod, "files", key) != null || FindFile(mod, "merge", key) != null) return true;
            }
            return false;
        }

        public static string GetResourceFile(string name)
        {
            string key = Normalize(name);
            string cached;
            if (cache.TryGetValue(key, out cached)) return cached;

            string result = null;
            try
            {
                // 1) Last mod (alphabetical) that ships a full file wins.
                for (int m = mods.Count - 1; m >= 0 && result == null; m--)
                {
                    string path = FindFile(mods[m], "files", key);
                    if (path != null)
                    {
                        result = File.ReadAllText(path);
                        Log("files: " + name + " <- " + mods[m].Name);
                    }
                }
                // 2) Otherwise start from the game's own file.
                if (result == null) result = CallOriginal(name);

                // 3) Apply merge patches in mod order.
                object tree = null;
                foreach (var mod in mods)
                {
                    string path = FindFile(mod, "merge", key);
                    if (path == null) continue;
                    if (tree == null) tree = MiniJson.Parse(result);
                    tree = MiniJson.Merge(tree, MiniJson.Parse(File.ReadAllText(path)));
                    Log("merge: " + name + " <- " + mod.Name);
                }
                // 4) Register new cages in every camera path of genericConfig.
                if (key == "genericconfig.json" && AnyCages())
                {
                    if (tree == null) tree = MiniJson.Parse(result);
                    RegisterCages(tree as JsonObject);
                }
                if (tree != null) result = MiniJson.Serialize(tree);
            }
            catch (Exception e)
            {
                Log("ERROR building " + name + ", falling back to game file: " + e);
                result = CallOriginal(name);
            }
            cache[key] = result;
            return result;
        }

        static string CallOriginal(string name)
        {
            inOriginal = true;
            try { return main.getResourceFile(name); }
            finally { inOriginal = false; }
        }

        static void RegisterCages(JsonObject config)
        {
            if (config == null) return;
            var pathObjects = new List<JsonObject>();
            var paths = config["paths"] as List<object>;
            if (paths != null) foreach (object p in paths) if (p is JsonObject) pathObjects.Add((JsonObject)p);
            if (config["demoPath"] is JsonObject) pathObjects.Add((JsonObject)config["demoPath"]);

            foreach (var mod in mods)
            {
                foreach (var cage in mod.Cages)
                {
                    foreach (var path in pathObjects)
                    {
                        var cams = path["cams"] as List<object>;
                        if (cams == null || cams.Contains(cage.Id)) continue;
                        int at = Math.Max(0, Math.Min(cage.InsertAt, cams.Count));
                        cams.Insert(at, cage.Id);
                    }
                    Log("Registered cage '" + cage.Id + "' at position " + cage.InsertAt + " in " + pathObjects.Count + " path(s).");
                }
            }
        }

        // ------------------------------------------------------------------ storyController.getStoryMetadata / getStoryNews

        public static bool HandlesStory(string id)
        {
            if (id == null) return false;
            EnsureInit();
            string key = Normalize(id + ".json");
            foreach (var mod in mods) if (FindFile(mod, "files", key) != null) return true;
            return false;
        }

        public static object GetStoryMetadata(string id)
        {
            Hashtable h = JSONUtils.ParseJSON(GetResourceFile(id + ".json"));
            return h["metadata"];
        }

        public static object GetStoryNews(string id)
        {
            Hashtable h = JSONUtils.ParseJSON(GetResourceFile(id + ".json"));
            var pre = h["preNews"] as UnityScript.Lang.Array;
            return (pre != null && pre.length != 0) ? (object)pre : null;
        }

        // ------------------------------------------------------------------ helpers

        static bool AnyCages()
        {
            foreach (var m in mods) if (m.Cages.Count > 0) return true;
            return false;
        }

        static string Normalize(string name)
        {
            return name.Replace('\\', '/').TrimStart('/').ToLowerInvariant();
        }

        /// <summary>Case-insensitive lookup of mods/&lt;mod&gt;/&lt;kind&gt;/&lt;key&gt;.</summary>
        static string FindFile(ModInfo mod, string kind, string key)
        {
            string dir = Path.Combine(mod.Dir, kind);
            if (!Directory.Exists(dir)) return null;
            string[] parts = key.Split('/');
            for (int p = 0; p < parts.Length; p++)
            {
                bool last = p == parts.Length - 1;
                string[] entries = last ? Directory.GetFiles(dir) : Directory.GetDirectories(dir);
                string match = null;
                foreach (string e in entries)
                {
                    if (string.Equals(Path.GetFileName(e), parts[p], StringComparison.OrdinalIgnoreCase)) { match = e; break; }
                }
                if (match == null) return null;
                dir = match;
            }
            return dir;
        }

        static string LogPath { get { return modsRoot == null ? null : Path.Combine(modsRoot, "ModLoader.log"); } }

        static void ResetLog()
        {
            try { if (Directory.Exists(modsRoot)) File.WriteAllText(LogPath, string.Empty); } catch { }
        }

        internal static void Log(string msg)
        {
            string line = "[DNFTMModLoader] " + msg;
            try { Debug.Log(line); } catch { }
            try { if (LogPath != null && Directory.Exists(modsRoot)) File.AppendAllText(LogPath, DateTime.Now.ToString("HH:mm:ss ") + msg + Environment.NewLine); } catch { }
        }
    }
}
