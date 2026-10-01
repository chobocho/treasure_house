// 슬라이드 p4-v3-query-groupjoin — join … into, 바깥 조인, C# 3.0
using System;
using System.Linq;

class Program
{
    static void Main()
    {
        var customers = new[] {
            new { Id = 1, Name = "Kim" },
            new { Id = 2, Name = "Lee" },
        };
        var orders = new[] {
            new { CustId = 1, Item = "pen" },
            new { CustId = 1, Item = "pad" },
        };

        var counts = from c in customers
                     join o in orders on c.Id equals o.CustId into os
                     select c.Name + "=" + os.Count();
        Console.WriteLine(string.Join(" ", counts));

        var outer = from c in customers
                    join o in orders on c.Id equals o.CustId into os
                    from o in os.DefaultIfEmpty()
                    select c.Name + ":" + (o == null ? "-" : o.Item);
        Console.WriteLine(string.Join(" ", outer));
    }
}
