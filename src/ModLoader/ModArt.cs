using System;
using System.Collections.Generic;
using System.IO;
using UnityEngine;

namespace DNFTMModLoader
{
    /// <summary>One frame-based animation of a custom art object.</summary>
    internal sealed class ModAnimClip
    {
        public string Name;
        public Sprite[] Frames;
        public float Fps = 6f;
        public bool Loop = true;
        public float Duration { get { return Frames.Length / Mathf.Max(0.01f, Fps); } }
    }

    /// <summary>
    /// Plays sprite frames on a custom art object. The game's script runner talks to animationInterface;
    /// the installer redirects animationInterface calls here when this component is present.
    /// Only the registry key is serialized, so copies made by Object.Instantiate (the game clones the
    /// scene template for every cage instance and for recorded videos) find their clips again.
    /// </summary>
    public class ModSpriteAnimator : MonoBehaviour
    {
        public string setKey;

        internal static readonly Dictionary<string, Dictionary<string, ModAnimClip>> Registry = new Dictionary<string, Dictionary<string, ModAnimClip>>();

        string current = string.Empty;
        float time;
        SpriteRenderer sr;
        Animator animator;
        float ownSpeed = 1f;

        Dictionary<string, ModAnimClip> Clips
        {
            get { Dictionary<string, ModAnimClip> c; return setKey != null && Registry.TryGetValue(setKey, out c) ? c : null; }
        }

        void Awake()
        {
            sr = GetComponent<SpriteRenderer>();
            animator = GetComponent<Animator>();
        }

        void Start()
        {
            if (string.IsNullOrEmpty(current) && Clips != null && Clips.ContainsKey("default")) Play("default", 0f);
            if (Hooks.Verbose)
                Hooks.Log("anim start " + name + " key=" + setKey + " clips=" + (Clips != null ? Clips.Count : -1) + " pos=" + transform.position +
                    " layer=" + gameObject.layer + " sprite=" + (sr != null && sr.sprite != null ? sr.sprite.name : "null") +
                    " srEnabled=" + (sr != null && sr.enabled) + " color=" + (sr != null ? sr.color.ToString() : "-") + " scale=" + transform.lossyScale);
        }

        /// <summary>Speed from the (controller-less) Animator so the game's pause logic (speed 0/1) still works.</summary>
        float Speed { get { return (animator != null ? animator.speed : 1f) * ownSpeed; } }

        void Update()
        {
            var c = CurrentClip;
            if (c == null || c.Frames.Length == 0) return;
            time += Time.deltaTime * Speed;
            int frame = Mathf.FloorToInt(time * c.Fps);
            frame = c.Loop ? frame % c.Frames.Length : Mathf.Min(frame, c.Frames.Length - 1);
            if (frame < 0) frame = 0;
            if (sr != null && sr.sprite != c.Frames[frame]) sr.sprite = c.Frames[frame];
        }

        ModAnimClip CurrentClip
        {
            get { var cl = Clips; ModAnimClip c; return cl != null && cl.TryGetValue(current, out c) ? c : null; }
        }

        public bool Has(string anim) { var cl = Clips; return cl != null && cl.ContainsKey(anim); }

        public void Play(string anim, float normalized)
        {
            var cl = Clips;
            ModAnimClip c;
            if (cl == null || !cl.TryGetValue(anim, out c)) { if (anim != "default") Hooks.Log("Custom animation not found: " + anim + " -> " + name); return; }
            // 0.5.8: switching between looping clips of the same length and speed (a walk cycle and its smaller
            // copies, or the same clip again) keeps the step phase. Restarting at frame 0 on every switch froze the
            // walk when a cage swaps sizes several times a second.
            var prev = CurrentClip;
            bool keepPhase = normalized <= 0f && prev != null && prev.Loop && c.Loop && prev.Frames.Length == c.Frames.Length
                             && Mathf.Approximately(prev.Fps, c.Fps);
            current = anim;
            if (keepPhase) time = c.Duration > 0f ? time % c.Duration : 0f;
            else time = Mathf.Clamp01(normalized) * c.Duration;
            if (sr == null) sr = GetComponent<SpriteRenderer>();
            if (sr != null && c.Frames.Length > 0) sr.sprite = c.Frames[Mathf.Min(c.Frames.Length - 1, Mathf.FloorToInt(time * c.Fps))];
        }

