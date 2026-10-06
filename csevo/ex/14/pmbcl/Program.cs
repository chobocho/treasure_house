// 슬라이드 p14-v13-pm-recompile — 다시 컴파일만 해도 스팬 판으로, C# 13
using System;
using System.IO;

class Program
{
    static string a = "a", b = "b", c = "c", d = "d", e = "e";
    static string[] abc = { "a", "b", "c" };

    static long Bytes(Func<string> f)
    {
        f();                                    // warm up
        long b0 = GC.GetAllocatedBytesForCurrentThread();
        f();
        return GC.GetAllocatedBytesForCurrentThread() - b0;
    }

    static void Main()
    {
        Console.WriteLine("string.Join(\",\", a, b, c)     "
            + Bytes(() => string.Join(",", a, b, c)));
        Console.WriteLine("string.Concat(a, b, c, d, e)  "
            + Bytes(() => string.Concat(a, b, c, d, e)));
        Console.WriteLine("Path.Combine(a, b, c, d, e)   "
            + Bytes(() => Path.Combine(a, b, c, d, e)));
        Console.WriteLine("string.Join(\",\", a)           "
            + Bytes(() => string.Join(",", a)));
        Console.WriteLine("string.Join(\",\", abc)         "
            + Bytes(() => string.Join(",", abc)));
    }
}
