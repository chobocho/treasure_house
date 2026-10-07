// 슬라이드 p15-v14-runtime-bcl — BCL 의 확장 메서드와 블록, C# 14
using System;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Runtime.CompilerServices;

class Program
{
    static Assembly Load(string f) =>
        Path.GetFileName(f) == "System.Private.CoreLib.dll"
            ? typeof(object).Assembly : Assembly.LoadFrom(f);

    static void Main()
    {
        string dir = Path.GetDirectoryName(
            typeof(object).Assembly.Location);
        int files = 0, classic = 0, blocks = 0;
        foreach (string f in Directory.GetFiles(dir, "System*.dll"))
        {
            Type[] types;
            try { types = Load(f).GetTypes(); files++; }
            catch (BadImageFormatException) { continue; } // native
            catch (ReflectionTypeLoadException e)
            { types = e.Types.Where(t => t != null).ToArray();
              files++; }
            foreach (Type t in types)
            {
                if (t.Name.StartsWith("<G>$")) blocks++; // grouping
                if (!t.IsDefined(typeof(ExtensionAttribute), false))
                    continue;
                classic += t.GetMethods(BindingFlags.Public
                    | BindingFlags.Static | BindingFlags.DeclaredOnly)
                    .Count(m => m.IsDefined(
                        typeof(ExtensionAttribute)));
            }
        }
        Console.WriteLine("assemblies " + files);
        Console.WriteLine("public extension methods " + classic);
        Console.WriteLine("extension blocks " + blocks);
    }
}
