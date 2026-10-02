// 슬라이드 p8-v7_1-refasm-only — 참조 어셈블리를 불러오려 하면, C# 7.1
using System;
using System.IO;
using System.Runtime.Loader;

class App
{
    static void Main()
    {
        foreach (string dll in new[] { "bin/a.dll", "bin/ref.dll" })
        {
            if (!File.Exists(dll)) continue;
            var alc = new AssemblyLoadContext(dll);  // a fresh context
            try
            {
                var a = alc.LoadFromAssemblyPath(Path.GetFullPath(dll));
                Console.WriteLine(dll + ": loaded " + a.GetName().Name);
            }
            catch (BadImageFormatException e)
            {
                Console.WriteLine(dll + ": " + e.GetType().Name);
                Console.WriteLine("  " + e.Message);
            }
        }
    }
}
