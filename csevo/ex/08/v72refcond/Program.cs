// 슬라이드 p8-v7_2-refcond — ref 조건식, C# 7.2
using System;

class App
{
    // the old workaround: a method that picks one of two refs
    static ref int Choice(bool c, ref int a, ref int b)
    {
        if (c) return ref a;
        return ref b;
    }

    static void Main()
    {
        int[] a = { 1, 2, 3 }, b = { 10, 20, 30 };
        bool big = a.Length > 5;

        ref int r = ref (big ? ref a[0] : ref b[0]);
        r = 99;                                // writes b[0]
        (big ? ref a[1] : ref b[1]) = 77;      // assign to it directly
        Console.WriteLine(string.Join(",", b));

        int[] none = null;
        ref int z = ref (none != null ? ref none[0] : ref b[2]);
        Console.WriteLine(z);                  // only one side ran
        try
        {
            ref int w = ref Choice(none != null, ref none[0], ref b[2]);
        }
        catch (NullReferenceException)
        {
            Console.WriteLine("Choice: both sides ran");
        }
    }
}
