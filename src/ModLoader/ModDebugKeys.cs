using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace DNFTMModLoader
{
    /// <summary>
    /// Verbose mode only (Mods/verbose.txt): F8 opens the browser result of the next keyword of the active mod cages,
    /// so mod authors can check web pages, wiki entries, Metayou profiles and maps without collecting the keyword first.
    /// </summary>
    public class ModDebugKeys : MonoBehaviour
    {
        public List<string> Cages = new List<string>();
        readonly List<KeyValuePair<string, Hashtable>> results = new List<KeyValuePair<string, Hashtable>>();
        int next;

        void Load()
        {
            results.Clear();
            foreach (string cage in Cages)
            {
                string json = Hooks.GetResourceFile(cage + ".json");
                if (string.IsNullOrEmpty(json)) continue;
                var data = JSONUtils.ParseJSON(json);
                var kws = data == null ? null : data["keywords"] as Hashtable;
                if (kws == null) continue;
                var names = new List<string>();
                foreach (object k in kws.Keys) names.Add((string)k);
                names.Sort(StringComparer.Ordinal);
                foreach (string k in names)
                {
                    var b = (kws[k] as Hashtable) == null ? null : ((Hashtable)kws[k])["browser"] as Hashtable;
                    var list = b == null ? null : b["data"] as IEnumerable;
                    if (list == null) continue;
                    foreach (object r in list) if (r is Hashtable) results.Add(new KeyValuePair<string, Hashtable>(cage + "/" + k, (Hashtable)r));
                }
            }
            Hooks.Log("DEBUG F8: " + results.Count + " browser result(s) to show.");
        }

        void Update()
        {
            if (Input.GetKeyDown(KeyCode.F9))
            {
                // Unlock the camera recording add-on (as if bought) to test Shock.tv recordings of mod cages.
                var padlock = main.getObject("MonitorRightMenuRecPadlock") as GameObject;
                if (padlock != null) padlock.SetActive(false);
                Hooks.Log("DEBUG F9: recording unlocked (" + (padlock != null) + ").");
            }
            if (!Input.GetKeyDown(KeyCode.F8)) return;
            if (results.Count == 0) Load();
            if (results.Count == 0) return;
            var item = results[next++ % results.Count];
            BrowserController browser = null;
            foreach (var bc in Resources.FindObjectsOfTypeAll<BrowserController>()) if (bc.gameObject.scene.IsValid()) { browser = bc; break; }
            if (browser == null) { Hooks.Log("DEBUG F8: no BrowserController in the scene."); return; }
            for (var t = browser.transform; t != null; t = t.parent) if (!t.gameObject.activeSelf) t.gameObject.SetActive(true);
            // The search screen puts the cage's storyController into the result before opening it (text markup needs it).
            string cageId = item.Key.Substring(0, item.Key.IndexOf('/'));
            foreach (var sc in Resources.FindObjectsOfTypeAll<storyController>())
                if (sc != null && sc.gameObject.scene.IsValid() && sc.getStoryId() == cageId) { item.Value["storyController"] = sc; break; }
            string type = item.Value["type"] as string ?? "new";
            Hooks.Log("DEBUG F8: " + item.Key + " (" + type + ")");
            try
            {
                switch (type)
                {
                    case "web": browser.openWeb(item.Value); break;
                    case "wiki": browser.openWiki(item.Value); break;
                    case "meta": browser.openMetayou(item.Value); break;
                    case "map": browser.openMap(item.Value); break;
                    case "guide": browser.openPhoneGuide(item.Value); break;
                    default: browser.openNew(item.Value); break;
                }
            }
            catch (Exception e) { Hooks.Log("DEBUG F8: " + item.Key + " failed: " + e); }
        }
    }
}
