// 슬라이드 p8-v7-ref-bcl — 같이 온 런타임: ref 를 돌려주는 BCL, C# 7.0
using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Runtime.InteropServices;

class App
{
    static void Show(Type t, string name)
    {
        MethodInfo m = t.GetMethods().First(x => x.Name == name);
        Console.WriteLine("  {0}.{1} -> {2}", t.Name, name,
            m.ReturnType.Name);
    }

    static void Main()
    {
        var counts = new Dictionary<string, int>();
        foreach (string w in "a b a c a b".Split(' '))
        {
            bool found;
            ref int n = ref CollectionsMarshal
                .GetValueRefOrAddDefault(counts, w, out found);
            n++;                     // one lookup per word
        }
        foreach (var kv in counts.OrderBy(p => p.Key))
            Console.Write(kv.Key + "=" + kv.Value + " ");
        Console.WriteLine();

        Show(typeof(Span<int>), "get_Item");
        Show(typeof(ReadOnlySpan<int>), "get_Item");
        Show(typeof(CollectionsMarshal), "GetValueRefOrAddDefault");
        Show(typeof(MemoryMarshal), "GetArrayDataReference");
        int n2 = typeof(object).Assembly.GetExportedTypes()
            .SelectMany(t => t.GetMethods())
            .Count(m => m.DeclaringType.Assembly == typeof(object)
                .Assembly && m.ReturnType.IsByRef);
        Console.WriteLine("CoreLib ref-returning methods: " + n2);
    }
}
