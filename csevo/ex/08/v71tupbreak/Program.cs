// 슬라이드 p8-v7_1-tuplenames-break — 이름 유추가 바꾼 호출, C# 7.1
using System;

static class Ext
{
    // an extension method named like the second element
    public static string a(this (int, Func<string>) t)
    {
        return "extension method a";
    }
}

class App
{
    static void Main()
    {
        int x = 1;
        Func<string> a = () => "tuple element a";
        var t = (x, a);
        Console.WriteLine(t.a());
    }
}
