// 슬라이드 p4-v3-query-join-trap — equals 의 왼쪽은 바깥 시퀀스, C# 3.0
using System;
using System.Linq;

class Program
{
    static void Main()
    {
        var customers = new[] { new { Id = 1, Name = "Kim" } };
        var orders = new[] { new { CustId = 1, Item = "pen" } };

        var q = from c in customers
                join o in orders on o.CustId equals c.Id
                select c.Name + ":" + o.Item;
        Console.WriteLine(q.Count());
    }
}
