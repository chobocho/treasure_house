// 슬라이드 p4-v3-query-group-key — 익명 형식을 묶음 키로, C# 3.0
using System;
using System.Linq;

class Key
{
    public string Region; public int Q;
    public Key(string r, int q) { Region = r; Q = q; }
}

class Program
{
    static void Main()
    {
        var sales = new[] {
            new { Region = "N", Q = 1, Amount = 5 },
            new { Region = "S", Q = 1, Amount = 3 },
            new { Region = "N", Q = 1, Amount = 2 },
            new { Region = "N", Q = 2, Amount = 4 },
        };

        var byAnon = from s in sales
                     group s.Amount by new { s.Region, s.Q } into g
                     select g.Key + " -> " + g.Sum();
        foreach (string line in byAnon) Console.WriteLine(line);

        var byClass = from s in sales
                      group s.Amount by new Key(s.Region, s.Q);
        Console.WriteLine("class key: " + byClass.Count() + " groups");
    }
}
