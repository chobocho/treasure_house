// 슬라이드 p10-v9-sl-cache — static 람다와 대리자 캐시, C# 9.0
using System;

class App
{
    static Func<int, int> Static() => static x => x + 1;
    static Func<int, int> Plain() => x => x + 1;
    static Func<int, int> Capture(int k) => x => x + k;

    static void Show(string name, Func<int, int> a, Func<int, int> b)
    {
        Console.WriteLine("{0,-8} same={1,-5} static={2,-5} {3}",
            name, ReferenceEquals(a, b), a.Method.IsStatic,
            a.Target == null ? "-" : a.Target.GetType().Name);
    }

    static void Main()
    {
        Show("static", Static(), Static());
        Show("plain", Plain(), Plain());
        Show("capture", Capture(1), Capture(1));
    }
}
