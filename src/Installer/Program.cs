using System;
using System.IO;
using System.Linq;
using Mono.Cecil;
using Mono.Cecil.Cil;

namespace DNFTMInstaller
{
    /// <summary>
    /// Installs the DNFTM mod loader into a local copy of Do Not Feed the Monkeys.
    ///
    /// It never ships or modifies game code other than adding small call sites:
    ///   main.Awake()                              -> Hooks.OnMainAwake(this)
    ///   main.getResourceFile(name)                -> if (Hooks.HandlesResourceFile(name)) return Hooks.GetResourceFile(name);
    ///   storyController.getStoryMetadata(id)      -> if (Hooks.HandlesStory(id)) return Hooks.GetStoryMetadata(id);
    ///   storyController.getStoryNews(id)          -> if (Hooks.HandlesStory(id)) return Hooks.GetStoryNews(id);
    ///   MenuController.startNewGame()             -> Hooks.OnStartNewGame(this)
    ///   animationInterface (8 methods)            -> DNFTMModLoader.AnimHooks for custom art objects
    ///   main.loadImage / NewspapperController.generateNews: Resources.Load(path) -> Hooks.LoadImageResource(path)
    ///                                             (lets mods use their own PNGs as news, web, chat and ending images)
    /// The original DLL is backed up once and every install patches from that backup,
    /// so installing twice is safe and uninstalling restores the exact original file.
    /// </summary>
    internal static class Program
    {
        const string TargetDll = "Assembly-UnityScript.dll";
        const string BackupSuffix = ".dnftm-backup";
        const string LoaderDll = "DNFTMModLoader.dll";
        const string HooksType = "DNFTMModLoader.Hooks";
        const string Marker = "DNFTMModLoaderPatched";

        static string VersionOf(System.Reflection.AssemblyName n)
        {
            var v = n.Version;
            return v == null ? "?" : v.Major + "." + v.Minor + "." + v.Build;
        }

        /// <summary>The version of a DNFTMModLoader.dll (from its assembly name), or "not found".</summary>
        static string LoaderVersion(string path)
        {
            try { return File.Exists(path) ? VersionOf(System.Reflection.AssemblyName.GetAssemblyName(path)) : "not found / 找不到"; }
            catch (Exception) { return "?"; }
        }

        static int Main(string[] args)
        {
            Console.OutputEncoding = System.Text.Encoding.UTF8;
            Console.WriteLine("DNFTM Mod Installer " + VersionOf(System.Reflection.Assembly.GetExecutingAssembly().GetName()) +
                              "  (ModLoader " + LoaderVersion(Path.Combine(AppDomain.CurrentDomain.BaseDirectory, LoaderDll)) + ")");
            Console.WriteLine();

            string mode = null;
            string gameDir = null;
            foreach (string a in args)
            {
                if (a == "install" || a == "uninstall" || a == "status") mode = a;
                else gameDir = a;
            }
            bool interactive = mode == null;

            try
            {
                gameDir = FindGameDir(gameDir ?? AppDomain.CurrentDomain.BaseDirectory);
                if (gameDir == null)
                {
                    Fail("Could not find the game. Put this installer in the game folder (next to dnftm.exe) or pass the folder as an argument.\n" +
                         "找不到遊戲。請把安裝器放在遊戲資料夾（dnftm.exe 旁邊），或把資料夾路徑當作參數傳入。");
                    return Exit(1, interactive);
                }
                string managed = Path.Combine(FindDataDir(gameDir), "Managed");
                Console.WriteLine("Game folder / 遊戲資料夾: " + gameDir);

                if (interactive)
                {
                    Console.WriteLine();
                    Console.WriteLine("  1) Install / 安裝");
                    Console.WriteLine("  2) Uninstall / 解除安裝");
                    Console.Write("Choose / 請選擇 [1/2]: ");
                    string choice = (Console.ReadLine() ?? "").Trim();
                    mode = choice == "2" ? "uninstall" : choice == "1" ? "install" : null;
                    if (mode == null) { Console.WriteLine("Cancelled / 已取消"); return Exit(0, true); }
                }

                int code;
                switch (mode)
                {
                    case "install": code = Install(gameDir, managed); break;
                    case "uninstall": code = Uninstall(managed); break;
                    default: code = Status(managed); break;
                }
                return Exit(code, interactive);
            }
            catch (Exception e)
            {
                Fail(e.ToString());
                return Exit(1, interactive);
            }
        }

