// 슬라이드 p4-v3-query-instance — 인스턴스 메서드가 이긴다, C# 3.0
using System;
using System.Collections.Generic;
using System.Linq;

class Names : List<string>
{
    public IEnumerable<string> Where(Func<string, bool> p)
    {
        Console.WriteLine("  Names.Where (instance)");
        return Enumerable.Where(this, p);
    }
}

class Program
{
    static void Main()
    {
        Names n = new Names();
        n.Add("Kim"); n.Add("Lee"); n.Add("Park");

        IEnumerable<string> a = from s in n where s.Length == 3
                                select s;
        Console.WriteLine(string.Join(" ", a));

        IEnumerable<string> list = n;      // static type decides
        IEnumerable<string> b = from s in list where s.Length == 3
                                select s;
        Console.WriteLine(string.Join(" ", b));
    }
}
