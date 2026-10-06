// 슬라이드 p13-v12-ia-layout — 인라인 배열의 크기와 원소 형식, C# 12.0
using System;
using System.Reflection;
using System.Runtime.CompilerServices;

[InlineArray(8)] struct Ints { int _e; }
[InlineArray(3)] struct Names { string _e; }     // managed: ok
[InlineArray(4)] struct Buf<T> { T _e; }         // generic: ok
unsafe struct Fixed { public fixed int E[8]; }   // C# 2

class App
{
    static void Main()
    {
        Console.WriteLine("Ints      " + Unsafe.SizeOf<Ints>());
        Console.WriteLine("Fixed     " + Unsafe.SizeOf<Fixed>());
        Console.WriteLine("Names     " + Unsafe.SizeOf<Names>());
        Console.WriteLine("Buf<long> " + Unsafe.SizeOf<Buf<long>>());
        var f = typeof(Ints).GetFields(BindingFlags.Instance
                                       | BindingFlags.NonPublic);
        var a = typeof(Ints).GetCustomAttribute<InlineArrayAttribute>();
        Console.WriteLine($"fields={f.Length} Length={a.Length}");

        var n = new Names();
        n[0] = "Ada";
        GC.Collect();              // elements are tracked by the GC
        Console.WriteLine(n[0] + " " + (n[2] == null));
        var g = new Buf<string>();
        g[^1] = "last";            // System.Index
        Console.WriteLine(g[3]);
    }
}