        static int Install(string gameDir, string managed)
        {
            string target = Path.Combine(managed, TargetDll);
            string backup = target + BackupSuffix;
            string loaderSrc = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, LoaderDll);
            if (!File.Exists(loaderSrc))
            {
                Fail(LoaderDll + " must be next to the installer / 必須和安裝器放在同一個資料夾。");
                return 1;
            }

            if (!File.Exists(backup))
            {
                if (IsPatched(target))
                {
                    Fail("Game DLL is already patched but the backup is missing. Verify game files in Steam/GOG first.\n" +
                         "遊戲 DLL 已被修改但找不到備份，請先在 Steam/GOG 驗證遊戲檔案完整性。");
                    return 1;
                }
                File.Copy(target, backup);
                Console.WriteLine("Backup created / 已建立備份: " + Path.GetFileName(backup));
            }

            // Copy the loader first so the patched DLL can resolve it.
            string loaderDst = Path.Combine(managed, LoaderDll);
            File.Copy(loaderSrc, loaderDst, true);

            var resolver = new DefaultAssemblyResolver();
            resolver.AddSearchDirectory(managed);
            var readerParams = new ReaderParameters { AssemblyResolver = resolver, ReadingMode = ReadingMode.Immediate, InMemory = true };

            using (var game = AssemblyDefinition.ReadAssembly(backup, readerParams))
            using (var loader = AssemblyDefinition.ReadAssembly(loaderDst, readerParams))
            {
                var module = game.MainModule;
                var hooks = loader.MainModule.GetType(HooksType) ?? throw new Exception("Hooks type not found in " + LoaderDll);
                MethodReference Hook(string name) => module.ImportReference(hooks.Methods.Single(m => m.Name == name));

                var mainType = module.GetType("main") ?? throw new Exception("type 'main' not found");
                var storyType = module.GetType("storyController") ?? throw new Exception("type 'storyController' not found");

                InjectCall(Single(mainType, "Awake", 0), Hook("OnMainAwake"));
                InjectPrefix(Single(mainType, "getResourceFile", 1), Hook("HandlesResourceFile"), Hook("GetResourceFile"));
                InjectPrefix(Single(storyType, "getStoryMetadata", 1), Hook("HandlesStory"), Hook("GetStoryMetadata"));
                InjectPrefix(Single(storyType, "getStoryNews", 1), Hook("HandlesStory"), Hook("GetStoryNews"));

                // Opt-in mods: a new game records the mods ticked on the MODS page.
                var menuType = module.GetType("MenuController") ?? throw new Exception("type 'MenuController' not found");
                InjectCall(Single(menuType, "startNewGame", 1), Hook("OnStartNewGame"));

                // Custom art: animationInterface calls go to DNFTMModLoader.AnimHooks when the object has a ModSpriteAnimator.
                var animType = module.GetType("animationInterface") ?? throw new Exception("type 'animationInterface' not found");
                var animHooks = loader.MainModule.GetType("DNFTMModLoader.AnimHooks") ?? throw new Exception("AnimHooks type not found in " + LoaderDll);
                MethodReference AH(string name) => module.ImportReference(animHooks.Methods.Single(m => m.Name == name));
                var isMod = AH("IsMod");
                InjectInstancePrefix(Single(animType, "Play", 1), isMod, AH("Play1"));
                InjectInstancePrefix(Single(animType, "Play", 3), isMod, AH("Play3"));
                InjectInstancePrefix(Single(animType, "isPlaying", 0), isMod, AH("IsPlaying"));
                InjectInstancePrefix(Single(animType, "isPlayingWaitFinish", 0), isMod, AH("IsPlayingWaitFinish"));
                InjectInstancePrefix(Single(animType, "getAnimationSpeed", 0), isMod, AH("GetSpeed"));
                InjectInstancePrefix(Single(animType, "setAnimationSpeed", 1), isMod, AH("SetSpeed"));
                InjectInstancePrefix(Single(animType, "getAnimationName", 0), isMod, AH("GetName"));
                InjectInstancePrefix(Single(animType, "collectData", 0), isMod, AH("CollectData"));

                // Mod images: every browser/chat/ending/door image and the newspaper photos are loaded with Resources.Load(string).
                var newsType = module.GetType("NewspapperController") ?? throw new Exception("type 'NewspapperController' not found");
                var loadImg = Hook("LoadImageResource");
                int redirected = RedirectResourcesLoad(Single(mainType, "loadImage", 1), loadImg)
                               + RedirectResourcesLoad(Single(newsType, "generateNews", 0, allowMany: true), loadImg);
                if (redirected != 2) throw new Exception("Expected 2 image loads to redirect, found " + redirected + ". Unsupported game version?");

                // Marker type so status/install can tell a patched DLL apart.
                module.Types.Add(new TypeDefinition("", Marker, TypeAttributes.NotPublic | TypeAttributes.Abstract | TypeAttributes.Sealed, module.TypeSystem.Object));

                string tmp = target + ".tmp";
                game.Write(tmp);
                File.Copy(tmp, target, true);
                File.Delete(tmp);
            }

