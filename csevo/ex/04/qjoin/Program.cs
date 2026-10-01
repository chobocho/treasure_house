// 슬라이드 p4-v3-query-join — join … on … equals, C# 3.0
using System;
using System.Linq;

class Program
{
    static void Main()
    {
        var customers = new[] {
            new { Id = 1, Name = "Kim" },
            new { Id = 2, Name = "Lee" },
            new { Id = 3, Name = "Park" },
        };
        var orders = new[] {
            new { CustId = 3, Item = "ink" },
            new { CustId = 1, Item = "pen" },
            new { CustId = 9, Item = "cup" },
            new { CustId = 1, Item = "pad" },
        };

        var q = from c in customers
                join o in orders on c.Id equals o.CustId
                select c.Name + ":" + o.Item;
        Console.WriteLine(string.Join(" ", q));

        var m = customers.Join(orders, c => c.Id, o => o.CustId,
                               (c, o) => c.Name + ":" + o.Item);
        Console.WriteLine(string.Join(" ", m));
    }
}
