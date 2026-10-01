// 슬라이드 p4-v3-query-orderby — orderby 두 번과 쉼표 하나, C# 3.0
using System;
using System.Linq;

class Program
{
    static void Main()
    {
        var people = new[] {
            new { First = "Bob", Last = "Lee" },
            new { First = "Ann", Last = "Lee" },
            new { First = "Cal", Last = "Kim" },
            new { First = "Ann", Last = "Kim" },
        };

        var comma = from p in people
                    orderby p.Last, p.First descending
                    select p.Last + " " + p.First;
        Console.WriteLine(string.Join(", ", comma));

        var twice = from p in people
                    orderby p.Last
                    orderby p.First
                    select p.Last + " " + p.First;
        Console.WriteLine(string.Join(", ", twice));

        var once = from p in people
                   orderby p.First ascending
                   select p.Last + " " + p.First;
        Console.WriteLine(string.Join(", ", once));
    }
}
