// 슬라이드 p10-v9-rec-contract — EqualityContract, C# 9.0
using System;
using System.Reflection;

record Base(int X);
record Derived(int X) : Base(X);         // no new fields

class App
{
    static Type Contract(Base b) => (Type)typeof(Base)
        .GetProperty("EqualityContract",
            BindingFlags.Instance | BindingFlags.NonPublic)
        .GetValue(b);

    static void Main()
    {
        Base b = new Base(1);
        Base d = new Derived(1);
        Console.WriteLine("b == d       " + (b == d));
        Console.WriteLine("b.Equals(d)  " + b.Equals(d));
        Console.WriteLine("d.Equals(b)  " + d.Equals(b));
        Console.WriteLine("contracts    " + Contract(b).Name + " / "
            + Contract(d).Name);
        Console.WriteLine("d == d2      " + (d == new Derived(1)));
    }
}
