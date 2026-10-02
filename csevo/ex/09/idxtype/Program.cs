// 슬라이드 p9-v8-index-type — System.Index 라는 값, C# 8.0
using System;

class App
{
    static void Main()
    {
        Index last = ^1;                 // new Index(1, fromEnd: true)
        Index third = 2;                 // implicit from int
        Console.WriteLine("{0} {1}", last, third);
        Console.WriteLine("Value={0} IsFromEnd={1}",
            last.Value, last.IsFromEnd);
        Console.WriteLine("offset in 10: {0}", last.GetOffset(10));
        Console.WriteLine(last.Equals(new Index(1, fromEnd: true)));

        int[] a = { 10, 20, 30 };
        int[] b = { 1, 2, 3, 4, 5 };
        Console.WriteLine("{0} {1}", a[last], b[last]);   // same Index

        int n = -1;
        try
        {
            Index bad = ^n;
        }
        catch (ArgumentOutOfRangeException e)
        {
            Console.WriteLine(e.GetType().Name + ": " + e.ParamName);
        }
    }
}
