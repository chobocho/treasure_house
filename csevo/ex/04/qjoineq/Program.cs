// 슬라이드 p4-v3-query-join-trap — == 가 아니라 equals, C# 3.0
using System;
using System.Linq;

class Program
{
    static void Main()
    {
        var customers = new[] { new { Id = 1, Name = "Kim" } };
        var orders = new[] { new { CustId = 1, Item = "pen" } };

        var q = from c in customers
                join o in orders on c.Id == o.CustId
                select c.Name + ":" + o.Item;
        Console.WriteLine(q.Count());
    }
}
