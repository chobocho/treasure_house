// 슬라이드 p13-v12-lp-mix — 기본값과 params 를 한 람다에, C# 12
using System;

class Program
{
    static void Main()
    {
        var log = (string msg, int level = 1, params object[] args) =>
            "[" + level + "] " + string.Format(msg, args);
        Console.WriteLine(log("start"));
        Console.WriteLine(log("x={0} y={1}", 2, 10, 20));
#if BAD
        var bad = (params int[] xs = null) => xs.Length;
#endif
#if BAD2
        var bad2 = (params int[] xs, int n) => n;
#endif
    }
}
