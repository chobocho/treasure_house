// 슬라이드 p15-v14-fk-struct — 구조체의 field 와 readonly, C# 14
using System;
using System.Reflection;

struct S
{
    public S() { }
    public static int Loads;
    public readonly string P0 { get => field; } = "p0";
    public string P1 { get => field ??= Load(); }      // caches
    public readonly string P3 { get; set { _ = field; } }
#if P2
    public readonly string P2 { get => field ??= ""; }
#endif
#if P4
    public readonly string P4 { get; set { field = value; } }
#endif
    static string Load() { Loads++; return "p1"; }
}

class Program
{
    static readonly S frozen = new S();

    static void Main()
    {
        var s = new S();
        _ = s.P1; _ = s.P1;
        Console.WriteLine("local: Loads=" + S.Loads);
        _ = frozen.P1; _ = frozen.P1;
        Console.WriteLine("readonly field: Loads=" + S.Loads);
        foreach (var f in typeof(S).GetFields(
                     BindingFlags.NonPublic | BindingFlags.Instance))
            Console.WriteLine(f.Name
                + (f.IsInitOnly ? " initonly" : ""));
    }
}