            Directory.CreateDirectory(Path.Combine(gameDir, "Mods"));
            Console.WriteLine("Installed ModLoader " + LoaderVersion(loaderDst) + " / 安裝完成。Put mods in / mod 放在: " + Path.Combine(gameDir, "Mods"));
            return 0;
        }

        static int Uninstall(string managed)
        {
            string target = Path.Combine(managed, TargetDll);
            string backup = target + BackupSuffix;
            if (!File.Exists(backup))
            {
                Console.WriteLine("Not installed (no backup found) / 尚未安裝（找不到備份）。");
                return 0;
            }
            File.Copy(backup, target, true);
            File.Delete(backup);
            string loader = Path.Combine(managed, LoaderDll);
            if (File.Exists(loader)) File.Delete(loader);
            Console.WriteLine("Uninstalled, original DLL restored. Your Mods folder was left untouched.");
            Console.WriteLine("已解除安裝並還原原始 DLL，Mods 資料夾沒有被刪除。");
            return 0;
        }

        static int Status(string managed)
        {
            string target = Path.Combine(managed, TargetDll);
            Console.WriteLine("Patched / 已安裝: " + IsPatched(target));
            Console.WriteLine("Installed ModLoader / 已安裝的 ModLoader: " + LoaderVersion(Path.Combine(managed, LoaderDll)));
            Console.WriteLine("Backup / 備份: " + File.Exists(target + BackupSuffix));
            return 0;
        }

        // ------------------------------------------------------------------ IL injection

        static MethodDefinition Single(TypeDefinition type, string name, int paramCount, bool allowMany = false)
        {
            var found = type.Methods.Where(m => m.Name == name && (allowMany || m.Parameters.Count == paramCount) && m.HasBody).ToList();
            if (found.Count != 1) throw new Exception($"Expected exactly one {type.Name}.{name}({paramCount} args), found {found.Count}. Unsupported game version?");
            return found[0];
        }

        /// <summary>Replaces each call to UnityEngine.Resources.Load(string) in a method with a call to hook(string).</summary>
        static int RedirectResourcesLoad(MethodDefinition method, MethodReference hook)
        {
            int n = 0;
            foreach (var ins in method.Body.Instructions)
            {
                if (ins.OpCode != OpCodes.Call || !(ins.Operand is MethodReference mr)) continue;
                if (mr.DeclaringType.FullName == "UnityEngine.Resources" && mr.Name == "Load" && mr.Parameters.Count == 1)
                {
                    ins.Operand = hook;
                    n++;
                }
            }
            return n;
        }

