// 슬라이드 p13-v12-ce-cond — 조건부로 펼치기, C# 12
using System;
using System.Collections.Generic;

class Program
{
    static readonly string[] Verbose = ["-v", "--log"];

    static List<string> Args(bool verbose, string[] files) =>
        ["build", .. verbose ? Verbose : [], .. files];
#if BAD
    static List<string> Bad(bool v) => ["build", .. v ? ["-v"] : []];
#endif

    static void Main()
    {
        Console.WriteLine(string.Join(" ", Args(false, ["a.cs"])));
        Console.WriteLine(string.Join(" ",
            Args(true, ["a.cs", "b.cs"])));
        int x = -3;
        int[] r = x switch
        {
            0 => [],
            < 0 => [-1, x],
            _ => [x, x],
        };
        int[] s = x > 0 ? [x] : [];      // target-typed ?:
        Console.WriteLine(r.Length + " " + s.Length);
    }
}
