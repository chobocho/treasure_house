// 슬라이드 p4-v3-linq-selectmany — 쿼리 문법에 없는 오버로드들, C# 3.0
using System;
using System.Linq;

class Program
{
    static void Main()
    {
        string[] teams = { "red:Kim,Lee", "blue:Park" };

        // SelectMany with a result selector (what "from from" uses)
        var members = teams.SelectMany(
            t => t.Split(':')[1].Split(','),
            (t, m) => m + "@" + t.Split(':')[0]);
        Console.WriteLine(string.Join(" ", members));

        // index overloads have no query syntax
        var numbered = teams.Select((t, i) =>
            i + "=" + t.Split(':')[0]);
        Console.WriteLine(string.Join(" ", numbered));

        var everyOther = "abcdef".Where((c, i) => i % 2 == 0);
        Console.WriteLine(new string(everyOther.ToArray()));
    }
}
