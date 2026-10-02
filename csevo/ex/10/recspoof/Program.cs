// 슬라이드 p10-v9-rec-contract-override — 계약을 직접, C# 9.0
using System;

record Base(int X);

record Derived(int X) : Base(X)
{
    // pretend to be a Base for equality
    protected override Type EqualityContract => typeof(Base);
}

class App
{
    static void Main()
    {
        Base b = new Base(1);
        Base d = new Derived(1);
        Console.WriteLine("b == d       " + (b == d));
        Console.WriteLine("d == b       " + (d == b));
        Console.WriteLine("b.Equals(d)  " + b.Equals(d));
        Console.WriteLine("d.Equals(b)  " + d.Equals(b));
        Console.WriteLine(d);
    }
}