        public float Normalized { get { var c = CurrentClip; return c == null ? 1f : time / Mathf.Max(0.0001f, c.Duration); } }
        public bool IsLooping { get { var c = CurrentClip; return c != null && c.Loop; } }
        public string Current { get { return current; } }
        public float OwnSpeed { get { return ownSpeed; } set { ownSpeed = value; } }
    }

    /// <summary>Builds custom art objects inside a scene template camera node.</summary>
    internal static class ModArt
    {
        static readonly Dictionary<string, Texture2D> textures = new Dictionary<string, Texture2D>(StringComparer.OrdinalIgnoreCase);
        static readonly Dictionary<string, Sprite> sprites = new Dictionary<string, Sprite>(StringComparer.Ordinal);

        const float PixelsPerUnit = 100f;
        const float OriginX = 126f, OriginY = 87f; // TemplateScriptController.calculatePosition

        static Texture2D LoadTexture(string modDir, string rel)
        {
            string path = Path.Combine(modDir, rel.Replace('/', Path.DirectorySeparatorChar));
            Texture2D tex;
            if (textures.TryGetValue(path, out tex)) return tex;
            if (!File.Exists(path)) { Hooks.Log("ERROR: art file not found: " + path); return null; }
            tex = new Texture2D(2, 2, TextureFormat.RGBA32, false);
            if (!tex.LoadImage(File.ReadAllBytes(path))) { Hooks.Log("ERROR: cannot decode image " + path); return null; }
            tex.filterMode = FilterMode.Point;
            tex.wrapMode = TextureWrapMode.Clamp;
            tex.name = rel;
            textures[path] = tex;
            return tex;
        }

        /// <summary>
        /// A PNG named by a game image path below Mods: "MyMod/news/photo" -> Mods/MyMod/news/photo.png.
        /// The extension is optional; the game's door code asks for "&lt;image&gt;3" (second frame), which falls back
        /// to "&lt;image&gt;" when no separate file exists. Returns null when there is no such file.
        /// </summary>
        internal static Texture2D FindModImage(string modsRoot, string rel)
        {
            if (string.IsNullOrEmpty(rel) || rel.Contains("..")) return null;
            var tries = new List<string> { rel, rel + ".png" };
            if (rel.EndsWith("3")) { string b = rel.Substring(0, rel.Length - 1); tries.Add(b); tries.Add(b + ".png"); }
            foreach (string t in tries)
            {
                string full = Path.Combine(modsRoot, t.Replace('/', Path.DirectorySeparatorChar));
                if (t.EndsWith(".png", StringComparison.OrdinalIgnoreCase) && File.Exists(full)) return LoadTexture(modsRoot, t);
            }
            return null;
        }

        static Material outlineMat;

        /// <summary>The yellow outline material of the game's clickable items: taken from the template being built
        /// (its original objects are only deactivated) or, failing that, from any loaded OnMouseOutline.</summary>
        static Material OutlineMaterial(Transform cam)
        {
            if (outlineMat != null) return outlineMat;
            // The most used outline material among all the game's clickable items is the normal yellow one
            // (a few objects use special ones, e.g. Red Fred's demon camera).
            var count = new Dictionary<Material, int>();
            foreach (var o in Resources.FindObjectsOfTypeAll<OnMouseOutline>())
            {
                if (o == null || o.outline == null) continue;
                int n; count.TryGetValue(o.outline, out n); count[o.outline] = n + 1;
            }
            int best = 0;
            foreach (var kv in count)
            {
                if (Hooks.Verbose) Hooks.Log("outline material " + kv.Key.name + " (" + kv.Key.shader.name + "): " + kv.Value);
                if (kv.Value > best) { best = kv.Value; outlineMat = kv.Key; }
            }
            if (outlineMat != null) Hooks.Log("Outline material for clickable objects: " + outlineMat.name);
            return outlineMat;
        }

        static Vector2 PivotOf(string pivot)
        {
            switch (pivot)
            {
                case "center": return new Vector2(0.5f, 0.5f);
                case "top": return new Vector2(0.5f, 1f);
                case "bottomLeft": return new Vector2(0f, 0f);
                default: return new Vector2(0.5f, 0f); // bottom centre = feet, like the game's characters
            }
        }

