// 슬라이드 p2-v1-refelem — 배열 원소와 필드를 ref 로, C# 1.0
using System;

class Holder
{
    public int Count;
}

class App
{
    static void Swap(ref int a, ref int b) { int t = a; a = b; b = t; }
    static void Inc(ref int x) { x++; }

    static void Main()
    {
        int[] a = { 1, 2, 3 };
        Swap(ref a[0], ref a[2]);             // elements are variables
        Console.WriteLine(a[0] + " " + a[1] + " " + a[2]);

        Holder h = new Holder();
        Inc(ref h.Count);                     // so are fields
        Inc(ref h.Count);
        Console.WriteLine(h.Count);

        int i = 0;
        Inc(ref a[i++]);                      // index evaluated once
        Console.WriteLine(a[0] + " i=" + i);
    }
}
