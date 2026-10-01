// 슬라이드 p2-v1-arrayref — 배열은 참조 형식, Clone 은 얕다, C# 1.0
using System;

class App
{
    static void Main()
    {
        int[] a = { 1, 2, 3 };
        int[] b = a;                          // same array
        b[0] = 9;
        Console.WriteLine("a[0]=" + a[0]);

        int[] c = (int[])a.Clone();           // new array, copied ints
        c[1] = 8;
        Console.WriteLine("a[1]=" + a[1] + " c[1]=" + c[1]);

        int[][] jag = { new int[] { 1 }, new int[] { 2 } };
        int[][] copy = (int[][])jag.Clone();  // copies the references
        copy[0][0] = 100;
        copy[1] = new int[] { 200 };
        Console.WriteLine("jag " + jag[0][0] + " " + jag[1][0]);
        Console.WriteLine("copy " + copy[0][0] + " " + copy[1][0]);

        Console.WriteLine(a.Equals(c) + " " + (a == b));
    }
}
