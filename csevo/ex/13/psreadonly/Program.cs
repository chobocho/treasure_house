// 슬라이드 p13-v12-ps-readonly — readonly 구조체의 포착 필드, C# 12.0
using System;
using System.Reflection;

readonly struct Temp(double c)
{
    public double F => c * 9 / 5 + 32;
#if BAD
    public void Warm() { c += 1; }
#endif
}

struct Gauge(int level)
{
    public readonly int Read() => level;
    public void Up() => level++;              // fine: not readonly
#if BAD2
    public readonly void Down() { level--; }
#endif
}

class App
{
    static void Main()
    {
        var flags = BindingFlags.Instance | BindingFlags.NonPublic;
        foreach (var t in new[] { typeof(Temp), typeof(Gauge) })
            foreach (var f in t.GetFields(flags))
                Console.WriteLine($"{t.Name}.{f.Name} "
                    + $"readonly={f.IsInitOnly}");
        var g = new Gauge(1);
        g.Up();
        Console.WriteLine($"{new Temp(100).F} {g.Read()}");
    }
}
