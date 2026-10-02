// 슬라이드 p9-v8-dim-runtime — 런타임이 알리는 기능, C# 8.0
using System;
using System.Reflection;
using System.Runtime.CompilerServices;

class App
{
    static void Main()
    {
        Console.WriteLine("runtime " + Environment.Version);

        // every public const string of RuntimeFeature is a feature name
        foreach (FieldInfo f in typeof(RuntimeFeature).GetFields())
            if (f.IsLiteral)
                Console.WriteLine("  {0,-36} {1}", f.Name,
                    RuntimeFeature.IsSupported(f.Name));

        // the name used in the C# 8 proposal
        string old = "DefaultInterfaceImplementation";
        Console.WriteLine(old + "? " + RuntimeFeature.IsSupported(old));
    }
}