        /// <summary>Inserts <c>Hook(this)</c> at the start of an instance method.</summary>
        static void InjectCall(MethodDefinition method, MethodReference hook)
        {
            var il = method.Body.GetILProcessor();
            var first = method.Body.Instructions[0];
            il.InsertBefore(first, il.Create(OpCodes.Ldarg_0));
            il.InsertBefore(first, il.Create(OpCodes.Call, hook));
        }

        /// <summary>
        /// Inserts, at the start of a static one-argument method:
        ///   if (handles(arg0)) return get(arg0);
        /// </summary>
        static void InjectPrefix(MethodDefinition method, MethodReference handles, MethodReference get)
        {
            if (!method.IsStatic) throw new Exception(method.FullName + " is not static");
            var body = method.Body;
            var il = body.GetILProcessor();
            var first = body.Instructions[0];
            il.InsertBefore(first, il.Create(OpCodes.Ldarg_0));
            il.InsertBefore(first, il.Create(OpCodes.Call, handles));
            il.InsertBefore(first, il.Create(OpCodes.Brfalse, first));
            il.InsertBefore(first, il.Create(OpCodes.Ldarg_0));
            il.InsertBefore(first, il.Create(OpCodes.Call, get));
            il.InsertBefore(first, il.Create(OpCodes.Ret));
            body.MaxStackSize = Math.Max(body.MaxStackSize, 2);
        }

        /// <summary>
        /// Inserts, at the start of an instance method with any arguments:
        ///   if (handles(this)) return impl(this, arg1, ..., argN);
        /// impl must take (Component, args...) and return the method's return type.
        /// </summary>
        static void InjectInstancePrefix(MethodDefinition method, MethodReference handles, MethodReference impl)
        {
            if (method.IsStatic) throw new Exception(method.FullName + " is static");
            var body = method.Body;
            var il = body.GetILProcessor();
            var first = body.Instructions[0];
            il.InsertBefore(first, il.Create(OpCodes.Ldarg_0));
            il.InsertBefore(first, il.Create(OpCodes.Call, handles));
            il.InsertBefore(first, il.Create(OpCodes.Brfalse, first));
            il.InsertBefore(first, il.Create(OpCodes.Ldarg_0));
            foreach (var p in method.Parameters) il.InsertBefore(first, il.Create(OpCodes.Ldarg, p));
            il.InsertBefore(first, il.Create(OpCodes.Call, impl));
            il.InsertBefore(first, il.Create(OpCodes.Ret));
            body.MaxStackSize = Math.Max(body.MaxStackSize, method.Parameters.Count + 2);
        }

        // ------------------------------------------------------------------ helpers

        static bool IsPatched(string dll)
        {
            using (var asm = AssemblyDefinition.ReadAssembly(dll, new ReaderParameters { InMemory = true }))
                return asm.MainModule.GetType(Marker) != null;
        }

        static string FindDataDir(string gameDir)
        {
            return Directory.GetDirectories(gameDir, "*_Data")
                .FirstOrDefault(d => File.Exists(Path.Combine(d, "Managed", TargetDll)));
        }

        static string FindGameDir(string start)
        {
            string dir = Path.GetFullPath(start);
            for (int i = 0; i < 3 && dir != null; i++)
            {
                if (Directory.Exists(dir) && FindDataDir(dir) != null) return dir;
                dir = Path.GetDirectoryName(dir);
            }
            return null;
        }

        static void Fail(string msg)
        {
            Console.ForegroundColor = ConsoleColor.Red;
            Console.WriteLine("ERROR: " + msg);
            Console.ResetColor();
        }

        static int Exit(int code, bool interactive)
        {
            if (interactive)
            {
                Console.WriteLine();
                Console.Write("Press Enter to close / 按 Enter 關閉...");
                Console.ReadLine();
            }
            return code;
        }
    }
}
