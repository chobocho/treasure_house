// 슬라이드 p5-v4-dyn-conv — 암시적 dynamic 변환, C# 4.0
using System;
using Microsoft.CSharp.RuntimeBinder;

class Program
{
    static void Print(Exception e) { Console.WriteLine(e.Message); }

    static void Main()
    {
        dynamic d = "dynamic";
        string s = d;                     // found at run time
        Console.WriteLine(s);
        try { int i = d; }
        catch (RuntimeBinderException e) { Print(e); }

        object o = d;
        try { int j = (int)o; }           // plain unboxing cast
        catch (InvalidCastException e) { Print(e); }

        dynamic n = 42;
        long l = n;                       // int -> long: implicit
        Console.WriteLine(l);
        try { short sh = n; }             // int -> short: explicit only
        catch (RuntimeBinderException e) { Print(e); }
        short ok = (short)n;
        Console.WriteLine(ok);
    }
}
