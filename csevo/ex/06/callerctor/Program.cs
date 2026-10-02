// 슬라이드 p6-v5-caller-ctor — 생성자·연산자·암시적 호출, C# 5.0
using System;
using System.Runtime.CompilerServices;

class Base
{
    public Base([CallerMemberName] string m = "(default)")
    {
        Console.WriteLine("Base() sees " + m);
    }
}

class Implicit : Base { public Implicit() { } }
class Explicit : Base { public Explicit() : base() { } }

class Money
{
    static string N([CallerMemberName] string m = "?") { return m; }

    static Money() { Console.WriteLine("static ctor -> " + N()); }
    public Money() { Console.WriteLine("ctor        -> " + N()); }
    public static Money operator +(Money a, Money b)
    { Console.WriteLine("operator +  -> " + N()); return a; }
    public static implicit operator int(Money a)
    { Console.WriteLine("conversion  -> " + N()); return 0; }
}

class App
{
    static void Main()
    {
        Money a = new Money();
        Money b = a + a;
        int n = b;
        new Implicit();
        new Explicit();
    }
}