        /// <summary>A whole PNG of a mod (path relative to the mod folder, ".png" optional) as a sprite.</summary>
        internal static Sprite ModSprite(string modDir, string rel, Vector2 pivot)
        {
            if (string.IsNullOrEmpty(rel)) return null;
            return LoadSprite(modDir, rel.EndsWith(".png", StringComparison.OrdinalIgnoreCase) ? rel : rel + ".png", pivot, -1, 0, 0);
        }

        /// <summary>A sprite from a whole image, or from cell <paramref name="index"/> of a sprite sheet.</summary>
        static Sprite LoadSprite(string modDir, string rel, Vector2 pivot, int index, int cellW, int cellH)
        {
            string key = modDir + "|" + rel + "|" + index + "|" + cellW + "x" + cellH + "|" + pivot.x + "," + pivot.y;
            Sprite s;
            if (sprites.TryGetValue(key, out s)) return s;
            var tex = LoadTexture(modDir, rel);
            if (tex == null) return null;
            Rect r;
            if (index < 0 || cellW <= 0 || cellH <= 0) r = new Rect(0, 0, tex.width, tex.height);
            else
            {
                int cols = Mathf.Max(1, tex.width / cellW);
                int cx = index % cols, cy = index / cols;
                // sheet cells are counted from the top-left; texture coordinates start bottom-left
                r = new Rect(cx * cellW, tex.height - (cy + 1) * cellH, cellW, cellH);
                if (r.y < 0) { Hooks.Log("ERROR: frame " + index + " is outside sheet " + rel); return null; }
            }
            s = Sprite.Create(tex, r, pivot, PixelsPerUnit, 0, SpriteMeshType.FullRect);
            s.name = rel + (index >= 0 ? "#" + index : "");
            sprites[key] = s;
            return s;
        }

        static float Num(object v, float def)
        {
            var n = v as JsonNumber;
            float f;
            if (n != null && float.TryParse(n.Text, System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out f)) return f;
            if (v is bool) return (bool)v ? 1 : 0;
            return def;
        }

        static GameObject[] Append(GameObject[] arr, GameObject go)
        {
            var list = new List<GameObject>(arr ?? new GameObject[0]);
            list.Add(go);
            return list.ToArray();
        }

