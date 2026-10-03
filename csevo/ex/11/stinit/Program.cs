// 슬라이드 p11-v10-st-init — 구조체 필드 초기화자, C# 10.0
using System;

struct Counter
{
    public string Name = "unnamed";         // C# 10
    public int Step = 1;
    public int Value;

    public Counter(int start) { Value = start; }
    public Counter(string name) : this(0) { Name = name; }
}

class App
{
    static void Main()
    {
        var a = new Counter(10);
        var b = new Counter("hits");
        Console.WriteLine(a.Name + " " + a.Step + " " + a.Value);
        Console.WriteLine(b.Name + " " + b.Step + " " + b.Value);
        Console.WriteLine(new Counter().Name ?? "(null)");
    }
}
