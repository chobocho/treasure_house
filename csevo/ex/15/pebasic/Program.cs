// 슬라이드 p15-v14-partial — partial 이벤트와 생성자, C# 14
using System;

partial class Sensor
{
    // defining declarations
    public partial Sensor(string name);
    public partial event Action<int> Changed;
}

partial class Sensor
{
    // implementing declarations
    Action<int> handlers;
    readonly string name;

    public partial Sensor(string name)
    {
        this.name = name;
        Console.WriteLine("ctor " + name);
    }

    public partial event Action<int> Changed
    {
        add { Console.WriteLine("add"); handlers += value; }
        remove { Console.WriteLine("remove"); handlers -= value; }
    }

    public void Set(int v) => handlers?.Invoke(v);
}

class Program
{
    static void Main()
    {
        var s = new Sensor("t1");
        Action<int> h = v => Console.WriteLine("got " + v);
        s.Changed += h;
        s.Set(42);
        s.Changed -= h;
        s.Set(43);
    }
}
