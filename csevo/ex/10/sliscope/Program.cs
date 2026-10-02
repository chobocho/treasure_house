// 슬라이드 p10-v9-localsinit-scope — 형식에 붙이면 안쪽 모두에, C# 9.0
using System;
using System.Collections.Generic;
using System.Reflection;
using System.Runtime.CompilerServices;
#if MOD
[module: SkipLocalsInit]
#endif

[SkipLocalsInit]
class Fast
{
    public static int Sum(int[] a)
    {
        int s = 0;
        foreach (int x in a) s += x;
        Func<int, int> twice = v => { int w = v; return w * 2; };
        return Local(twice(s));
        static int Local(int v) { int t = v; return t + 1; }
    }
}

class App
{
    static void Main()
    {
        Console.WriteLine(Fast.Sum(new[] { 1, 2, 3 }));
        BindingFlags all = BindingFlags.Static | BindingFlags.Instance
            | BindingFlags.Public | BindingFlags.NonPublic
            | BindingFlags.DeclaredOnly;
        var types = new List<Type> { typeof(Fast) };
        types.AddRange(typeof(Fast).GetNestedTypes(all));
        types.Add(typeof(App));
        foreach (Type x in types)
            foreach (MethodInfo m in x.GetMethods(all))
                Console.WriteLine(x.Name + "." + m.Name + " InitLocals "
                    + m.GetMethodBody().InitLocals);
    }
}