        /// <summary>Applies one camera entry of a template's "art" block to the camera node.</summary>
        public static void BuildCamera(Transform cam, JsonObject def, string modDir, string templateId, int camIndex)
        {
            // Rendering settings copied from the template so custom sprites go through the same camera/effects.
            SpriteRenderer reference = null;
            foreach (var r in cam.GetComponentsInChildren<SpriteRenderer>(true)) { reference = r; break; }

            if (def["clear"] is bool && (bool)def["clear"])
            {
                var kids = new List<Transform>();
                foreach (Transform c in cam) kids.Add(c);
                foreach (var c in kids) { c.gameObject.SetActive(false); c.name = "_unused_" + c.name; }
            }

            var objects = def["objects"] as List<object>;
            if (objects == null) return;
            var light = cam.GetComponent<LightController>();
            int built = 0;
            foreach (object o in objects)
            {
                var od = o as JsonObject;
                if (od == null || !(od["name"] is string)) continue;
                string name = (string)od["name"];
                var pivot = PivotOf(od["pivot"] as string);
                var sheet = od["sheet"] as JsonObject;
                string sheetImg = sheet != null ? sheet["image"] as string : null;
                int cellW = sheet != null ? (int)Num(sheet["w"], 0) : 0, cellH = sheet != null ? (int)Num(sheet["h"], 0) : 0;

                Func<object, Sprite> frameSprite = f =>
                {
                    if (f is string) return LoadSprite(modDir, (string)f, pivot, -1, 0, 0);
                    if (f is JsonNumber && sheetImg != null) return LoadSprite(modDir, sheetImg, pivot, (int)Num(f, 0), cellW, cellH);
                    return null;
                };

                var go = new GameObject(name);
                go.layer = cam.gameObject.layer;
                go.transform.SetParent(cam, false);
                go.transform.localPosition = new Vector3((Num(od["x"], OriginX) - OriginX) / PixelsPerUnit, (Num(od["y"], OriginY) - OriginY) / PixelsPerUnit, Num(od["z"], -10));
                if (od["flip"] is bool && (bool)od["flip"]) go.transform.localScale = new Vector3(-1, 1, 1);
                var sr = go.AddComponent<SpriteRenderer>();
                if (reference != null)
                {
                    sr.sharedMaterial = reference.sharedMaterial;
                    sr.sortingLayerID = reference.sortingLayerID;
                }
                if (od["alpha"] is JsonNumber) { var col = sr.color; col.a = Num(od["alpha"], 1); sr.color = col; }

                if (od["image"] is string) sr.sprite = frameSprite(od["image"]);

                var anims = od["animations"] as JsonObject;
                if (anims != null && anims.Keys.Count > 0)
                {
                    string key = templateId + "/" + camIndex + "/" + name;
                    var clips = new Dictionary<string, ModAnimClip>();
                    foreach (string an in anims.Keys)
                    {
                        var ad = anims[an] as JsonObject;
                        if (ad == null) continue;
                        var frames = new List<Sprite>();
                        var fl = ad["frames"] as List<object>;
                        if (fl != null) foreach (object f in fl) { var s = frameSprite(f); if (s != null) frames.Add(s); }
                        if (frames.Count == 0) { Hooks.Log("WARNING: animation '" + an + "' of " + name + " has no frames."); continue; }
                        clips[an] = new ModAnimClip { Name = an, Frames = frames.ToArray(), Fps = Num(ad["fps"], 6), Loop = !(ad["loop"] is bool) || (bool)ad["loop"] };
                    }
                    ModSpriteAnimator.Registry[key] = clips;
                    if (sr.sprite == null)
                    {
                        ModAnimClip first;
                        if (clips.TryGetValue("default", out first) || (clips.Count > 0 && (first = new List<ModAnimClip>(clips.Values)[0]) != null)) sr.sprite = first.Frames[0];
                    }
                    // The game's script runner expects an Animator and an animationInterface on animated objects.
                    go.AddComponent<Animator>();
                    go.AddComponent<animationInterface>();
                    var msa = go.AddComponent<ModSpriteAnimator>();
                    msa.setKey = key;
                }

                // Clickable object: the player clicks it in the camera view to collect a keyword (like the game's own items).
                if (od["keyword"] is string && !string.IsNullOrEmpty((string)od["keyword"]))
                {
                    // PolygonCollider2D (not BoxCollider2D): the script's "disable"/"enable" actions switch Collider and
                    // PolygonCollider2D only, so a hidden object must not stay clickable.
                    var col = go.AddComponent<PolygonCollider2D>();
                    if (sr.sprite != null)
                    {
                        var b = sr.sprite.bounds;
                        col.pathCount = 1;
                        col.SetPath(0, new[] { new Vector2(b.min.x, b.min.y), new Vector2(b.max.x, b.min.y), new Vector2(b.max.x, b.max.y), new Vector2(b.min.x, b.max.y) });
                    }
                    // Yellow outline on mouse over, like the game's own clickable items (StoryItemInterface.Start picks it up).
                    var hl = go.AddComponent<OnMouseOutline>();
                    hl.outline = OutlineMaterial(cam);
                    if (hl.outline == null) Hooks.Log("WARNING: no outline material found for " + name + "; it will be clickable without the yellow outline.");
                    var item = go.AddComponent<StoryItemInterface>();
                    item.wordId = (string)od["keyword"];
                    if (Hooks.Verbose) go.AddComponent<ModClickDebug>();
                }

                string role = od["role"] as string;
                if (light != null && role != null)
                {
                    switch (role)
                    {
                        case "day": light.dayLayers = Append(light.dayLayers, go); break;
                        case "night": light.nightLayers = Append(light.nightLayers, go); break;
                        case "tint": light.nightLayersTint = Append(light.nightLayersTint, go); break;
                        case "nightVision": light.nightVisionLayers = Append(light.nightVisionLayers, go); break;
                        case "nightVisionOnly":
                            // Hidden until night vision is on: the game restores the alpha it stored when vision is enabled.
                            light.nightVisionVisibleLayers = Append(light.nightVisionVisibleLayers, go);
                            var c0 = sr.color; c0.a = 0f; sr.color = c0;
                            break;
                    }
                }
                // Objects stay active in the template: the game assigns each cage's render layer to the
                // active hierarchy when it clones the template. Use a "disable" action in the start scene to hide.
                if (od["active"] is bool && !(bool)od["active"]) Hooks.Log("NOTE: '" + name + "' has active:false; hide it with a disable action in the start scene instead.");
                built++;
            }
            Hooks.Log("Custom art for Story" + templateId + " camera " + (camIndex + 1) + ": " + built + " object(s).");
        }
    }

