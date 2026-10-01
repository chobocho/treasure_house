// 슬라이드 p4-v3-implarray — 암시적 형식 배열 new[], C# 3.0
using System;

class App
{
    static void Main()
    {
        int[] a = new[] { 1, 2, 3 };
        string[][] b = new[] { new[] { "x" }, new[] { "y", "z" } };
        Console.WriteLine(a.Length + " " + b[1][1]);
    }
}
