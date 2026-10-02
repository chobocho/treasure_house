// 슬라이드 p8-v7-exprbody — 생성자·종료자·접근자의 식 본문, C# 7.0
using System;

class Temp
{
    double c;
    Action changed;

    public Temp(double c) => this.c = c;            // constructor
    ~Temp() => changed = null;                      // finalizer

    public double Celsius
    {
        get => c;                                   // get accessor
        set { c = value; changed?.Invoke(); }       // C# 6 style
    }

    public double this[char unit]
    {
        get => unit == 'F' ? c * 9 / 5 + 32 : c;    // indexer get
        set => c = unit == 'F' ? (value - 32) * 5 / 9 : value;
    }

    public event Action Changed
    {
        add => changed += value;                    // event add
        remove => changed -= value;                 // event remove
    }
}

class App
{
    static void Main()
    {
        var t = new Temp(100);
        t.Changed += () => Console.WriteLine("changed");
        t.Celsius = 37;
        Console.WriteLine(t['F'].ToString("0.0"));
        t['F'] = 212;
        Console.WriteLine(t.Celsius);
    }
}
