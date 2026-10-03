// 슬라이드 p11-v10-la-synth — 합성되는 대리자 형식, C# 10.0
using System;
using System.Reflection;

class App
{
    static void Show(string what, Delegate d)
    {
        Type t = d.GetType();
        ParameterInfo[] ps = t.GetMethod("Invoke").GetParameters();
        string sig = ps.Length > 2 ? ps.Length + " parameters"
            : string.Join(", ", Array.ConvertAll(ps,
                p => p.ParameterType.Name + " " + p.Name));
        Console.WriteLine($"{what,-20}{t.Name}");
        Console.WriteLine($"{"",-20}public={t.IsPublic} Invoke({sig})");
    }

    static void Main()
    {
        var inc = (ref int x) => x++;                 // ref parameter
        var get = (out int x) => { x = 7; };          // out parameter
        var big = (int a1, int a2, int a3, int a4, int a5, int a6,
                   int a7, int a8, int a9, int a10, int a11, int a12,
                   int a13, int a14, int a15, int a16, int a17) => a17;
        var inc2 = (ref int y) => y++;                // same signature

        Show("(ref int x) => x++", inc);
        Show("(out int x) => ...", get);
        Show("17 int parameters", big);
        Console.WriteLine($"same type for inc/inc2: " +
                          $"{inc.GetType() == inc2.GetType()}");
        int n = 1;
        inc(ref n);
        get(out int m);
        Console.WriteLine($"n={n} m={m}");
    }
}
