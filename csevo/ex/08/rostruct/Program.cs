// 슬라이드 p8-v7_2-rostruct — readonly struct, C# 7.2
using System;

readonly struct Money
{
    public readonly long Cents;            // fields must be readonly
    public string Code { get; }            // get-only auto-property

    public Money(long cents, string code)
    {
        Cents = cents; Code = code;        // set in the constructor
    }

    public Money Add(long c) => new Money(Cents + c, Code);

    public override string ToString() =>
        (Cents / 100) + "." + (Cents % 100).ToString("00") + " " + Code;
}

class App
{
    static void Main()
    {
        var m = new Money(1250, "KRW");
        Console.WriteLine(m.Add(5));
        Console.WriteLine(m);
        foreach (var a in typeof(Money).GetCustomAttributes(false))
        {
            var t = a.GetType();
            Console.WriteLine(t.FullName);
            Console.WriteLine("  @ " + t.Assembly.GetName().Name);
        }
    }
}