    /// <summary>animationInterface redirection targets (see installer).</summary>
    public static class AnimHooks
    {
        static ModSpriteAnimator Get(Component ai) { return ai == null ? null : ai.GetComponent<ModSpriteAnimator>(); }

        public static bool IsMod(Component ai) { return Get(ai) != null; }

        public static void Play1(Component ai, string anim)
        {
            var m = Get(ai);
            // The game starts animations at their end when time runs very fast (Time.timeScale > 32).
            m.Play(anim, Time.timeScale > 32f && anim != "explota" ? 1f : 0f);
        }

        public static float Play3(Component ai, string anim, int layer, float normalized)
        {
            Get(ai).Play(anim, Time.timeScale > 32f ? 1f : normalized);
            return 0f;
        }

        public static bool IsPlaying(Component ai) { var m = Get(ai); return m.IsLooping || m.Normalized < 1f; }
        public static bool IsPlayingWaitFinish(Component ai) { return Get(ai).Normalized < 1f; }
        public static float GetSpeed(Component ai) { return Get(ai).OwnSpeed; }
        public static void SetSpeed(Component ai, float s) { Get(ai).OwnSpeed = s; }
        public static string GetName(Component ai) { return Get(ai).Current; }
        public static string CollectData(Component ai) { var m = Get(ai); return IsPlaying(ai) ? m.Current : string.Empty; }
    }

    /// <summary>Verbose mode only (Mods/verbose.txt): logs the state of a clickable object every 2 seconds.</summary>
    public class ModClickDebug : MonoBehaviour
    {
        float next;
        static string Field(object o, string f)
        {
            if (o == null) return "?";
            var fi = o.GetType().GetField(f, System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.NonPublic);
            var v = fi == null ? null : fi.GetValue(o);
            return v == null || (v is UnityEngine.Object && !(UnityEngine.Object)v) ? "NULL" : "ok";
        }
        void Update()
        {
            if (Time.realtimeSinceStartup < next) return;
            next = Time.realtimeSinceStartup + 2f;
            var it = GetComponent<StoryItemInterface>(); var hl = GetComponent<OnMouseOutline>();
            var sr = GetComponent<SpriteRenderer>(); var col = GetComponent<PolygonCollider2D>();
            Hooks.Log("DEBUG " + name + ": active=" + gameObject.activeInHierarchy + " layer=" + gameObject.layer
                + " parentLayer=" + (transform.parent ? transform.parent.gameObject.layer : -1)
                + " collider=" + (col ? col.enabled + " pts=" + col.GetTotalPointCount() + " bounds=" + col.bounds : "none")
                + " renderer=" + (sr ? sr.enabled.ToString() : "none")
                + " item.sc=" + Field(it, "sc") + " item.outline=" + Field(it, "onMouseOutline")
                + " outlineMat=" + (hl && hl.outline ? hl.outline.name + "/" + hl.outline.shader.name : "NULL")
                + " current=" + (sr ? sr.sharedMaterial.name : "?") + " activeOver=" + (hl ? hl.activeOver.ToString() : "?")
                + " mouseOver=" + Raw(hl, "mouseOver") + " inside=" + Raw(it, "estoyDentro") + " collected=" + Collected(it));
        }
        static string Raw(object o, string f)
        {
            var fi = o == null ? null : o.GetType().GetField(f, System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.NonPublic);
            return fi == null ? "?" : "" + fi.GetValue(o);
        }
        static string Collected(StoryItemInterface it)
        {
            var fi = typeof(StoryItemInterface).GetField("sc", System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.NonPublic);
            var sc = fi == null ? null : fi.GetValue(it) as storyController;
            if (sc == null || sc.keywordsListHashtable == null) return "?";
            return "" + sc.keywordsListHashtable[it.wordId];
        }
    }
}
