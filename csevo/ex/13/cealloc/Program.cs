// 슬라이드 p13-v12-ce-alloc — 할당한 바이트를 센다, C# 12
using System;
using System.Collections.Generic;
using System.Linq;

class Program
{
    static int[] xs = [1, 2, 3], ys = [4, 5, 6];
    static object keep;

    static void Spread() { int[] a = [.. xs, .. ys]; keep = a; }
    static void Linq() { keep = xs.Concat(ys).ToArray(); }
    static void ListCe() { List<int> l = [.. xs, .. ys]; keep = l; }
    static void ListAdd()
    {
        var l = new List<int>();
        l.AddRange(xs);
        l.AddRange(ys);
        keep = l;
    }
    static void Seq() { IEnumerable<int> e = [.. xs, .. ys]; keep = e; }

    static long Bytes(Action a)
    {
        a();                                     // JIT first
        long b0 = GC.GetAllocatedBytesForCurrentThread();
        a();
        return GC.GetAllocatedBytesForCurrentThread() - b0;
    }

    static void Main()
    {
        Console.WriteLine("[..xs, ..ys] int[]  " + Bytes(Spread));
        Console.WriteLine("Concat().ToArray()  " + Bytes(Linq));
        Console.WriteLine("[..xs, ..ys] List   " + Bytes(ListCe));
        Console.WriteLine("new List + AddRange " + Bytes(ListAdd));
        Console.WriteLine("[..xs, ..ys] IEnum  " + Bytes(Seq));
    }
}
